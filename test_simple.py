#!/usr/bin/env python3
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.codecs.msgpack_lua.codec import CHUNK_END, CHUNK_ERROR, CHUNK_START
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


def parse_chunks(data: bytes) -> list[tuple[int, bytes]]:
    chunks: list[tuple[int, bytes]] = []
    offset = 0
    while offset < len(data):
        t = data[offset]
        offset += 1
        l = struct.unpack(">I", data[offset : offset + 4])[0]
        offset += 4
        p = data[offset : offset + l]
        offset += l
        chunks.append((t, p))
    return chunks


def make_codec() -> MsgPackLuaCodec:
    cfg = AnnotatorConfig(
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
        description="simple-test",
        descriptor=AnnotatorDescriptor(
            name="simple",
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
        ),
        typesystem_xml_path="/tmp/no-typesystem.xml",
        parameters_schema={},
    )
    return MsgPackLuaCodec(cfg)


def main() -> int:
    codec = make_codec()
    body = codec.encode_response(DuuiResult(errors=["x"]))
    chunks = parse_chunks(body)

    assert chunks[0][0] == CHUNK_START
    assert chunks[-1][0] == CHUNK_END
    assert any(t == CHUNK_ERROR for t, _ in chunks)

    comm = codec.communication_layer_content()
    assert comm["format"] == "lua"
    assert isinstance(comm["spec"], str) and "function serialize" in comm["spec"]

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
