import os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_PATH, "sharegpt_example.json")
OUTPUT_PATH = os.path.join(BASE_PATH, "output_data.jsonl")

from chatbot_dataset_tools.adapters import ShareGPTAdapter
from chatbot_dataset_tools.transforms import ExtractorPresets
from chatbot_dataset_tools.io import DatasetReader, DatasetWriter
from chatbot_dataset_tools.renderers import RendererPresets

# 1. 准备适配器和转换器
adapter = ShareGPTAdapter(renderer=RendererPresets.classic_asterisk())
action_extractor = ExtractorPresets.roleplay_standard()

# 2. 流式加载
reader = DatasetReader(adapter=adapter)
conv_stream = reader.stream(JSON_PATH)


# 3. 进行变换
def my_filter(stream):
    for conv in stream:
        new_conv = action_extractor.apply(conv)
        for msg in new_conv.messages:
            msg.action = None
        yield new_conv


filtered_stream = my_filter(conv_stream)

# 4. 写入结果
writer = DatasetWriter(adapter=adapter)
writer.write(filtered_stream, OUTPUT_PATH)
