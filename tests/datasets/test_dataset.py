import pytest
from chatbot_dataset_tools.datasets import Dataset


def test_dataset_base_class():
    class DummyDataset(Dataset):
        pass

    dataset = DummyDataset()

    with pytest.raises(NotImplementedError):
        list(dataset)

    with pytest.raises(NotImplementedError):
        len(dataset)
