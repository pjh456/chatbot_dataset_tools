import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Optional, Callable
from tqdm import tqdm

from chatbot_dataset_tools.core import Conversation
from .synthesizer import DataSynthesizer, ResponseMapper


class GenerationTaskRunner:
    """批量数据集生成任务运行器.

    负责协调场景生成、API调用、并发控制以及结果持久化。
    """

    def __init__(
        self, synthesizer: DataSynthesizer, max_workers: int = 10, retry_limit: int = 3
    ):
        """
        Args:
            synthesizer: 绑定的数据合成器实例.
            max_workers: 最大并发线程数.
            retry_limit: 单个任务失败后的重试次数.
        """
        self.synthesizer = synthesizer
        self.max_workers = max_workers
        self.retry_limit = retry_limit
        self._lock = threading.Lock()
        self._success_count = 0
        self._next_idx = 1

    def run_batch(
        self,
        total_goal: int,
        system_prompt: str,
        schema: Dict[str, Any],
        mapper: ResponseMapper,
        prompt_factory: Callable[[], Dict[str, Any]],
        on_success: Callable[[Conversation, int], None],
        start_idx: int = 1,
    ):
        """执行批量生成任务.

        Args:
            total_goal: 目标生成总数.
            system_prompt: 系统提示词.
            schema: JSON Schema 定义.
            mapper: 响应字段映射配置.
            prompt_factory: 一个函数，每次调用返回一个字典，包含 {"prompt": str, "world_info": str}.
            on_success: 成功后的回调函数，参数为 (Conversation对象, 当前编号).
            start_idx: 起始编号（用于断点续传）.
        """
        self._next_idx = start_idx
        self._success_count = 0

        print(f"🚀 任务启动: 目标 {total_goal} 条, 并发 {self.max_workers}")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 初始任务提交
            futures = {}
            for _ in range(min(self.max_workers, total_goal)):
                task_data = prompt_factory()
                future = executor.submit(
                    self._single_worker,
                    system_prompt,
                    task_data["prompt"],
                    schema,
                    mapper,
                    task_data.get("world_info"),
                )
                futures[future] = task_data

            with tqdm(total=total_goal, desc="生成进度") as pbar:
                while self._success_count < total_goal:
                    # 等待任务完成
                    done_futures = as_completed(futures)

                    for future in done_futures:
                        conv = future.result()
                        # 移除已完成的任务
                        del futures[future]

                        if conv:
                            # 成功逻辑：加锁分配 ID 并执行持久化
                            with self._lock:
                                current_idx = self._next_idx
                                self._next_idx += 1
                                self._success_count += 1
                                # 执行回调（通常是写入文件）
                                on_success(conv, current_idx)

                            pbar.update(1)
                        else:
                            # 失败逻辑：tqdm 打印日志不干扰进度条
                            pbar.write("⚠️ 某次请求失败或解析错误，正在自动重试...")

                        # 补位逻辑：只要还没达标且队列没满，就补充新任务
                        if (self._success_count + len(futures)) < total_goal:
                            new_task = prompt_factory()
                            new_future = executor.submit(
                                self._single_worker,
                                system_prompt,
                                new_task["prompt"],
                                schema,
                                mapper,
                                new_task.get("world_info"),
                            )
                            futures[new_future] = new_task

                        # 每次处理完一个完成的 future 就退出内循环，检查 while 条件
                        break

        print(f"🏁 任务完成！总计生成 {self._success_count} 条数据。")

    def _single_worker(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Dict[str, Any],
        mapper: ResponseMapper,
        world_info: Optional[str],
    ) -> Optional[Conversation]:
        """单个任务的内部重试逻辑"""
        for attempt in range(self.retry_limit):
            try:
                conv = self.synthesizer.generate_conversation(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema=schema,
                    mapper=mapper,
                    world_info=world_info,
                )
                if conv:
                    return conv
            except Exception as e:
                # 可以在这里记录更详细的 log
                pass

            # 指数退避重试
            if attempt < self.retry_limit - 1:
                time.sleep(2**attempt)

        return None
