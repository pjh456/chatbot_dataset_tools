# ChatBot Dataset Tools

**ChatBot Dataset Tools** 是一个面向 **角色扮演（Role-Play）与对话型大模型** 的数据集处理与转换工具库，目标是：

- 用 **统一的中间模型** 描述复杂对话（含场景、行为、思考）
- 在不同主流指令微调数据集格式之间 **可靠、可扩展地转换**
- 为后续 **自动化生成 / 调整数据（API 并发调用）** 提供稳定底座

该库定位为 **工程化数据工具**，而非一次性脚本。

---

## 设计目标

- **中间模型优先**：所有格式先归一化，再导出
- **面向角色扮演优化**：原生支持场景、动作、思考链
- **低耦合、可扩展**：新增格式不影响已有逻辑
- **适配主流微调生态**：ShareGPT / Alpaca 等

---

## 核心中间模型（Canonical Model）

库内部使用统一的 `Message` / `Conversation` 模型作为数据流转核心。

```text
Message
├── role     # system / user / assistant ...
├── scene    # 场景描述（世界观、环境、状态）
├── action   # 行为描述（角色正在做什么）
├── think    # 内部思考 / Chain-of-Thought（可选）
└── content  # 可见输出文本
```

设计原则：

- **think 字段可选**：
  - 可导出为显式 CoT（研究 / 推理模型）
  - 或在导出阶段直接丢弃（对齐不支持思考的模型）
- `scene` / `action` 用于高质量角色扮演建模，而非简单闲聊

---

## 项目架构

```
chatbot_dataset_tools/
├── core/        # 核心中间模型 + 不可动摇的基础设施
├── adapters/    # 各类数据集格式（ShareGPT / Alpaca / ...）
├── transforms/  # 对 Conversation 的结构性变换
├── renderers/   # 把中间模型“渲染”为文本/指令
├── io/          # 读写、批量处理、流式
├── api/         # API 并发生成 / 修正（后续）
├── cli/         # 命令行工具（后期）
└── tests/       # 单元测试
```

## 计划支持的数据集格式

### 指令微调常用格式

- **ShareGPT**
  - 可读取 / 可导出
  - 支持 system 注入、角色映射

- **Alpaca / Instruction-Response**
  - instruction / input / output 结构
  - 自动从多轮对话压缩或抽取

### 🚧 计划中

- LLaMA Factory 扩展格式
- 自定义 Role-Play JSON Schema

---

## 转换流程示意

```text
[ ShareGPT / Alpaca / Custom JSON ]
              ↓ load
        Conversation (中间模型)
              ↓ dump
[ ShareGPT / Alpaca / Other Format ]
```

特点：

- 不存在 A → B 的硬编码转换
- 任意格式之间天然可互转

---

## API 扩展规划（Roadmap）

后续版本将加入 **数据生成与修正工具链**：

- 基于 API 的并发请求生成对话
- 自动补全 scene / action / think
- 批量风格迁移（如：从“普通对话”转“强角色扮演”）
- 数据清洗与一致性校验

这些能力将直接复用现有中间模型，不破坏格式层。

---

## 适用场景

- 角色扮演 / 剧情向模型微调
- 带或不带思考链的模型对齐
- 多数据源统一清洗与再分发
- 自动化构造或调整高质量 RP 数据集

---

## 项目状态

> 当前阶段：**核心模型 + 数据集格式适配层设计中**

接口可能仍会微调，但整体架构已稳定。

---

## License

MIT
