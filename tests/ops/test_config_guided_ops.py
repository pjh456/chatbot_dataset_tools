from chatbot_dataset_tools.config import config
from chatbot_dataset_tools.ops import transforms
from chatbot_dataset_tools.types import Message, Conversation


def test_rename_roles_guided_by_config():
    conv = Conversation([Message("old_user", "hi")])

    # 在特定的配置上下文中运行
    with config.switch(role_map={"old_user": "new_user"}):
        # 此时 rename_roles 不传参数，应该自动按 config 映射
        op = transforms.rename_roles()
        new_conv = op(conv)
        assert new_conv.messages[0].role == "new_user"


def test_merge_sep_guided_by_config():
    conv = Conversation([Message("user", "line1"), Message("user", "line2")])

    # 测试自定义分隔符配置
    with config.switch(msg_sep=" <SEP> "):
        op = transforms.merge_consecutive_roles()
        new_conv = op(conv)
        assert new_conv.messages[0].content == "line1 <SEP> line2"
