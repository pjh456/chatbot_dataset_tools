# ChatBot Dataset Tools 🤖

**ChatBot Dataset Tools** 是一个专为 **角色扮演 (Role-Play)** 与 **对话型大模型** 设计的高性能数据集工程框架。

它不仅能让你在不同格式（ShareGPT/Alpaca）之间无损转换，更提供了一套从 **“随机场景构造 -> 大模型高并发生成 -> 结构化清洗提取”** 的完整生产线。

---

## 🌟 核心特性

- **结构化中间模型**：原生支持 `Thought` (思考链)、`Action` (行为)、`Scene` (场景) 等 RP 核心字段。
- **Dataset 管理器**：支持链式调用，提供 `filter`, `map`, `split`, `shuffle` 等高阶数据操作。
- **双向格式适配**：支持 ShareGPT 和 Alpaca (含 LLaMA Factory 多轮 history) 格式的相互转换。
- **智能提取器**：基于正则规则，自动从杂乱文本中分离动作、思考与正文。
- **工业级生成引擎**：支持高并发 API 调用、场景随机化、JSON Schema 约束及断点续传。

---

## 🛠️ 项目架构

```text
chatbot_dataset_tools/
├── core/           # 核心模型 (Message, Conversation, Dataset)
├── adapters/       # 格式适配器 (ShareGPT, Alpaca)
├── transforms/     # 变换逻辑 (RegexExtractor, TextCleanup)
├── renderers/      # 文本渲染引擎 (Asterisk, Bracket, ThoughtChain)
├── generator/      # 生产引擎 (ScenarioManager, TaskRunner)
├── api/            # API 客户端封装
└── io/             # 流式读写层 (JSON, JSONL)
```

---

## 🚀 快速上手

### 1. 数据加载与格式转换
将 ShareGPT 格式的数据无缝转为带 History 的 Alpaca 格式：

```python
from chatbot_dataset_tools import Dataset, DatasetReader, DatasetWriter
from chatbot_dataset_tools.adapters import ShareGPTAdapter, AlpacaAdapter

# 加载数据
reader = DatasetReader(adapter=ShareGPTAdapter())
ds = Dataset(list(reader.stream("raw_data.jsonl")))

# 转换为 Alpaca 格式并写入 (开启 history 支持)
writer = DatasetWriter(adapter=AlpacaAdapter(use_history=True))
writer.write(ds, "alpaca_history.json")
```

### 2. 结构化提取与清洗
利用 `Extractor` 从原始对话中把 `*动作*` 和 `(心理)` 提取到独立字段：

```python
from chatbot_dataset_tools.transforms import ExtractorPresets

# 应用正则提取预设
processed_ds = ds.apply(ExtractorPresets.roleplay_standard())

# 此时数据已结构化：
# msg.content -> "你好呀！"
# msg.action  -> "轻轻挥手"
# msg.thought -> "他看起来很眼熟"
```

### 3. 高并发自动化数据集生成 (黑科技)
利用场景引擎和生成器，从零开始批量制造高质量 RP 剧本：

```python
from chatbot_dataset_tools.generator import ScenarioManager, GenerationTaskRunner, DataSynthesizer
from chatbot_dataset_tools.api import APIClient

# 1. 定义场景变量
mgr = ScenarioManager(bases=["在{location}约会"], slots={"location": ["水族馆", "屋顶"]}, modifiers=["雨天"])

# 2. 配置映射关系 (解耦 API 字段名)
mapper = ResponseMapper(
    items_path="turns",
    message_mapping=MessageMapping(role_map={"user_part": "user", "resp_part": "assistant"})
)

# 3. 启动高并发任务
runner = GenerationTaskRunner(DataSynthesizer(APIClient(...)), max_workers=20)
runner.run_batch(
    total_goal=1000,
    system_prompt="你现在是角色XXX...",
    schema=MY_JSON_SCHEMA,
    mapper=mapper,
    prompt_factory=lambda: {"prompt": mgr.generate()},
    on_success=lambda conv, idx: writer.write([conv], f"data_{idx}.json")
)
```

---

## 🧩 核心组件说明

### 渲染器 (Renderers)
决定了数据在“落地”时的样子。通过切换 `Renderer`，你可以让同一份数据输出为：
- `*动作* 你好`
- `[动作] 你好`
- `<thought> 思考 </thought> 你好`

### 适配器 (Adapters)
- **ShareGPTAdapter**: 现代多轮对话标准。
- **AlpacaAdapter**: 支持将多轮对话压缩进 `instruction` 或存入 `history` 列表（适配 LLaMA Factory）。

### 变换器 (Transforms)
- **RegexExtractor**: 将非结构化文本升维为结构化数据。
- **TextCleanup**: 自动合并多余空格，清理提取后残留的孤儿标点。

---

## 📈 开发路线

- [x] 核心模型与 Dataset 管理器
- [x] ShareGPT / Alpaca 双向适配
- [x] 正则提取与内容清洗变换
- [x] 高并发生成引擎与场景随机化
- [ ] 接入本地模型 (Ollama/vLLM) 直接生成
- [ ] 数据一致性校验器（检查 User/Assistant 是否交替）
- [ ] 交互式数据标注/修正工具

---

## 📜 许可证

MIT License. 欢迎贡献代码或提出 Issue。

---

### 开发建议
如果你在处理角色扮演数据时感到痛苦，请记住：**不要去改你的原始 JSON，写一个 Transform！**