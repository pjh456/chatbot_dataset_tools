# ChatBot Dataset Tools (CDT) 🤖

**ChatBot Dataset Tools** 是一个专门为对话型大模型（特别是 Role-Play 角色扮演领域）设计的工业级数据集工程框架。

它采用了 **上下文隔离的配置管理** 和 **混合驱动（惰性+内存）的数据流架构**，旨在解决大规模对话数据清洗、格式转换、以及后续 LLM 批量处理中的痛点。

---

## ✨ 核心特性

- 🛠️ **上下文感知配置 (Context-Aware Config)**：基于 `ContextVar` 实现。支持在不同线程/协程、甚至在代码块级别（`with config.switch`）动态切换 API 密钥、并发数或角色映射表。
- ⚡ **混合驱动数据集 (Hybrid-Drive Dataset)**：
    - **LazyDataset**：支持超大规模文件流式处理，内存占用极低。
    - **InMemoryDataset**：支持快速随机访问、打乱（Shuffle）和切分。
- 🔄 **全能格式适配器 (Formatters)**：原生支持 **OpenAI**、**ShareGPT**、**Alpaca** (含 LLaMA Factory 风格) 格式的无损解析与导出。
- 🧪 **流式算子库 (Fluent Ops)**：提供 `map`, `filter`, `limit`, `batch` 等链式调用方法，预设了角色重命名、连续对话合并、非法轮次过滤等常用转换。
- 💉 **配置血统延续 (Lineage Tracking)**：数据集在克隆或变换时，会自动保留其创建时刻的“配置基因”（如编码、角色定义），确保处理逻辑的一致性。

---

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/chatbot-dataset_tools.git
cd chatbot_dataset_tools

# 开发者模式安装
pip install -e .
```

---

## 🚀 快速上手

### 1. 基础加载与转换
通过 `DatasetLoader` 自动识别并捕获当前配置，实现不同标准间的转换：

```python
from chatbot_dataset_tools.datasets import DatasetLoader
from chatbot_dataset_tools.formatters import ShareGPTFormatter, OpenAIFormatter

# 1. 加载本地 ShareGPT 格式的数据集（惰性加载，不占内存）
ds = DatasetLoader.from_jsonl("my_data.jsonl")

# 2. 定义格式化器
sharegpt = ShareGPTFormatter()
openai = OpenAIFormatter()

# 3. 打印第一条数据的 OpenAI 格式输出
first_conv = next(iter(ds))
print(openai.format(first_conv))
```

### 2. 动态配置切换 (核心黑科技)
无需修改全局变量，即可在局部代码块中改变处理逻辑：

```python
from chatbot_dataset_tools.config import config
from chatbot_dataset_tools.ops import transforms

# 默认角色映射是 {"user": "human", "assistant": "gpt"}
# 我们可以临时切换它来处理特定的旧数据
with config.switch(ds={"role_map": {"user": "User", "assistant": "Assistant"}}):
    # 此范围内的 transforms.rename_roles() 将自动使用新的 role_map
    processed_ds = ds.map(transforms.rename_roles())
    processed_ds.to_jsonl("converted.jsonl")
```

### 3. 数据清洗链 (Pipeline)
利用链式调用轻松完成复杂清洗：

```python
from chatbot_dataset_tools.ops import filters, transforms

cleaned_ds = (
    ds.filter(filters.min_turns(2))              # 过滤掉少于 2 轮的对话
      .filter(filters.is_valid_alternating())    # 确保 user/assistant 严格交替
      .map(transforms.strip_content())           # 去除内容首尾空格
      .map(transforms.merge_consecutive_roles()) # 合并连续的同角色发言
      .limit(100)                                # 只取前 100 条用于测试
)
```

---

## 🏗️ 项目架构

```text
chatbot_dataset_tools
├── chatbot_dataset_tools/     # 源代码主包
│   ├── config/                # 配置管理：支持隔离切换、嵌套覆盖
│   ├── datasets/              # 数据集封装：LazyDataset (惰性), InMemoryDataset (内存)
│   ├── formatters/            # 格式适配：OpenAI, Alpaca, ShareGPT 转换逻辑
│   ├── ops/                   # 算子库：包含 filters (过滤) 与 transforms (变换)
│   ├── types/                 # 核心模型：Conversation, Message, MessageList
│   └── __init__.py
├── tests/                     # 单元测试目录
│   ├── config/
│   ├── datasets/
│   └── ...
├── pyproject.toml                   # 安装配置文件
└── README.md
```

---

## 📅 未来路线图 (Roadmap)

- [ ] **LLM 自动化生产引擎**：
    - [ ] 接入 `Ollama` / `OpenAI` 接口，支持对本地数据集进行批量任务处理（如：自动打分、摘要生成、扩充对话）。
    - [ ] 支持基于 `JSON Schema` 的结构化数据提取。
- [ ] **统计报告**：自动生成数据集 Token 分布、角色占比等可视化报告。

---

## 📜 许可证

MIT License. 欢迎提交 Issue 或 Pull Request。
