from __future__ import annotations

import sys
from collections.abc import AsyncIterable, AsyncIterator
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent / "src"))

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.base import Codec
import duui_py.settings as framework_settings
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    ErrorSettings,
    FrameworkSettings,
    InputDesc,
    InputSofaSpec,
    LimitSettings,
    OutputDesc,
    OutputSofaSpec,
    SofaModeSpec,
    ValidationSettings,
)
from duui_py.models.config import LoggingSettings


def _config(name: str) -> AnnotatorConfig:
    typesystem_path = Path("/tmp/duui_py_test_typesystem.xml")
    if not typesystem_path.exists():
        typesystem_path.write_text("<typeSystemDescription xmlns='http://uima.apache.org/resourceSpecifier'><types/></typeSystemDescription>")

    return AnnotatorConfig(
        meta=AnnotatorMeta(
            implementation_lang="Python",
            meta={},
            settings=FrameworkSettings(
                validation=ValidationSettings(),
                limits=LimitSettings(),
                errors=ErrorSettings(),
                logging=LoggingSettings(enabled=False),
            ),
        ),
        description=name,
        descriptor=AnnotatorDescriptor(
            name=name,
            version="1.0.0",
            input=InputDesc(sofa=InputSofaSpec(text=SofaModeSpec(mimeType="text/plain", language="x-unspecified"))),
            output=OutputDesc(sofa=OutputSofaSpec(text=SofaModeSpec(mimeType="text/plain", language="x-unspecified"))),
        ),
        typesystem_xml_path=str(typesystem_path),
        parameters_schema={},
    )


class StreamingLineCodec(Codec[str, str]):
    name = "stream-lines"
    request_media_type = "application/octet-stream"
    response_media_type = "application/octet-stream"

    def communication_layer_content(self) -> dict[str, str | int]:
        return {"kind": "custom", "format": "lua", "version": 1, "spec": "function serialize() end function deserialize() end"}

    def decode_request(self, body: bytes) -> str:
        return body.decode("utf-8")

    def encode_response(self, result: str) -> bytes:
        return result.encode("utf-8")

    async def decode_request_stream(self, body_stream: AsyncIterable[bytes]) -> AsyncIterator[str]:
        async def _iter_lines() -> AsyncIterator[str]:
            buffer = ""
            async for chunk in body_stream:
                buffer += chunk.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line:
                        yield line
            if buffer:
                yield buffer

        return _iter_lines()

    async def encode_response_stream(self, result_stream: AsyncIterable[str]) -> AsyncIterator[bytes]:
        async def _iter_encoded() -> AsyncIterator[bytes]:
            async for result in result_stream:
                yield f"{result}|".encode("utf-8")

        return _iter_encoded()


class StreamingUpperAnnotator(DuuiAnnotator[str, str]):
    config = _config("streaming-upper")

    def codec(self) -> StreamingLineCodec:
        return StreamingLineCodec()

    async def process(self, doc: str) -> str:
        return doc.upper()

    async def process_stream(self, docs: str | AsyncIterable[str]) -> AsyncIterator[str]:
        if hasattr(docs, "__aiter__"):
            async for doc in docs:  # type: ignore[union-attr]
                yield doc.upper()
            return
        yield docs.upper()


class BufferedUpperAnnotator(DuuiAnnotator[str, str]):
    config = _config("buffered-upper")

    def codec(self) -> StreamingLineCodec:
        return StreamingLineCodec()

    async def process(self, doc: str) -> str:
        return doc.upper()


def test_process_endpoint_uses_codec_streaming_when_available() -> None:
    app = create_app(StreamingUpperAnnotator)
    client = TestClient(app)

    response = client.post("/v1/process", data=b"alpha\nbeta\n")
    assert response.status_code == 200
    assert response.content == b"ALPHA|BETA|"


def test_process_endpoint_keeps_buffered_mode_as_fallback() -> None:
    framework_settings._settings_initialized = False  # type: ignore[attr-defined]
    app = create_app(BufferedUpperAnnotator)
    client = TestClient(app)

    response = client.post("/v1/process", data=b"alpha\nbeta\n")
    assert response.status_code == 200
    assert response.content == b"ALPHA\nBETA\n"
