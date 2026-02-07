import json
import pytest
import respx
from httpx import Response
from chatbot_dataset_tools.types import Conversation, Message
from chatbot_dataset_tools.connectors import HTTPSource, HTTPSink
from chatbot_dataset_tools.config import config, HTTPConfig


@pytest.fixture
def sample_convs():
    """提供基础的测试数据"""
    return [
        Conversation([Message(role="user", content="hello")]),
        Conversation(
            [
                Message(role="user", content="hi"),
                Message(role="assistant", content="hey"),
            ]
        ),
    ]


@pytest.fixture
def sample_raw_data():
    """提供模拟服务器返回的原始字典数据"""
    return [
        {"messages": [{"role": "user", "content": "hello"}], "metadata": {}},
        {
            "messages": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hey"},
            ],
            "metadata": {},
        },
    ]


class TestHTTPSource:
    @respx.mock
    def test_load_simple_list(self, sample_raw_data):
        """测试直接从返回的列表加载数据"""
        url = "http://api.test/convs"
        # 模拟 API 返回一个列表
        respx.get(url).mock(return_value=Response(200, json=sample_raw_data))

        cfg = HTTPConfig(
            url=url, method="GET", data_path=[]
        )  # path为空表示根部即是列表
        source = HTTPSource(http_cfg=cfg)

        results = list(source.load())
        assert len(results) == 2
        assert results[0].messages[0].content == "hello"

    @respx.mock
    def test_load_nested_data(self, sample_raw_data):
        """测试根据 data_path 从嵌套 JSON 中提取数据"""
        url = "http://api.test/nested"
        # 模拟嵌套结构: {"status": "ok", "results": {"items": [...]}}
        nested_response = {"status": "ok", "results": {"items": sample_raw_data}}
        respx.get(url).mock(return_value=Response(200, json=nested_response))

        cfg = HTTPConfig(url=url, data_path=["results", "items"])
        source = HTTPSource(http_cfg=cfg)

        results = list(source.load())
        assert len(results) == 2
        assert results[1].messages[1].role == "assistant"

    @respx.mock
    def test_http_error_handling(self):
        """测试 404 或 500 错误"""
        url = "http://api.test/error"
        respx.get(url).mock(return_value=Response(404))

        source = HTTPSource(HTTPConfig(url=url))
        with pytest.raises(Exception):  # httpx.HTTPStatusError
            list(source.load())


class TestHTTPSink:
    @respx.mock
    def test_save_bulk(self, sample_convs):
        """测试一次性保存所有数据"""
        url = "http://api.test/save"
        route = respx.post(url).mock(return_value=Response(201))

        cfg = HTTPConfig(url=url, method="POST", data_path=["data"])
        sink = HTTPSink(http_cfg=cfg)

        sink.save(sample_convs)

        # 检查发送的请求内容
        assert route.called
        sent_data = json.loads(route.calls.last.request.content)
        # 验证 data_path 是否生效：{"data": [...]}
        assert "data" in sent_data
        assert len(sent_data["data"]) == 2
        assert sent_data["data"][0]["messages"][0]["content"] == "hello"

    @respx.mock
    def test_save_streaming(self, sample_convs):
        """测试逐条流式发送数据"""
        url = "http://api.test/stream"
        route = respx.post(url).mock(return_value=Response(200))

        cfg = HTTPConfig(url=url, method="POST")
        sink = HTTPSink(http_cfg=cfg)

        sink.save_streaming(sample_convs)

        # 应该发送了两次请求
        assert route.call_count == 2
        # 验证最后一次发送的内容是单条对话
        last_sent = json.loads(route.calls.last.request.content)
        assert "messages" in last_sent
        assert last_sent["messages"][0]["content"] == "hi"

    def test_wrap_data_logic(self):
        """测试内部路径包装逻辑 (不涉及网络)"""
        sink = HTTPSink(HTTPConfig(data_path=["v1", "payload"]))
        test_list = [{"id": 1}, {"id": 2}]

        wrapped = sink._wrap_data(test_list)

        assert wrapped == {"v1": {"payload": test_list}}

    @respx.mock
    def test_sink_with_global_config(self, sample_convs):
        """测试 Sink 响应全局 config 切换"""
        url = "http://global-api.test/push"
        route = respx.put(url).mock(return_value=Response(200))

        # 使用 config.switch 动态注入配置
        with config.switch(url=url, method="PUT", data_path=[]):
            sink = HTTPSink()  # 不传参数，使用全局
            sink.save(sample_convs)

        assert route.called
        assert route.calls.last.request.method == "PUT"


def test_source_invalid_path():
    """测试当路径不匹配时的报错"""
    # 模拟返回的是个列表，但配置要求去字典里找 'items' 键
    url = "http://api.test/invalid"
    with respx.mock:
        respx.get(url).mock(return_value=Response(200, json=[1, 2, 3]))

        source = HTTPSource(HTTPConfig(url=url, data_path=["items"]))
        with pytest.raises(ValueError, match="invalid for current structure"):
            list(source.load())
