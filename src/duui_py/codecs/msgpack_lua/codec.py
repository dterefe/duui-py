from __future__ import annotations

import json
import struct
from typing import Any, cast

import msgpack

from duui_py.codecs.base import Codec
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    V1RequestEnvelope,
    DuuiResult,
    SoFa,
    SoFaAnnotationSpans,
    sofa_annotation_type,
    sofa_default_for_mime,
    sofa_from_wire,
    sofa_kind,
    sofa_to_wire_data,
)
from duui_py.models.uima import FeatureStructure, normalize_uima_value

CHUNK_START = 0x01
CHUNK_SOFA = 0x02
CHUNK_ANNOTATION = 0x03
CHUNK_FEATURE_STRUCTURE = 0x04
CHUNK_END = 0x05
CHUNK_ERROR = 0x06


class MsgPackLuaCodec(Codec[V1RequestEnvelope, DuuiResult]):
    """Descriptor-driven Lua communication layer codec with strict framed msgpack chunks."""

    name = "msgpack-lua"
    request_media_type = "application/x-msgpack"
    response_media_type = "application/x-msgpack"

    def __init__(self, config: AnnotatorConfig):
        self.config = config
        self.descriptor = config.descriptor

    def _default_input_mime(self) -> str:
        resolved = self.descriptor.input.first_available()
        return resolved.mimeType if resolved and resolved.mimeType else "text/plain; charset=utf-8"

    def _default_input_language(self) -> str:
        resolved = self.descriptor.input.first_available()
        if resolved and resolved.languages:
            return resolved.languages[0]
        return "x-unspecified"

    def communication_layer_content(self) -> dict[str, str | int]:
        return {
            "kind": "custom",
            "format": "lua",
            "version": 1,
            "spec": self._generate_lua_script(),
        }

    def decode_request(self, body: bytes) -> V1RequestEnvelope:
        chunks = self._parse_chunked_stream(body)
        if not chunks:
            raise ValueError("empty chunk stream")
        if chunks[0][0] != CHUNK_START:
            raise ValueError("first chunk must be START")
        parameters: dict[str, Any] = {}
        view = ""
        if chunks[0][1]:
            start_payload = self._decode_msgpack_map(chunks[0][1])
            raw_parameters = start_payload.get("parameters", {})
            if isinstance(raw_parameters, dict):
                parameters = {str(k): normalize_uima_value(v) for k, v in raw_parameters.items()}
            raw_view = start_payload.get("view", "")
            if isinstance(raw_view, str):
                view = raw_view
        if chunks[-1][0] != CHUNK_END:
            raise ValueError("chunk stream must end with END")
        if chunks[-1][1]:
            raise ValueError("END chunk must not contain payload")

        sofa_payload: SoFa | None = None
        fs_items: list[FeatureStructure] = []

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
                mime_value = unpacked.get("mimeType", self._default_input_mime())
                lang_value = unpacked.get("language", self._default_input_language())
                if not isinstance(mime_value, str) or not isinstance(lang_value, str):
                    raise ValueError("invalid SOFA payload mimeType/language")
                annotation_type = unpacked.get("annotationType")
                spans = unpacked.get("spans")
                sofa_payload = sofa_from_wire(
                    mime_type=mime_value,
                    language=lang_value,
                    data=unpacked.get("data"),
                    annotation_type=annotation_type if isinstance(annotation_type, str) else None,
                    spans=[str(v) for v in spans] if isinstance(spans, list) else None,
                )
                continue
            if chunk_type in (CHUNK_ANNOTATION, CHUNK_FEATURE_STRUCTURE):
                unpacked = self._decode_msgpack_map(payload)
                raw_features = cast(dict[str, Any], unpacked.get("features", {}))
                features = {str(k): normalize_uima_value(v) for k, v in raw_features.items()}
                covered_text = unpacked.get("coveredText")
                if isinstance(covered_text, str):
                    features["coveredText"] = covered_text
                fs_items.append(
                    FeatureStructure(
                        ref=cast(int | None, unpacked.get("ref")),
                        type=str(unpacked.get("type", "")),
                        begin=cast(int | None, unpacked.get("begin")),
                        end=cast(int | None, unpacked.get("end")),
                        features=features,
                    )
                )
                continue
            raise ValueError(f"unknown chunk type: 0x{chunk_type:02X}")

        if sofa_payload is None and fs_items:
            spans: list[str] = []
            annotation_type = ""
            for item in fs_items:
                if not annotation_type and item.type:
                    annotation_type = item.type
                covered = item.features.get("coveredText")
                if isinstance(covered, str):
                    spans.append(covered)
            if annotation_type:
                sofa_payload = SoFaAnnotationSpans(
                    mimeType="application/x-uima-annotation-spans",
                    language=self._default_input_language(),
                    annotationType=annotation_type,
                    spans=spans,
                )

        if sofa_payload is None:
            sofa_payload = sofa_default_for_mime(
                mime_type=self._default_input_mime(),
                language=self._default_input_language(),
            )

        return V1RequestEnvelope(parameters=parameters, view=view, sofa=sofa_payload, fs=fs_items)

    def encode_response(self, result: DuuiResult) -> bytes:
        chunks: list[tuple[int, bytes]] = [(CHUNK_START, b"")]

        if result.sofa is not None:
            payload_map: dict[str, Any] = {
                "type": "uima.cas.Sofa",
                "kind": sofa_kind(result.sofa),
                "mimeType": result.sofa.mimeType,
                "language": result.sofa.language,
                "data": sofa_to_wire_data(result.sofa),
            }
            annotation_type = sofa_annotation_type(result.sofa)
            if annotation_type:
                payload_map["annotationType"] = annotation_type
                payload_map["spans"] = list(cast(SoFaAnnotationSpans, result.sofa).spans)
            chunks.append(
                (
                    CHUNK_SOFA,
                    msgpack.packb(payload_map, use_bin_type=True),
                )
            )

        if result.feature_structures:
            for fs_item in result.feature_structures:
                chunks.append(
                    (
                        CHUNK_FEATURE_STRUCTURE,
                        msgpack.packb(
                            {
                                "ref": fs_item.ref,
                                "type": fs_item.type,
                                "begin": fs_item.begin,
                                "end": fs_item.end,
                                "features": {k: normalize_uima_value(v) for k, v in fs_item.feature_map().items()},
                            },
                            use_bin_type=True,
                        ),
                    )
                )

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
                                "features": {k: normalize_uima_value(v) for k, v in annotation.feature_map().items()},
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

    def _generate_lua_script(self) -> str:
        descriptor_json = json.dumps(self.descriptor.model_dump(), ensure_ascii=False)

        return f'''-- MsgPack Lua communication script for {self.descriptor.name}
-- Auto-generated from annotator descriptor
-- Framing: 1-byte type + 4-byte big-endian length + payload

if MessagePack == nil then
    MessagePack = luajava.bindClass("org.msgpack.core.MessagePack")
end
if JCasUtil == nil then
    JCasUtil = luajava.bindClass("org.apache.uima.fit.util.JCasUtil")
end
if DUUIBytes == nil then
    DUUIBytes = luajava.bindClass("org.texttechnologylab.duui.communication.DUUIBytes")
end

local descriptor = json.decode([=[{descriptor_json}]=])

local CHUNK_START = 0x01
local CHUNK_SOFA = 0x02
local CHUNK_ANNOTATION = 0x03
local CHUNK_FEATURE_STRUCTURE = 0x04
local CHUNK_END = 0x05
local CHUNK_ERROR = 0x06

local function byte_len(value)
    if value == nil then
        return 0
    end
    if type(value) == "string" then
        return #value
    end
    return DUUIBytes:length(value)
end

local function write_chunk(output_stream, chunk_type, payload)
    local payload_len = byte_len(payload)
    output_stream:write(chunk_type)
    output_stream:write(math.floor(payload_len / 16777216) % 256)
    output_stream:write(math.floor(payload_len / 65536) % 256)
    output_stream:write(math.floor(payload_len / 256) % 256)
    output_stream:write(payload_len % 256)
    if payload_len > 0 then
        output_stream:write(payload)
    end
end

local function read_exact(input_stream, n)
    return DUUIBytes:readNBytes(input_stream, n)
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
        DUUIBytes:unsignedByte(len_b, 0) * 16777216 +
        DUUIBytes:unsignedByte(len_b, 1) * 65536 +
        DUUIBytes:unsignedByte(len_b, 2) * 256 +
        DUUIBytes:unsignedByte(len_b, 3)

    local payload = nil
    if payload_len > 0 then
        local p = read_exact(input_stream, payload_len)
        if not p then
            return nil, "truncated-payload"
        end
        payload = p
    end

    return {{ type = DUUIBytes:unsignedByte(type_b, 0), payload = payload }}
end

local function unpack_value(u)
    local value = u:unpackValue()
    if value:isNilValue() then
        return nil
    end
    if value:isStringValue() then
        return value:asStringValue():asString()
    end
    if value:isIntegerValue() then
        return value:asIntegerValue():asLong()
    end
    if value:isFloatValue() then
        return value:asFloatValue():toDouble()
    end
    if value:isBooleanValue() then
        return value:asBooleanValue():getBoolean()
    end
    return tostring(value)
end

local function set_feature(fs, feature, value)
    if feature == nil or value == nil then
        return
    end
    local range = feature:getRange()
    local range_name = range:getName()
    if range_name == "uima.cas.String" then
        fs:setStringValue(feature, tostring(value))
    elseif range_name == "uima.cas.Short" then
        fs:setShortValue(feature, value)
    elseif range_name == "uima.cas.Integer" then
        fs:setIntValue(feature, value)
    elseif range_name == "uima.cas.Long" then
        fs:setLongValue(feature, value)
    elseif range_name == "uima.cas.Float" then
        fs:setFloatValue(feature, value)
    elseif range_name == "uima.cas.Double" then
        fs:setDoubleValue(feature, value)
    elseif range_name == "uima.cas.Boolean" then
        fs:setBooleanValue(feature, value)
    end
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

local function pack_start_payload(parameters, sourceView)
    local p = MessagePack:newDefaultBufferPacker()
    p:packMapHeader(2)
    p:packString("parameters")
    if type(parameters) == "table" then
        local count = 0
        for k, _ in pairs(parameters) do
            if type(k) == "string" then
                count = count + 1
            end
        end
        p:packMapHeader(count)
        for k, v in pairs(parameters) do
            if type(k) == "string" then
                p:packString(k)
                if type(v) == "string" then
                    p:packString(v)
                elseif type(v) == "number" then
                    p:packDouble(v)
                elseif type(v) == "boolean" then
                    p:packBoolean(v)
                elseif v == nil then
                    p:packNil()
                else
                    p:packString(tostring(v))
                end
            end
        end
    else
        p:packMapHeader(0)
    end
    p:packString("view")
    if type(sourceView) == "string" then
        p:packString(sourceView)
    else
        p:packString("")
    end
    local out = p:toByteArray()
    p:close()
    return out
end

function serialize(inputCas, outputStream, parameters, sourceView)
    local ok, err = pcall(function()
        write_chunk(outputStream, CHUNK_START, pack_start_payload(parameters, sourceView))

        local function domain_first_mime(domain_name)
            if not descriptor or not descriptor.input or not descriptor.input[domain_name] then
                return nil
            end
            local domain = descriptor.input[domain_name]
            if domain.default and domain.default.mimeType then
                return domain.default.mimeType
            end
            for k, v in pairs(domain) do
                if k ~= "default" and k ~= "types" and k ~= "languages" and type(v) == "table" and v.mimeType then
                    return v.mimeType
                end
            end
            return nil
        end
        local mime = domain_first_mime("text") or domain_first_mime("bytes") or domain_first_mime("uri") or "text/plain; charset=utf-8"
        local prefer_bytes_sofa = domain_first_mime("bytes") ~= nil and domain_first_mime("text") == nil
        local lang = inputCas:getDocumentLanguage() or "x-unspecified"
        if descriptor and descriptor.input and descriptor.input.languages and #descriptor.input.languages > 0 then
            lang = descriptor.input.languages[1]
        end
        local annotation_selection = nil
        if descriptor and descriptor.input and descriptor.input.annotation and descriptor.input.annotation.types then
            annotation_selection = {{}}
            for _, type_list in pairs(descriptor.input.annotation.types) do
                if type(type_list) == "table" then
                    for i = 1, #type_list do
                        annotation_selection[#annotation_selection + 1] = type_list[i]
                    end
                end
            end
        end

        if annotation_selection and #annotation_selection > 0 then
            local selected_type = annotation_selection[1]
            local spans = {{}}
            for i = 1, #annotation_selection do
                local type_name = annotation_selection[i]
                local ok_bind, ann_cls = pcall(function()
                    return luajava.bindClass(type_name)
                end)
                if ok_bind and ann_cls ~= nil then
                    local ann_list = luajava.newInstance("java.util.ArrayList", JCasUtil:select(inputCas, ann_cls))
                    local it = ann_list:listIterator()
                    while it:hasNext() do
                        local ann = it:next()
                        local covered = ann:getCoveredText() or ""
                        spans[#spans + 1] = covered
                    end
                end
            end
            local p = MessagePack:newDefaultBufferPacker()
            p:packMapHeader(7)
            p:packString("type")
            p:packString("uima.cas.Sofa")
            p:packString("kind")
            p:packString("annotation_spans")
            p:packString("mimeType")
            p:packString("application/x-uima-annotation-spans")
            p:packString("language")
            p:packString(lang)
            p:packString("annotationType")
            p:packString(selected_type)
            p:packString("spans")
            p:packArrayHeader(#spans)
            for i = 1, #spans do
                p:packString(spans[i])
            end
            p:packString("data")
            p:packArrayHeader(#spans)
            for i = 1, #spans do
                p:packString(spans[i])
            end
            local sofa_payload = p:toByteArray()
            p:close()
            write_chunk(outputStream, CHUNK_SOFA, sofa_payload)
        else
            local p = MessagePack:newDefaultBufferPacker()
            p:packMapHeader(6)
            p:packString("type")
            p:packString("uima.cas.Sofa")
            p:packString("kind")
            if prefer_bytes_sofa then
                p:packString("bytes")
            else
                p:packString("text")
            end
            p:packString("mimeType")
            p:packString(mime)
            p:packString("language")
            p:packString(lang)
            p:packString("data")
            local sofa_data_for_features = nil
            if prefer_bytes_sofa then
                local sofa_array = inputCas:getSofaDataArray()
                local parts = {{}}
                if sofa_array ~= nil then
                    local size = sofa_array:size()
                    for i = 0, size - 1 do
                        local b = sofa_array:get(i)
                        if b < 0 then
                            b = b + 256
                        end
                        parts[#parts + 1] = string.char(b)
                    end
                end
                local sofa_text_bytes = table.concat(parts)
                p:packString(sofa_text_bytes)
                sofa_data_for_features = sofa_text_bytes
            else
                local text = inputCas:getSofaDataString() or ""
                p:packString(text)
                sofa_data_for_features = text
            end
            p:packString("features")
            p:packMapHeader(3)
            p:packString("mimeType")
            p:packString(mime)
            p:packString("language")
            p:packString(lang)
            p:packString("data")
            if prefer_bytes_sofa then
                p:packString(sofa_data_for_features)
            else
                p:packString(sofa_data_for_features)
            end

            local sofa_payload = p:toByteArray()
            p:close()
            write_chunk(outputStream, CHUNK_SOFA, sofa_payload)
        end

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
            if byte_len(payload) > 0 then
                local u = MessagePack:newDefaultUnpacker(payload)
                u:skipValue()
                u:close()
            end
            saw_start = true

        elseif t == CHUNK_SOFA then
            local u = MessagePack:newDefaultUnpacker(payload)
            local map_size = u:unpackMapHeader()
            local data = nil
            local mime = nil
            local lang = nil
            for _ = 1, map_size do
                local k = u:unpackString()
                if k == "features" then
                    local fs_size = u:unpackMapHeader()
                    for __ = 1, fs_size do
                        local fk = u:unpackString()
                        if fk == "data" then
                            data = u:unpackString()
                        elseif fk == "mimeType" then
                            mime = u:unpackString()
                        elseif fk == "language" then
                            lang = u:unpackString()
                        else
                            u:skipValue()
                        end
                    end
                elseif k == "data" then
                    data = u:unpackString()
                elseif k == "mimeType" then
                    mime = u:unpackString()
                elseif k == "language" then
                    lang = u:unpackString()
                else
                    u:skipValue()
                end
            end
            u:close()
            if data and mime then
                inputCas:setSofaDataString(data, mime)
                if lang and #lang > 0 then
                    inputCas:setDocumentLanguage(lang)
                end
            end

        elseif t == CHUNK_ANNOTATION then
            local u = MessagePack:newDefaultUnpacker(payload)
            local map_size = u:unpackMapHeader()
            local type_name = nil
            local begin = nil
            local finish = nil
            local features = {{}}
            for _ = 1, map_size do
                local k = u:unpackString()
                if k == "type" then
                    type_name = u:unpackString()
                elseif k == "begin" then
                    begin = u:unpackInt()
                elseif k == "end" then
                    finish = u:unpackInt()
                elseif k == "features" then
                    local fs_size = u:unpackMapHeader()
                    for __ = 1, fs_size do
                        local fk = u:unpackString()
                        features[fk] = unpack_value(u)
                    end
                else
                    u:skipValue()
                end
            end
            u:close()
            if type_name ~= nil and begin ~= nil and finish ~= nil then
                local cas = inputCas:getCas()
                local ts = cas:getTypeSystem()
                local ann_type = ts:getType(type_name)
                if ann_type == nil then
                    error("unknown annotation type: " .. tostring(type_name))
                end
                local ann = cas:createAnnotation(ann_type, begin, finish)
                for fk, fv in pairs(features) do
                    set_feature(ann, ann_type:getFeatureByBaseName(fk), fv)
                end
                cas:addFsToIndexes(ann)
            end

        elseif t == CHUNK_FEATURE_STRUCTURE then
            local u = MessagePack:newDefaultUnpacker(payload)
            u:skipValue()
            u:close()

        elseif t == CHUNK_END then
            if byte_len(payload) ~= 0 then
                error("END chunk must be empty")
            end
            return

        elseif t == CHUNK_ERROR then
            local message = "received ERROR chunk"
            if byte_len(payload) > 0 then
                local ok_unpack, unpack_err = pcall(function()
                    local u = MessagePack:newDefaultUnpacker(payload)
                    local map_size = u:unpackMapHeader()
                    for _ = 1, map_size do
                        local k = u:unpackString()
                        if k == "message" then
                            message = "received ERROR chunk: " .. tostring(u:unpackString())
                        else
                            u:skipValue()
                        end
                    end
                    u:close()
                end)
                if not ok_unpack then
                    message = message .. " (failed to decode payload: " .. tostring(unpack_err) .. ")"
                end
            end
            error(message)

        else
            error("unknown chunk type: " .. tostring(t))
        end
    end
end
'''

    @classmethod
    def generate_default_lua_script(
        cls, descriptor: AnnotatorDescriptor, typesystem_info: dict[str, Any] | None = None
    ) -> str:
        del typesystem_info

        class TempConfig:
            def __init__(self, desc: AnnotatorDescriptor):
                self.descriptor = desc
                self.typesystem_xml_path = ""

        codec = cls(cast(AnnotatorConfig, TempConfig(descriptor)))
        return codec._generate_lua_script()
