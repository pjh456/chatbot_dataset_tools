import os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_PATH, "sharegpt_example2.jsonl")
TRAIN_PATH = os.path.join(BASE_PATH, "train.jsonl")
TEST_PATH = os.path.join(BASE_PATH, "test.jsonl")

from chatbot_dataset_tools.core import Dataset
from chatbot_dataset_tools.adapters import ShareGPTAdapter
from chatbot_dataset_tools.io import DatasetReader, DatasetWriter
from chatbot_dataset_tools.transforms import ExtractorPresets

# 1. 加载
adapter = ShareGPTAdapter()
reader = DatasetReader(adapter=adapter)
# 注意：我们这里从生成器创建 Dataset 对象
ds = Dataset(list(reader.stream(JSON_PATH)))

# 2. 链式清洗与过滤
processed_ds = (
    ds.apply(ExtractorPresets.roleplay_standard())  # 提取动作和思考
    .filter(lambda c: len(c.messages) >= 1)  # 只保留 1 轮以上的对话
    .shuffle(seed=42)  # 打乱
)

# 3. 统计一下看看结果
print(processed_ds.summary())

# 4. 拆分数据集
train_ds, test_ds = processed_ds.split(0.9)

# 5. 保存
writer = DatasetWriter(adapter=adapter)
writer.write(train_ds, TRAIN_PATH)
writer.write(test_ds, TEST_PATH)
