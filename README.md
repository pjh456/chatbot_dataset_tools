# ChatBot Dataset Tools (CDT) 🤖

**ChatBot Dataset Tools** 是一个工业级的对话数据集工程框架。它不仅仅是一套工具集，更是一个高度可扩展的 **ETL (Extract, Transform, Load)** 引擎，专为大模型（LLM）微调、角色扮演数据清洗和合成而生。

---

## 🌟 核心升级：声明式流水线
现在，你可以完全通过 **JSON 配置文件** 来定义复杂的数据处理流水线，无需编写冗长的 Python 代码。

- **组件解耦**：IO、算子、配置完全分离，支持参数化构造。
- **智能匹配**：Registry 支持别名与后缀智能识别（如 `file` 自动匹配 `FileSource`）。
- **变量注入**：支持 `${VAR}` 语法，从环境变量或配置文件动态注入参数。
- **自动发现**：插件化架构，系统自动扫描并注册所有内部及外部算子。
- **透明日志**：标准化的日志体系，覆盖从 IO 到 API 调用的每一个细节。

---

## 🏗️ 核心架构

```text
chatbot_dataset_tools/
├── config/        # 静态环境配置：API Key, 默认并发, 上下文切换
├── pipeline/      # 动态业务逻辑：JSON 解析、步骤调度、变量注入
├── registry/      # 插件注册中心：支持智能模糊匹配的组件仓库
├── connectors/    # IO 适配器：File (JSON/JSONL), HTTP 接口支持
├── datasets/      # 数据容器：Lazy (流式), InMemory (内存), Concat (多源合并)
├── ops/           # 原子算子：Filter (过滤), Transform (变换)
├── tasks/         # 异步任务：TaskRunner, 限流器, 断点续传 (Checkpoint)
└── formatters/    # 格式标准：OpenAI, ShareGPT, Alpaca 无损转换
```

---

## 🚀 快速开始

### 1. 声明式处理 (推荐)
创建一个 `pipeline.json`，配置你的处理流：

```json
{
  "name": "LLM_Refine_Job",
  "variables": { "DATA_DIR": "./data/v1" },
  "settings": {
    "proc": { "max_workers": 16 },
    "api": { "openai_api_key": "${ENV_OPENAI_KEY}" }
  },
  "steps": [
    {
      "name": "加载原始数据",
      "type": "loader",
      "params": {
        "inputs": [
          { "source_type": "file", "path": "${DATA_DIR}/raw.jsonl" },
          { "source_type": "http", "url": "https://api.mydata.com/fetch" }
        ]
      }
    },
    {
      "name": "基础清洗",
      "type": "filter",
      "params": { "op": "min_turns", "n": 2 }
    },
    {
      "name": "LLM 润色任务",
      "type": "task",
      "params": {
        "processor": "llm",
        "model": "gpt-4",
        "checkpoint_path": "./data/v1/checkpoint.txt"
      }
    },
    {
      "name": "输出保存",
      "type": "saver",
      "params": { "path": "${DATA_DIR}/cleaned.jsonl" }
    }
  ]
}
```

运行 Pipeline：
```python
from chatbot_dataset_tools.pipeline.engine import PipelineEngine
from chatbot_dataset_tools.utils.logger import setup_logging

# 1. 初始化标准化日志
setup_logging(level="INFO")

# 2. 启动引擎（自动完成组件加载与注册）
engine = PipelineEngine("pipeline.json")
engine.run()
```

---

## 🧩 核心功能详解

### 1. 自动发现与注册中心 (Registry)
无需手动 `import`，只需在自定义算子上添加装饰器：
```python
from chatbot_dataset_tools.registry import register_transform

@register_transform("my_cleaner")
def my_custom_cleaner(arg1):
    return lambda conv: ... 
```
在 JSON 中通过 `"op": "my_cleaner"` 即可直接调用。Registry 支持智能匹配，写 `file` 也能找到 `FileSource`。

### 2. 上下文配置切换
支持配置的“血统延续”。数据集会记住它出生时的配置环境，你可以随时切换环境：
```python
# 临时切换并发数和 API 密钥
with config.switch(proc={"max_workers": 1}, api={"openai_api_key": "xxx"}):
    # 此范围内的任务将严格受限
    ds.run_task(processor)
```

### 3. 断点续传 (Checkpoint)
在大规模 API 处理任务中，CDT 会记录每一个 `uid`（基于内容哈希或显式 ID）。如果程序崩溃，下次启动将**自动跳过已处理的数据**。

### 4. 标准化 IO 与格式化
支持多种格式的无损转换。通过内置的 `FieldMapper` 支持复杂的模板注入。
- **Source**: `FileSource`, `HTTPSource`
- **Formatter**: `OpenAI`, `ShareGPT`, `Alpaca`

---

## 🛠️ 开发者指南

### 如何添加新的 Processor (如接入本地模型)?
1. 在 `tasks/processors/` 下新建文件。
2. 继承 `BaseProcessor` 并使用 `@register_processor`。
3. 实现 `process` 方法。
4. Engine 会自动扫描并使其在 JSON 中可用。

---

## 📅 路线图 (Roadmap)
- [x] **Registry & Pipeline 引擎** (已完成)
- [x] **自动模块发现** (已完成)
- [x] **标准化日志系统** (已完成)
- [x] **多源数据合并 (ConcatDataset)** (已完成)
- [ ] **可用性增强与环境优化**
- [ ] **Bug 排查与边缘情况对齐**
---

## 📜 许可证
MIT License. 贡献请提交 PR。