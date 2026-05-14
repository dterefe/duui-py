from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import msgpack
from fastapi.testclient import TestClient

from duui_py.app import create_app
import duui_py.app as duui_app_module
from duui_py.codecs.msgpack_lua.codec import CHUNK_END, CHUNK_SOFA, CHUNK_START, MsgPackLuaCodec
from duui_py.models import AnnotatorConfig, V1RequestEnvelope, SoFaBytes


ROOT = Path(__file__).parent
WHISPER_PATH = ROOT / "examples" / "whisper-msgpack-lua" / "whisper_annotator.py"

spec = importlib.util.spec_from_file_location("whisper_annotator_module", WHISPER_PATH)
assert spec and spec.loader
whisper_mod = importlib.util.module_from_spec(spec)
cwd_before_import = os.getcwd()
os.chdir(str(WHISPER_PATH.parent))
original_create_app = duui_app_module.create_app
duui_app_module.create_app = lambda *_args, **_kwargs: None
try:
    spec.loader.exec_module(whisper_mod)
finally:
    duui_app_module.create_app = original_create_app
    os.chdir(cwd_before_import)

WhisperAnnotator = whisper_mod.WhisperAnnotator


def _config() -> AnnotatorConfig:
    return AnnotatorConfig.model_validate(
        {
            "meta": {
                "implementation_lang": "Python",
                "meta": {},
                "settings": {"logging": {"enabled": False}},
            },
            "description": "",
            "descriptor": {
                "name": "whisper-test",
                "version": "1",
                "input": {"bytes": {"default": {"mimeType": "application/octet-stream", "languages": ["en"], "types": {}}}},
                "output": {"text": {"default": {"mimeType": "text/plain", "languages": ["en"], "types": {}}}},
            },
            "typesystem_xml_path": ".dev/UIMATypeSystem/target/classes/desc/type/Core.xml",
        }
    )


class _DummyModel:
    def transcribe(self, _path: str) -> dict:
        return {
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "hello"},
                {"start": 1.0, "end": 2.5, "text": "world"},
            ]
        }


def test_whisper_process_bytes_yields_result(monkeypatch) -> None:
    monkeypatch.setattr(whisper_mod, "_load_whisper_model", lambda _name: _DummyModel())

    annotator = WhisperAnnotator(config=_config())
    payload = V1RequestEnvelope(
        parameters={},
        sofa=SoFaBytes(mimeType="application/octet-stream", language="en", bytes=b"fake-audio"),
        fs=[],
    )

    import asyncio

    async def run() -> list:
        out = []
        async for chunk in duui_app_module._invoke_v1(annotator, payload, annotator.config.descriptor.input):
            out.append(chunk)
        return out

    got = asyncio.run(run())
    assert len(got) == 4
    assert got[0].features["value"] == "hello"
    assert got[1].features["value"] == "world"


def test_whisper_endpoint_processes_bytes(monkeypatch) -> None:
    monkeypatch.setattr(whisper_mod, "_load_whisper_model", lambda _name: _DummyModel())
    app = create_app(WhisperAnnotator, config=_config())
    codec = MsgPackLuaCodec(_config())
    client = TestClient(app)

    start_payload = msgpack.packb(
        {"parameters": {}, "view": ""},
        use_bin_type=True,
    )
    sofa_payload = msgpack.packb(
        {
            "type": "uima.cas.Sofa",
            "kind": "bytes",
            "mimeType": "application/octet-stream",
            "language": "en",
            "data": b"fake-audio".decode("latin-1"),
            "features": {"mimeType": "application/octet-stream", "language": "en", "data": b"fake-audio".decode("latin-1")},
        },
        use_bin_type=True,
    )
    body = codec._serialize_chunks([(CHUNK_START, start_payload), (CHUNK_SOFA, sofa_payload), (CHUNK_END, b"")])

    response = client.post("/v1/process", content=body, headers={"content-type": "application/x-msgpack"})
    assert response.status_code == 200

    out_chunks = codec._parse_chunked_stream(response.content)
    annotation_chunks = [chunk for chunk in out_chunks if chunk[0] == 0x03]
    assert len(annotation_chunks) == 2
