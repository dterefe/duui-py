from __future__ import annotations

from typing import Any

from duui_py.adapters import AsyncChunkedRequestAdapter, SynchronousRequestAdapter, default_request_adapter
from duui_py.codecs.base import Codec
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import AnnotatorConfig, AnnotatorDescriptor, AnnotatorMeta, Domain, DomainSpec, IODescriptor


def _config() -> AnnotatorConfig:
    return AnnotatorConfig(
        meta=AnnotatorMeta(),
        descriptor=AnnotatorDescriptor(
            name="test",
            version="1",
            input=IODescriptor(text=DomainSpec(default=Domain(mimeType="text/plain; charset=utf-8"))),
            output=IODescriptor(text=DomainSpec(default=Domain(mimeType="text/plain; charset=utf-8"))),
        ),
    )


class PlainCodec(Codec[bytes, bytes]):
    name = "plain"
    request_media_type = "application/octet-stream"
    response_media_type = "application/octet-stream"

    def communication_layer_content(self) -> dict[str, Any]:
        return {"format": "lua", "spec": "function serialize() end"}

    def decode_request(self, body: bytes) -> bytes:
        return body

    def encode_response(self, result: bytes) -> bytes:
        return result


def test_stream_capable_codec_uses_async_chunked_adapter() -> None:
    adapter = default_request_adapter(MsgPackLuaCodec(_config()))

    assert isinstance(adapter, AsyncChunkedRequestAdapter)


def test_plain_codec_uses_synchronous_adapter() -> None:
    adapter = default_request_adapter(PlainCodec())

    assert isinstance(adapter, SynchronousRequestAdapter)
