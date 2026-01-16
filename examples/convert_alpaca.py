from chatbot_dataset_tools.adapters import AlpacaAdapter
from chatbot_dataset_tools.core import Conversation, Role

# 1. 构造一个 3 轮的对话
conv = Conversation(system_prompt="你是一个可爱的猫娘。")
conv.add_message(Role.USER, content="你好")
conv.add_message(Role.ASSISTANT, content="*摇尾巴* 你好喵！")
conv.add_message(Role.USER, content="你叫什么名字？")
conv.add_message(Role.ASSISTANT, content="喵？我没有名字喵。")

# 2. 测试带 History 的导出 (LLaMA Factory 风格)
adapter_history = AlpacaAdapter(use_history=True)
data_with_history = adapter_history.dump([conv])
print("--- With History ---")
print(data_with_history[0])
# 预期: history 会包含第一轮，instruction 是第二轮的问，output 是第二轮的答

# 3. 测试不带 History 的导出 (Context Packing 风格)
adapter_no_history = AlpacaAdapter(use_history=False)
data_no_history = adapter_no_history.dump([conv])
print("\n--- No History ---")
print(data_no_history[0])
# 预期: instruction 包含了 System + 第一轮全过程 + 第二轮的问
