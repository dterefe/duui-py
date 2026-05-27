from __future__ import annotations

import asyncio
from pathlib import Path
import struct
from typing import Any

from duui_py.adapters import AsyncChunkedRequestAdapter, SynchronousRequestAdapter, default_request_adapter
from duui_py.codecs.base import Codec
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import AnnotatorConfig, AnnotatorDescriptor, AnnotatorMeta, Domain, DomainSpec, DuuiResult, IODescriptor, WireSettings
from duui_py.models.config import WireWindowSettings
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.types import Token


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


def test_msgpack_response_stream_emits_start_before_consuming_results() -> None:
    async def run() -> None:
        config = _config().model_copy(
            update={
                "wire": WireSettings(
                    protocol="runtime-msgpack-windowed",
                    window=WireWindowSettings(maxRows=2, maxBytes=4096, flushMs=0),
                )
            }
        )
        codec = MsgPackLuaCodec(config)
        consumed = 0

        async def results():
            nonlocal consumed
            for index in range(3):
                consumed += 1
                yield DuuiResult(annotations=[Token(begin=index, end=index + 1, order=index)])

        stream = codec.encode_response_stream(results())
        first = await anext(stream)

        assert first[0] == 0x01
        assert consumed == 0

        second = await anext(stream)
        assert second[0] == 0x11
        assert struct.unpack(">I", second[13:17])[0] == 2
        assert consumed == 2

    asyncio.run(run())


def test_msgpack_example_annotators_use_async_chunked_adapter() -> None:
    root = Path(__file__).resolve().parent / "examples"
    files = sorted(root.glob("*msgpack*/*_annotator.py"))
    assert files
    for path in files:
        text = path.read_text()
        assert "AsyncChunkedRequestAdapter" in text, str(path)
        assert "request_adapter=AsyncChunkedRequestAdapter()" in text, str(path)
