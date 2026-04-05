from __future__ import annotations

import struct
import sys
from pathlib import Path

import msgpack

sys.path.insert(0, str(Path(__file__).parent / "src"))

from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.codecs.msgpack_lua.codec import (
    CHUNK_END,
    CHUNK_ERROR,
    CHUNK_SOFA,
    CHUNK_START,
)
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    DuuiResult,
    InputSofaSpec,
    InputDesc,
    OutputSofaSpec,
    OutputDesc,
    SofaModeSpec,
)
from duui_py.models.config import ErrorSettings, FrameworkSettings, LimitSettings, LoggingSettings, ValidationSettings


def _config() -> AnnotatorConfig:
    descriptor = AnnotatorDescriptor(
        name="test-annotator",
        version="1.0.0",
        input=InputDesc(
            sofa=InputSofaSpec(
                text=SofaModeSpec(mimeType="text/plain; charset=utf-8", language="x-unspecified")
            ),
            types=[],
        ),
        output=OutputDesc(
            sofa=OutputSofaSpec(
                text=SofaModeSpec(mimeType="text/plain; charset=utf-8", language="x-unspecified")
            ),
            types=[],
        ),
    )
    return AnnotatorConfig(
        meta=AnnotatorMeta(
            implementation_lang="Python",
            meta={},
            settings=FrameworkSettings(
                validation=ValidationSettings(),
                limits=LimitSettings(),
                errors=ErrorSettings(),
                logging=LoggingSettings(),
            ),
        ),
        description="test",
        descriptor=descriptor,
        typesystem_xml_path="/tmp/non-existing-typesystem.xml",
        parameters_schema={},
    )


def _parse_chunks(data: bytes) -> list[tuple[int, bytes]]:
    chunks: list[tuple[int, bytes]] = []
    off = 0
    while off < len(data):
        t = data[off]
        off += 1
        l = struct.unpack(">I", data[off : off + 4])[0]
        off += 4
        p = data[off : off + l]
        off += l
        chunks.append((t, p))
    return chunks


def test_encode_response_emits_framed_chunks() -> None:
    codec = MsgPackLuaCodec(_config())
    result = DuuiResult(errors=["sample error"])

    body = codec.encode_response(result)
    chunks = _parse_chunks(body)

    assert chunks[0][0] == CHUNK_START
    assert chunks[-1][0] == CHUNK_END
    assert any(t == CHUNK_ERROR for t, _ in chunks)


def test_decode_request_requires_start_and_end() -> None:
    codec = MsgPackLuaCodec(_config())

    sofa_payload = msgpack.packb(
        {
            "mimeType": "text/plain; charset=utf-8",
            "language": "x-unspecified",
            "data": "hello",
        },
        use_bin_type=True,
    )

    body = bytearray()
    body.append(CHUNK_START)
    body.extend(struct.pack(">I", 0))
    body.append(CHUNK_SOFA)
    body.extend(struct.pack(">I", len(sofa_payload)))
    body.extend(sofa_payload)
    body.append(CHUNK_END)
    body.extend(struct.pack(">I", 0))

    doc = codec.decode_request(bytes(body))
    assert doc.sofa.data == "hello"


def test_decode_request_rejects_unknown_chunk() -> None:
    codec = MsgPackLuaCodec(_config())

    body = bytearray()
    body.append(CHUNK_START)
    body.extend(struct.pack(">I", 0))
    body.append(0x99)
    body.extend(struct.pack(">I", 0))
    body.append(CHUNK_END)
    body.extend(struct.pack(">I", 0))

    try:
        codec.decode_request(bytes(body))
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "unknown chunk type" in str(exc)


def test_lua_script_shape_is_valid_for_comm_layer() -> None:
    codec = MsgPackLuaCodec(_config())
    content = codec.communication_layer_content()

    assert content["kind"] == "custom"
    assert content["format"] == "lua"
    assert content["version"] == 1

    script = content["spec"]
    assert isinstance(script, str)
    assert "function serialize" in script
    assert "function deserialize" in script
    assert "local descriptor = json.decode" in script
    assert "CHUNK_FEATURE_STRUCTURE" in script


def test_legacy_descriptor_shape_is_normalized() -> None:
    payload = {
        "meta": {
            "implementation_lang": "Python",
            "meta": {},
            "settings": {
                "validation": {
                    "strict_mime_validation": True,
                    "strict_input_mime_check": True,
                    "strict_output_mime_check": True,
                    "strict_sofa_data_type_validation": True,
                    "strict_descriptor_mime_pattern_validation": True,
                },
                "limits": {"request_max_bytes": None, "response_max_bytes": None},
                "errors": {"fail_on_codec_error": True, "include_validation_details": True},
                "logging": {"enabled": True},
            },
        },
        "descriptor": {
            "name": "legacy",
            "version": "1.0.0",
            "input": {
                "domain": {
                    "sofa": {"mimeType": "text/plain; charset=utf-8", "language": "x-unspecified"},
                    "optional_types": ["uima.tcas.Annotation"],
                },
                "optional_inputs": [{"type": "uima.tcas.Annotation", "exclude": {}}],
            },
            "output": {
                "sofa": {"mimeType": "text/plain; charset=utf-8", "language": "x-unspecified"},
                "types": [],
            },
        },
        "typesystem_xml_path": "/tmp/non-existing-typesystem.xml",
        "parameters_schema": {},
    }

    config = AnnotatorConfig.model_validate(payload)
    assert config.descriptor.input.sofa.text is not None
    assert config.descriptor.input.sofa.text.mimeType == "text/plain; charset=utf-8"
    assert "uima.tcas.Annotation" in config.descriptor.input.types
