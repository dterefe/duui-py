from __future__ import annotations

import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, cast

import msgpack

from duui_py.codecs.base import Codec
from duui_py.models import AnnotatorConfig, AnnotatorDescriptor, DuuiDocument, DuuiResult, FsRec, SofaPayload
from duui_py.models.fs_builder import build_feature_structures

CHUNK_START = 0x01
CHUNK_SOFA = 0x02
CHUNK_ANNOTATION = 0x03
CHUNK_FEATURE_STRUCTURE = 0x04
CHUNK_END = 0x05
CHUNK_ERROR = 0x06


class MsgPackLuaCodec(Codec[DuuiDocument, DuuiResult]):
    """Descriptor-driven Lua communication layer codec with strict framed msgpack chunks."""

    name = "msgpack-lua"
    request_media_type = "application/x-msgpack"
    response_media_type = "application/x-msgpack"

    def __init__(self, config: AnnotatorConfig):
        self.config = config
        self.descriptor = config.descriptor
        self.typesystem_info = self._parse_typesystem_xml()

    def communication_layer_content(self) -> dict[str, str | int]:
        return {
            "kind": "custom",
            "format": "lua",
            "version": 1,
            "spec": self._generate_lua_script(),
        }

    def decode_request(self, body: bytes) -> DuuiDocument:
        chunks = self._parse_chunked_stream(body)
        if not chunks:
            raise ValueError("empty chunk stream")
        if chunks[0][0] != CHUNK_START:
            raise ValueError("first chunk must be START")
        if chunks[0][1]:
            raise ValueError("START chunk must not contain payload")
        if chunks[-1][0] != CHUNK_END:
            raise ValueError("chunk stream must end with END")
        if chunks[-1][1]:
            raise ValueError("END chunk must not contain payload")

        sofa_payload: SofaPayload | None = None
        fs_items: list[FsRec] = []

        for index, (chunk_type, payload) in enumerate(chunks):
            if chunk_type == CHUNK_START:
                if index != 0:
                    raise ValueError("START chunk may only appear at stream beginning")
                continue
            if chunk_type == CHUNK_END:
                if index != len(chunks) - 1:
                    raise ValueError("END chunk may only appear at stream end")
                continue
            if chunk_type == CHUNK_ERROR:
                raise ValueError(self._decode_error_payload(payload))
            if chunk_type == CHUNK_SOFA:
                unpacked = self._decode_msgpack_map(payload)
                sofa_payload = SofaPayload(
                    mimeType=str(unpacked.get("mimeType", self.descriptor.input.default_mime_type())),
                    language=str(unpacked.get("language", self.descriptor.input.default_language())),
                    data=cast(str | bytes, unpacked.get("data", "")),
                )
                continue
            if chunk_type in (CHUNK_ANNOTATION, CHUNK_FEATURE_STRUCTURE):
                unpacked = self._decode_msgpack_map(payload)
                fs_items.append(
                    FsRec(
                        id=int(unpacked.get("id", 0)),
                        ref=cast(int | None, unpacked.get("ref")),
                        type=str(unpacked.get("type", "")),
                        begin=cast(int | None, unpacked.get("begin")),
                        end=cast(int | None, unpacked.get("end")),
                        features=cast(dict[str, Any], unpacked.get("features", {})),
                    )
                )
                continue
            raise ValueError(f"unknown chunk type: 0x{chunk_type:02X}")

        if sofa_payload is None:
            sofa_payload = SofaPayload(
                mimeType=self.descriptor.input.default_mime_type(),
                language=self.descriptor.input.default_language(),
                data="",
            )

        return DuuiDocument(parameters={}, view="", sofa=sofa_payload, fs=fs_items)

    def encode_response(self, result: DuuiResult) -> bytes:
        chunks: list[tuple[int, bytes]] = [(CHUNK_START, b"")]

        if result.sofa is not None:
            chunks.append(
                (
                    CHUNK_SOFA,
                    msgpack.packb(
                        {
                            "mimeType": result.sofa.mimeType,
                            "language": result.sofa.language,
                            "data": result.sofa.data,
                        },
                        use_bin_type=True,
                    ),
                )
            )

        if result.feature_structures:
            for fs_item in build_feature_structures(result.feature_structures):
                chunks.append((CHUNK_FEATURE_STRUCTURE, msgpack.packb(fs_item.model_dump(by_alias=True), use_bin_type=True)))

        if result.annotations:
            for annotation in result.annotations:
                chunks.append(
                    (
                        CHUNK_ANNOTATION,
                        msgpack.packb(
                            {
                                "ref": annotation.ref,
                                "type": annotation.type,
                                "begin": annotation.begin,
                                "end": annotation.end,
                                "features": annotation.features,
                            },
                            use_bin_type=True,
                        ),
                    )
                )

        if result.meta is not None:
            chunks.append((CHUNK_FEATURE_STRUCTURE, msgpack.packb(result.meta.model_dump(), use_bin_type=True)))

        if result.modification_meta is not None:
            chunks.append((CHUNK_FEATURE_STRUCTURE, msgpack.packb(result.modification_meta.model_dump(), use_bin_type=True)))

        for error in result.errors:
            chunks.append((CHUNK_ERROR, msgpack.packb({"message": error}, use_bin_type=True)))

        chunks.append((CHUNK_END, b""))
        return self._serialize_chunks(chunks)

    def _decode_msgpack_map(self, payload: bytes) -> dict[str, Any]:
        unpacked = cast(object, msgpack.unpackb(payload, raw=False, strict_map_key=False))
        if not isinstance(unpacked, dict):
            raise ValueError("chunk payload must decode to msgpack map")
        if not all(isinstance(k, str) for k in unpacked):
            raise ValueError("chunk payload map keys must be strings")
        return cast(dict[str, Any], unpacked)

    def _decode_error_payload(self, payload: bytes) -> str:
        try:
            data = msgpack.unpackb(payload, raw=False, strict_map_key=False)
            if isinstance(data, dict):
                message = data.get("message")
                if isinstance(message, str) and message:
                    return f"received ERROR chunk: {message}"
            if isinstance(data, str) and data:
                return f"received ERROR chunk: {data}"
        except Exception:
            pass
        return "received ERROR chunk"

    def _parse_chunked_stream(self, data: bytes) -> list[tuple[int, bytes]]:
        chunks: list[tuple[int, bytes]] = []
        offset = 0
        total = len(data)

        while offset < total:
            if total - offset < 5:
                raise ValueError("truncated chunk header")
            chunk_type = data[offset]
            offset += 1
            payload_len = struct.unpack(">I", data[offset : offset + 4])[0]
            offset += 4

            if payload_len < 0:
                raise ValueError("invalid payload length")
            if total - offset < payload_len:
                raise ValueError("truncated chunk payload")

            payload = data[offset : offset + payload_len]
            offset += payload_len
            chunks.append((chunk_type, payload))

        return chunks

    def _serialize_chunks(self, chunks: list[tuple[int, bytes]]) -> bytes:
        out = bytearray()
        for chunk_type, payload in chunks:
            out.append(chunk_type)
            out.extend(struct.pack(">I", len(payload)))
            out.extend(payload)
        return bytes(out)

    def _parse_typesystem_xml(self) -> dict[str, Any]:
        path = Path(self.config.typesystem_xml_path)
        if not path.exists():
            return {}

        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except Exception:
            return {}

        def local_name(tag: str) -> str:
            if "}" in tag:
                return tag.rsplit("}", 1)[1]
            return tag

        collected_types: list[dict[str, Any]] = []
        for elem in root.iter():
            if local_name(elem.tag) != "typeDescription":
                continue

            name: str | None = None
            supertype: str | None = None
            features: list[dict[str, str | None]] = []

            for child in elem:
                child_name = local_name(child.tag)
                if child_name == "name":
                    name = (child.text or "").strip() or None
                elif child_name == "supertypeName":
                    supertype = (child.text or "").strip() or None
                elif child_name == "features":
                    for feature in child:
                        if local_name(feature.tag) != "featureDescription":
                            continue
                        feature_name: str | None = None
                        feature_range: str | None = None
                        for fchild in feature:
                            fchild_name = local_name(fchild.tag)
                            if fchild_name == "name":
                                feature_name = (fchild.text or "").strip() or None
                            elif fchild_name == "rangeTypeName":
                                feature_range = (fchild.text or "").strip() or None
                        features.append({"name": feature_name, "range": feature_range})

            collected_types.append(
                {
                    "name": name,
                    "supertype": supertype,
                    "features": features,
                }
            )

        return {"types": collected_types}

    def _generate_lua_script(self) -> str:
        descriptor_json = json.dumps(self.descriptor.model_dump(), ensure_ascii=False)
        typesystem_json = json.dumps(self.typesystem_info, ensure_ascii=False)

        return f'''-- MsgPack Lua communication script for {self.descriptor.name}
-- Auto-generated from annotator descriptor
-- Framing: 1-byte type + 4-byte big-endian length + payload

MessagePack = luajava.bindClass("org.msgpack.core.MessagePack")

local descriptor = json.decode([=[{descriptor_json}]=])
local typesystem_info = json.decode([=[{typesystem_json}]=])

local CHUNK_START = 0x01
local CHUNK_SOFA = 0x02
local CHUNK_ANNOTATION = 0x03
local CHUNK_FEATURE_STRUCTURE = 0x04
local CHUNK_END = 0x05
local CHUNK_ERROR = 0x06

local function len_bytes_be(n)
    return string.char(
        math.floor(n / 16777216) % 256,
        math.floor(n / 65536) % 256,
        math.floor(n / 256) % 256,
        n % 256
    )
end

local function write_chunk(output_stream, chunk_type, payload)
    output_stream:write(string.char(chunk_type))
    output_stream:write(len_bytes_be(#payload))
    if #payload > 0 then
        output_stream:write(payload)
    end
end

local function read_exact(input_stream, n)
    local data = input_stream:read(n)
    if not data or #data < n then
        return nil
    end
    return data
end

local function read_chunk(input_stream)
    local type_b = read_exact(input_stream, 1)
    if not type_b then
        return nil, "eof"
    end

    local len_b = read_exact(input_stream, 4)
    if not len_b then
        return nil, "truncated-length"
    end

    local payload_len =
        string.byte(len_b, 1) * 16777216 +
        string.byte(len_b, 2) * 65536 +
        string.byte(len_b, 3) * 256 +
        string.byte(len_b, 4)

    local payload = ""
    if payload_len > 0 then
        local p = read_exact(input_stream, payload_len)
        if not p then
            return nil, "truncated-payload"
        end
        payload = p
    end

    return {{ type = string.byte(type_b), payload = payload }}
end

local function pack_error_payload(message)
    local p = MessagePack:newDefaultBufferPacker()
    p:packMapHeader(1)
    p:packString("message")
    p:packString(tostring(message))
    local out = p:toByteArray()
    p:close()
    return out
end

function serialize(inputCas, outputStream, parameters, sourceView)
    local ok, err = pcall(function()
        write_chunk(outputStream, CHUNK_START, "")

        local mime = "text/plain; charset=utf-8"
        if descriptor and descriptor.input and descriptor.input.sofa then
            local ds = descriptor.input.sofa
            if ds.text and ds.text.mimeType then
                mime = ds.text.mimeType
            elseif ds.bytes and ds.bytes.mimeType then
                mime = ds.bytes.mimeType
            elseif ds.uri and ds.uri.mimeType then
                mime = ds.uri.mimeType
            end
        end
        local lang = inputCas:getDocumentLanguage() or "x-unspecified"
        if descriptor and descriptor.input and descriptor.input.sofa then
            local ds = descriptor.input.sofa
            if ds.text and ds.text.language then
                lang = ds.text.language
            elseif ds.bytes and ds.bytes.language then
                lang = ds.bytes.language
            elseif ds.uri and ds.uri.language then
                lang = ds.uri.language
            end
        end
        local text = inputCas:getSofaDataString() or ""

        local p = MessagePack:newDefaultBufferPacker()
        p:packMapHeader(3)
        p:packString("mimeType")
        p:packString(mime)
        p:packString("language")
        p:packString(lang)
        p:packString("data")
        p:packString(text)

        local sofa_payload = p:toByteArray()
        p:close()

        write_chunk(outputStream, CHUNK_SOFA, sofa_payload)
        write_chunk(outputStream, CHUNK_END, "")
    end)

    if not ok then
        write_chunk(outputStream, CHUNK_ERROR, pack_error_payload(err))
    end
end

function deserialize(inputCas, inputStream)
    local saw_start = false

    while true do
        local chunk, err = read_chunk(inputStream)
        if not chunk then
            if err == "eof" then
                error("missing END chunk")
            end
            error("malformed chunk stream: " .. tostring(err))
        end

        local t = chunk.type
        local payload = chunk.payload

        if t == CHUNK_START then
            if saw_start then
                error("duplicate START chunk")
            end
            if #payload ~= 0 then
                error("START chunk must be empty")
            end
            saw_start = true

        elseif t == CHUNK_SOFA then
            local u = MessagePack:newDefaultUnpacker(payload)
            local map_size = u:unpackMapHeader()
            local data = nil
            local mime = nil
            for _ = 1, map_size do
                local k = u:unpackString()
                if k == "data" then
                    data = u:unpackString()
                elseif k == "mimeType" then
                    mime = u:unpackString()
                else
                    u:skipValue()
                end
            end
            u:close()
            if data and mime then
                inputCas:setSofaDataString(data, mime)
            end

        elseif t == CHUNK_ANNOTATION or t == CHUNK_FEATURE_STRUCTURE then
            local u = MessagePack:newDefaultUnpacker(payload)
            u:skipValue()
            u:close()

        elseif t == CHUNK_END then
            if #payload ~= 0 then
                error("END chunk must be empty")
            end
            return

        elseif t == CHUNK_ERROR then
            error("received ERROR chunk")

        else
            error("unknown chunk type: " .. tostring(t))
        end
    end
end
'''

    @classmethod
    def generate_default_lua_script(cls, descriptor: AnnotatorDescriptor, typesystem_info: dict[str, Any]) -> str:
        class TempConfig:
            def __init__(self, desc: AnnotatorDescriptor):
                self.descriptor = desc
                self.typesystem_xml_path = ""

        codec = cls(cast(AnnotatorConfig, TempConfig(descriptor)))
        codec.typesystem_info = typesystem_info
        return codec._generate_lua_script()
