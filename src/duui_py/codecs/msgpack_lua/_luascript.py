"""Lua script generation for the MsgPack Lua codec.

Contains the Lua template string and generated setter/batch-applier builders.
"""

from __future__ import annotations

import json
from typing import Any

from duui_py.codecs.msgpack_lua._helpers import _lua_cas_setter


def generate_lua_script(
    descriptor_json: str,
    manifest_json: str,
    input_types_json: str,
    generated_setters: str,
    generated_batch_appliers: str,
    script_kind: str,
    annotator_name: str,
    protocol: str,
    compression: str,
) -> str:
    """Build the full Lua communication layer script."""
    return f"""-- {script_kind} DUUI MsgPack Lua wire protocol v2 for {annotator_name}
-- Protocol: {protocol}; compression: {compression}

if MessagePack == nil then MessagePack = luajava.bindClass("org.msgpack.core.MessagePack") end
if JCasUtil == nil then JCasUtil = luajava.bindClass("org.apache.uima.fit.util.JCasUtil") end
if DUUIBytes == nil then DUUIBytes = luajava.bindClass("org.texttechnologylab.duui.communication.DUUIBytes") end
if ByteArrayOutputStream == nil then ByteArrayOutputStream = luajava.bindClass("java.io.ByteArrayOutputStream") end
if Inflater == nil then Inflater = luajava.bindClass("java.util.zip.Inflater") end

local descriptor = json.decode([=[{descriptor_json}]=])
local manifest = json.decode([=[{manifest_json}]=])
local input_types = json.decode([=[{input_types_json}]=])
local use_zstd = manifest.compression == "zstd"
if use_zstd then
    if Zstd == nil then
        local ok_zstd, zstd_class = pcall(function() return luajava.bindClass("com.github.luben.zstd.Zstd") end)
        if ok_zstd then Zstd = zstd_class end
    end
    if ZstdInputStream == nil then
        local ok_zis, zis_class = pcall(function() return luajava.bindClass("com.github.luben.zstd.ZstdInputStream") end)
        if ok_zis then ZstdInputStream = zis_class end
    end
end

local runtime_protocol = string.sub(manifest.protocol or "", 1, 8) == "runtime-"
local chunk_sequence = 0

local CHUNK_START = 0x01
local CHUNK_SOFA = 0x02
local CHUNK_END = 0x05
local CHUNK_ERROR = 0x06
local CHUNK_ROW_BATCH = 0x10
local CHUNK_COLUMN_BATCH = 0x11
local CHUNK_COMPRESSED_BATCH = 0x12
local CHUNK_DIRECT_BATCH = 0x13
local CHUNK_DIRECT_MULTI_BATCH = 0x14

local response_types = {{}}
local response_features = {{}}
local response_ranges = {{}}
local fs_refs = {{}}
local pending_refs = {{}}

local function byte_len(value)
    if value == nil then return 0 end
    if type(value) == "string" then return #value end
    return DUUIBytes:length(value)
end

local function write_uint16(output_stream, value)
    DUUIBytes:write(output_stream, math.floor(value / 256) % 256)
    DUUIBytes:write(output_stream, value % 256)
end

local function write_uint32(output_stream, value)
    DUUIBytes:write(output_stream, math.floor(value / 16777216) % 256)
    DUUIBytes:write(output_stream, math.floor(value / 65536) % 256)
    DUUIBytes:write(output_stream, math.floor(value / 256) % 256)
    DUUIBytes:write(output_stream, value % 256)
end

local function read_uint16(bytes, offset)
    return DUUIBytes:unsignedByte(bytes, offset) * 256 +
        DUUIBytes:unsignedByte(bytes, offset + 1)
end

local function read_uint32(bytes, offset)
    return DUUIBytes:unsignedByte(bytes, offset) * 16777216 +
        DUUIBytes:unsignedByte(bytes, offset + 1) * 65536 +
        DUUIBytes:unsignedByte(bytes, offset + 2) * 256 +
        DUUIBytes:unsignedByte(bytes, offset + 3)
end

local function write_chunk(output_stream, chunk_type, payload, type_id_value, row_count, flags)
    local payload_len = byte_len(payload)
    DUUIBytes:write(output_stream, chunk_type)
    write_uint32(output_stream, payload_len)
    if runtime_protocol then
        chunk_sequence = chunk_sequence + 1
        write_uint32(output_stream, chunk_sequence)
        write_uint16(output_stream, flags or 0)
        write_uint16(output_stream, type_id_value or 0)
        write_uint32(output_stream, row_count or 0)
    end
    if payload_len > 0 then DUUIBytes:write(output_stream, payload) end
end

local function read_exact(input_stream, n)
    return DUUIBytes:readNBytes(input_stream, n)
end

local function read_chunk(input_stream)
    local type_b = read_exact(input_stream, 1)
    if not type_b then return nil, "eof" end
    local len_b = read_exact(input_stream, 4)
    if not len_b then return nil, "truncated-length" end
    local payload_len = read_uint32(len_b, 0)
    local sequence, flags, type_id_value, row_count = 0, 0, 0, 0
    if runtime_protocol then
        local meta_b = read_exact(input_stream, 12)
        if not meta_b then return nil, "truncated-runtime-header" end
        sequence = read_uint32(meta_b, 0)
        flags = read_uint16(meta_b, 4)
        type_id_value = read_uint16(meta_b, 6)
        row_count = read_uint32(meta_b, 8)
    end
    local payload = nil
    if payload_len > 0 then
        payload = read_exact(input_stream, payload_len)
        if not payload then return nil, "truncated-payload" end
    end
    return {{ type = DUUIBytes:unsignedByte(type_b, 0), payload = payload, sequence = sequence, flags = flags, type_id = type_id_value, row_count = row_count }}
end

local function inflate_bytes(payload)
    if use_zstd and Zstd ~= nil then
        return Zstd:decompress(payload, 1024 * 1024 * 64)
    end
    local inflater = luajava.newInstance("java.util.zip.Inflater")
    inflater:setInput(payload)
    local buffer = luajava.newInstance("[B", 8192)
    local output = luajava.newInstance("java.io.ByteArrayOutputStream")
    while not inflater:finished() do
        local written = inflater:inflate(buffer)
        if written == 0 then
            if inflater:needsInput() then break end
            if inflater:needsDictionary() then error("compressed payload requires a dictionary") end
        else
            output:write(buffer, 0, written)
        end
    end
    pcall(function() inflater:end_() end)
    return output:toByteArray()
end

local function unpack_value(u)
    local value = u:unpackValue()
    if value:isNilValue() then return nil end
    if value:isStringValue() then return value:asStringValue():asString() end
    if value:isIntegerValue() then return value:asIntegerValue():asLong() end
    if value:isFloatValue() then return value:asFloatValue():toDouble() end
    if value:isBooleanValue() then return value:asBooleanValue():getBoolean() end
    return tostring(value)
end

local function read_int_array(u)
    local size = u:unpackArrayHeader()
    local out = {{}}
    for i = 1, size do
        if u:tryUnpackNil() then out[i] = nil else out[i] = u:unpackInt() end
    end
    return out
end

local function read_packed_int_array(u)
    local size = u:unpackBinaryHeader()
    local bytes = u:readPayload(size)
    local out = {{}}
    local row = 1
    for offset = 0, size - 4, 4 do
        local value = read_uint32(bytes, offset)
        if value >= 2147483648 then value = value - 4294967296 end
        if value == -1 then out[row] = nil else out[row] = value end
        row = row + 1
    end
    return out
end

local function read_unsigned_varint(bytes, offset, size)
    local value = 0
    local shift = 0
    while offset < size do
        local b = DUUIBytes:unsignedByte(bytes, offset)
        value = value + (b % 128) * (2 ^ shift)
        offset = offset + 1
        if b < 128 then return value, offset end
        shift = shift + 7
    end
    error("truncated varint")
end

local function read_delta_packed_int_array(u)
    local size = u:unpackBinaryHeader()
    local bytes = u:readPayload(size)
    local out = {{}}
    local offset = 0
    local row = 1
    local previous = 0
    while offset < size do
        local b = DUUIBytes:unsignedByte(bytes, offset)
        if b == 0 then
            out[row] = nil
            offset = offset + 1
        else
            local encoded
            encoded, offset = read_unsigned_varint(bytes, offset, size)
            local zigzag = encoded - 1
            local delta
            if zigzag % 2 == 1 then
                delta = -((zigzag + 1) / 2)
            else
                delta = zigzag / 2
            end
            previous = previous + delta
            out[row] = previous
        end
        row = row + 1
    end
    return out
end

local function read_long_array(u)
    local size = u:unpackArrayHeader()
    local out = {{}}
    for i = 1, size do
        if u:tryUnpackNil() then out[i] = nil else out[i] = u:unpackLong() end
    end
    return out
end

local function read_string_or_nil_array(u)
    local size = u:unpackArrayHeader()
    local out = {{}}
    for i = 1, size do
        if u:tryUnpackNil() then out[i] = nil else out[i] = u:unpackString() end
    end
    return out
end

local function read_boolean_array(u)
    local size = u:unpackArrayHeader()
    local out = {{}}
    for i = 1, size do
        if u:tryUnpackNil() then out[i] = nil else out[i] = u:unpackBoolean() end
    end
    return out
end

local function read_double_array(u)
    local size = u:unpackArrayHeader()
    local out = {{}}
    for i = 1, size do
        if u:tryUnpackNil() then out[i] = nil else out[i] = u:unpackDouble() end
    end
    return out
end

local function read_value_array(u)
    local size = u:unpackArrayHeader()
    local out = {{}}
    for i = 1, size do out[i] = unpack_value(u) end
    return out
end

local function read_string_array(u)
    local size = u:unpackArrayHeader()
    local out = {{}}
    for i = 1, size do out[i] = u:unpackString() end
    return out
end

local function read_feature_array(u)
    local size = u:unpackArrayHeader()
    local out = {{}}
    for i = 1, size do out[i] = unpack_value(u) end
    return out
end

local function read_feature_value_array(u, type_id_value, feature_id_value)
    local ranges = response_ranges[type_id_value]
    local range = nil
    if ranges ~= nil and type(feature_id_value) == "number" then range = ranges[feature_id_value] end
    if range == "string" then return read_string_or_nil_array(u) end
    if range == "byte" or range == "short" or range == "integer" then return read_int_array(u) end
    if range == "long" then return read_long_array(u) end
    if range == "boolean" then return read_boolean_array(u) end
    if range == "float" or range == "double" then return read_double_array(u) end
    return read_value_array(u)
end

local function read_nullable_long_array(u)
    if u:tryUnpackNil() then return {{}} end
    return read_long_array(u)
end

local function max_numeric_index(values)
    local max_index = 0
    if values == nil then return 0 end
    for key, _ in pairs(values) do
        if type(key) == "number" and key > max_index then max_index = key end
    end
    return max_index
end

local function batch_row_count(refs, begins, ends, columns, sparse_columns)
    local row_count = max_numeric_index(refs)
    local begin_count = max_numeric_index(begins)
    if begin_count > row_count then row_count = begin_count end
    local end_count = max_numeric_index(ends)
    if end_count > row_count then row_count = end_count end
    if columns ~= nil then
        for i = 1, #columns do
            local count = max_numeric_index(columns[i])
            if count > row_count then row_count = count end
        end
    end
    if sparse_columns ~= nil then
        for i = 1, #sparse_columns do
            local sparse = sparse_columns[i]
            if sparse ~= nil and sparse.rows ~= nil then
                local count = max_numeric_index(sparse.rows)
                if count > row_count then row_count = count end
            end
        end
    end
    return row_count
end

local function read_direct_sparse_columns(u, type_id_value)
    if u:tryUnpackNil() then return {{}} end
    local sparse_count = u:unpackArrayHeader()
    local sparse_columns = {{}}
    for i = 1, sparse_count do
        u:unpackArrayHeader()
        local sparse_feature = u:unpackInt()
        local sparse_rows = read_int_array(u)
        local sparse_values = read_feature_value_array(u, type_id_value, sparse_feature)
        sparse_columns[i] = {{ feature = sparse_feature, rows = sparse_rows, values = sparse_values }}
    end
    return sparse_columns
end

local function read_direct_dictionary_columns(u)
    if u:tryUnpackNil() then return {{}} end
    local dictionary_count = u:unpackArrayHeader()
    local dictionary_columns = {{}}
    for i = 1, dictionary_count do
        u:unpackArrayHeader()
        local dictionary_feature = u:unpackInt()
        local dictionary_values = read_string_array(u)
        local dictionary_ids = read_int_array(u)
        dictionary_columns[i] = {{ feature = dictionary_feature, values = dictionary_values, ids = dictionary_ids }}
    end
    return dictionary_columns
end

local function write_start(outputStream, parameters, sourceView)
    local p = MessagePack:newDefaultBufferPacker()
    if runtime_protocol then
        p:packMapHeader(6)
        p:packString("version"); p:packInt(manifest.version)
        p:packString("schemaHash"); p:packString(manifest.schemaHash or "")
        p:packString("protocol"); p:packString(manifest.protocol)
        p:packString("compression"); p:packString(manifest.compression)
    else
        p:packMapHeader(7)
    p:packString("version"); p:packInt(manifest.version)
    p:packString("protocol"); p:packString(manifest.protocol)
    p:packString("compression"); p:packString(manifest.compression)
    p:packString("types")
    p:packArrayHeader(#manifest.types)
    for i = 1, #manifest.types do p:packString(manifest.types[i]) end
    p:packString("features")
    p:packArrayHeader(#manifest.features)
    for i = 1, #manifest.features do
        local features = manifest.features[i]
        p:packArrayHeader(#features)
            for j = 1, #features do p:packString(features[j]) end
        end
    end
    p:packString("parameters")
    if type(parameters) == "table" then
        local count = 0
        for k, _ in pairs(parameters) do if type(k) == "string" then count = count + 1 end end
        p:packMapHeader(count)
        for k, v in pairs(parameters) do
            if type(k) == "string" then
                p:packString(k)
                if type(v) == "string" then p:packString(v)
                elseif type(v) == "number" then p:packDouble(v)
                elseif type(v) == "boolean" then p:packBoolean(v)
                elseif v == nil then p:packNil()
                else p:packString(tostring(v)) end
            end
        end
    else
        p:packMapHeader(0)
    end
    p:packString("view")
    if type(sourceView) == "string" then p:packString(sourceView) else p:packString("") end
    local out = p:toByteArray(); p:close()
    write_chunk(outputStream, CHUNK_START, out)
end

local function type_id(type_name)
    for i = 1, #manifest.types do
        if manifest.types[i] == type_name then return i end
    end
    return nil
end

local function write_sofa(outputStream, inputCas, mime, lang, prefer_bytes_sofa)
    local p = MessagePack:newDefaultBufferPacker()
    p:packMapHeader(5)
    p:packString("type"); p:packString("uima.cas.Sofa")
    p:packString("kind"); if prefer_bytes_sofa then p:packString("bytes") else p:packString("text") end
    p:packString("mimeType"); p:packString(mime)
    p:packString("language"); p:packString(lang)
    p:packString("data")
    if prefer_bytes_sofa then
        local sofa_array = inputCas:getSofaDataArray()
        local parts = {{}}
        if sofa_array ~= nil then
            local size = sofa_array:size()
            for i = 0, size - 1 do
                local b = sofa_array:get(i)
                if b < 0 then b = b + 256 end
                parts[#parts + 1] = string.char(b)
            end
        end
        p:packString(table.concat(parts))
    else
        p:packString(inputCas:getSofaDataString() or "")
    end
    local out = p:toByteArray(); p:close()
    write_chunk(outputStream, CHUNK_SOFA, out)
end

local function annotation_feature_matches(annotation, feature_name, expected)
    if expected == nil or expected == "" then return true end
    if feature_name == nil or feature_name == "" then feature_name = "value" end
    local feature = annotation:getType():getFeatureByBaseName(feature_name)
    if feature == nil then return false end
    local ok, value = pcall(function() return annotation:getFeatureValueAsString(feature) end)
    return ok and value == expected
end

local function write_annotation_batch(outputStream, inputCas, type_name, parameters)
    local tid = type_id(type_name)
    if tid == nil then return end
    local ok_bind, ann_cls = pcall(function() return luajava.bindClass(type_name) end)
    if not ok_bind or ann_cls == nil then return end
    local ok_select, ann_list = pcall(function()
        return luajava.newInstance("java.util.ArrayList", JCasUtil:select(inputCas, ann_cls))
    end)
    if not ok_select or ann_list == nil or ann_list:size() == 0 then return end
    local feature_filter = nil
    local feature_value = nil
    if parameters then
        feature_filter = parameters["annotation_feature"]
        feature_value = parameters["annotation_value"]
    end
    if feature_value == nil or feature_value == "" then
        local p = MessagePack:newDefaultBufferPacker()
        p:packMapHeader(7)
        p:packString("t"); p:packInt(tid)
        p:packString("k"); p:packString("ann")
        p:packString("f"); p:packArrayHeader(1); p:packString("coveredText")
        p:packString("r"); p:packArrayHeader(ann_list:size()); for i = 1, ann_list:size() do p:packNil() end
        p:packString("b"); p:packArrayHeader(ann_list:size())
        for i = 1, ann_list:size() do p:packInt(ann_list:get(i - 1):getBegin()) end
        p:packString("e"); p:packArrayHeader(ann_list:size())
        for i = 1, ann_list:size() do p:packInt(ann_list:get(i - 1):getEnd()) end
        p:packString("c"); p:packArrayHeader(1); p:packArrayHeader(ann_list:size())
        for i = 1, ann_list:size() do p:packString(ann_list:get(i - 1):getCoveredText() or "") end
        local out = p:toByteArray(); p:close()
        write_chunk(outputStream, CHUNK_COLUMN_BATCH, out, tid, ann_list:size(), 0)
        return
    end
    local rows = {{}}
    for i = 1, ann_list:size() do
        local ann = ann_list:get(i - 1)
        if annotation_feature_matches(ann, feature_filter, feature_value) then
            rows[#rows + 1] = ann
        end
    end
    if #rows == 0 then return end
    local p = MessagePack:newDefaultBufferPacker()
    p:packMapHeader(7)
    p:packString("t"); p:packInt(tid)
    p:packString("k"); p:packString("ann")
    p:packString("f"); p:packArrayHeader(1); p:packString("coveredText")
    p:packString("r"); p:packArrayHeader(#rows); for i = 1, #rows do p:packNil() end
    p:packString("b"); p:packArrayHeader(#rows)
    for i = 1, #rows do p:packInt(rows[i]:getBegin()) end
    p:packString("e"); p:packArrayHeader(#rows)
    for i = 1, #rows do p:packInt(rows[i]:getEnd()) end
    p:packString("c"); p:packArrayHeader(1); p:packArrayHeader(#rows)
    for i = 1, #rows do p:packString(rows[i]:getCoveredText() or "") end
    local out = p:toByteArray(); p:close()
    write_chunk(outputStream, CHUNK_COLUMN_BATCH, out, tid, #rows, 0)
end

function serialize(inputCas, outputStream, parameters, sourceView)
    local ok, err = pcall(function()
        write_start(outputStream, parameters, sourceView)
        local mime = "text/plain; charset=utf-8"
        if descriptor and descriptor.input and descriptor.input.text and descriptor.input.text.default and descriptor.input.text.default.mimeType then
            mime = descriptor.input.text.default.mimeType
        end
        local lang = inputCas:getDocumentLanguage() or "x-unspecified"
        write_sofa(outputStream, inputCas, mime, lang, false)
        for i = 1, #input_types do write_annotation_batch(outputStream, inputCas, input_types[i], parameters) end
        write_chunk(outputStream, CHUNK_END, "")
    end)
    if not ok then
        local p = MessagePack:newDefaultBufferPacker()
        p:packMapHeader(1); p:packString("message"); p:packString(tostring(err))
        local out = p:toByteArray(); p:close()
        write_chunk(outputStream, CHUNK_ERROR, out)
    end
end

local type_cache = {{}}
local feature_cache = {{}}
local generated_setters = {{}}
local generated_batch_appliers = {{}}
local generated_batch_direct_features = {{}}
local generated_setter_state = {{}}
local new_instance_state = {{}}
local index_state = {{}}

{generated_setters}

local function cached_type(ts, type_name)
    local cached = type_cache[type_name]
    if cached ~= nil then if cached == false then return nil end; return cached end
    cached = ts:getType(type_name)
    type_cache[type_name] = cached or false
    return cached
end

local function cached_feature(type_name, fs_type, feature_name)
    local by_type = feature_cache[type_name]
    if by_type == nil then by_type = {{}}; feature_cache[type_name] = by_type end
    local cached = by_type[feature_name]
    if cached ~= nil then if cached == false then return nil end; return cached end
    cached = fs_type:getFeatureByBaseName(feature_name)
    by_type[feature_name] = cached or false
    return cached
end

local function set_ref_feature(fs, feature, ref_id)
    if feature == nil or ref_id == nil then return end
    if fs_refs[ref_id] ~= nil then
        fs:setFeatureValue(feature, fs_refs[ref_id])
    else
        pending_refs[#pending_refs + 1] = {{ fs = fs, feature = feature, ref = ref_id }}
    end
end

local function set_feature_with_range(fs, feature, range_name, value)
    if feature == nil or value == nil then return end
    if type(value) == "string" and string.sub(value, 1, 5) == "$ref:" then
        set_ref_feature(fs, feature, tonumber(string.sub(value, 6)))
    elseif range_name == "uima.cas.String" then fs:setStringValue(feature, tostring(value))
    elseif range_name == "uima.cas.Byte" then fs:setByteValue(feature, value)
    elseif range_name == "uima.cas.Short" then fs:setShortValue(feature, value)
    elseif range_name == "uima.cas.Integer" then fs:setIntValue(feature, value)
    elseif range_name == "uima.cas.Long" then fs:setLongValue(feature, value)
    elseif range_name == "uima.cas.Float" then fs:setFloatValue(feature, value)
    elseif range_name == "uima.cas.Double" then fs:setDoubleValue(feature, value)
    elseif range_name == "uima.cas.Boolean" then fs:setBooleanValue(feature, value)
    end
end

local function set_feature(fs, feature, value)
    if feature == nil or value == nil then return end
    set_feature_with_range(fs, feature, feature:getRange():getName(), value)
end

local function feature_name(type_id_value, feature_id_value)
    if type(feature_id_value) == "string" then return feature_id_value end
    local by_type = response_features[type_id_value]
    if by_type ~= nil and type(feature_id_value) == "number" then return by_type[feature_id_value] end
    return tostring(feature_id_value)
end

local function make_feature_plan(type_id_value, type_name, fs_type, features)
    local out = {{}}
    for i = 1, #features do
        local name = feature_name(type_id_value, features[i])
        local feature = cached_feature(type_name, fs_type, name)
        if feature ~= nil then
            out[i] = {{ feature = feature, range = feature:getRange():getName() }}
        else
            out[i] = false
        end
    end
    return out
end

{generated_batch_appliers}

local function apply_one(inputCas, cas, ts, kind, type_id_value, ref, begin, finish, features, values)
    local type_name = response_types[type_id_value]
    if type_name == nil then error("unknown wire type id: " .. tostring(type_id_value)) end
    local fs_type = cached_type(ts, type_name)
    if fs_type == nil then error("unknown UIMA type: " .. tostring(type_name)) end
    local fs
    local direct_state = new_instance_state[type_name]
    if direct_state ~= false then
        if direct_state == true then
            fs = luajava.newInstance(type_name, inputCas)
        else
            local ok, created = pcall(function() return luajava.newInstance(type_name, inputCas) end)
            if ok then
                new_instance_state[type_name] = true
                fs = created
            else
                new_instance_state[type_name] = false
            end
        end
    end
    if fs ~= nil and kind == "ann" then
        fs:setBegin(begin or 0)
        fs:setEnd(finish or 0)
    elseif fs == nil and kind == "ann" then
        fs = cas:createAnnotation(fs_type, begin or 0, finish or 0)
    elseif fs == nil then
        fs = cas:createFS(fs_type)
    end
    local sofa_feature = cached_feature(type_name, fs_type, "sofa")
    if kind ~= "ann" and sofa_feature ~= nil then fs:setFeatureValue(sofa_feature, inputCas:getSofa()) end
    if ref ~= nil then fs_refs[ref] = fs end
    for i = 1, #features do
        local handled = false
        local setter = generated_setters[type_id_value]
        if setter ~= nil then
            handled = setter(fs, features[i], values[i])
        end
        if not handled then
            local name = feature_name(type_id_value, features[i])
            set_feature(fs, cached_feature(type_name, fs_type, name), values[i])
        end
    end
    local index_mode = index_state[type_name]
    if index_mode == true then
        fs:addToIndexes()
    elseif index_mode == false then
        cas:addFsToIndexes(fs)
    else
        local ok_index = pcall(function() fs:addToIndexes() end)
        index_state[type_name] = ok_index
        if not ok_index then cas:addFsToIndexes(fs) end
    end
end

local function apply_row_batch(inputCas, cas, ts, payload)
    local u = MessagePack:newDefaultUnpacker(payload)
    local size = u:unpackMapHeader()
    local tid, kind, features, rows = nil, "fs", {{}}, {{}}
    for _ = 1, size do
        local k = u:unpackString()
        if k == "t" then tid = u:unpackInt()
        elseif k == "k" then kind = u:unpackString()
        elseif k == "f" then features = read_feature_array(u)
        elseif k == "rows" then
            local row_count = u:unpackArrayHeader()
            rows = {{}}
            for i = 1, row_count do
                u:unpackArrayHeader()
                local ref = unpack_value(u)
                local begin = unpack_value(u)
                local finish = unpack_value(u)
                local values = read_value_array(u)
                rows[i] = {{ ref, begin, finish, values }}
            end
        else u:skipValue() end
    end
    u:close()
    for i = 1, #rows do apply_one(inputCas, cas, ts, kind, tid, rows[i][1], rows[i][2], rows[i][3], features, rows[i][4]) end
end

local function apply_column_batch(inputCas, cas, ts, payload, declared_row_count)
    local u = MessagePack:newDefaultUnpacker(payload)
    local size = u:unpackMapHeader()
    local tid, kind, features, refs, begins, ends, columns, sparse_columns, dictionary_columns = nil, "fs", {{}}, {{}}, {{}}, {{}}, {{}}, {{}}, {{}}
    local payload_row_count = 0
    for _ = 1, size do
        local k = u:unpackString()
        if k == "t" then tid = u:unpackInt()
        elseif k == "k" then kind = u:unpackString()
        elseif k == "n" then payload_row_count = u:unpackInt()
        elseif k == "f" then features = read_feature_array(u)
        elseif k == "r" then refs = read_long_array(u)
        elseif k == "b" then begins = read_int_array(u)
        elseif k == "e" then ends = read_int_array(u)
        elseif k == "bp" then begins = read_delta_packed_int_array(u)
        elseif k == "ep" then ends = read_delta_packed_int_array(u)
        elseif k == "c" then
            local col_count = u:unpackArrayHeader()
            columns = {{}}
            for i = 1, col_count do columns[i] = read_feature_value_array(u, tid, features[i]) end
        elseif k == "s" then
            local sparse_count = u:unpackArrayHeader()
            sparse_columns = {{}}
            for i = 1, sparse_count do
                u:unpackArrayHeader()
                local sparse_feature = unpack_value(u)
                local sparse_rows = read_int_array(u)
                local sparse_values = read_feature_value_array(u, tid, sparse_feature)
                sparse_columns[i] = {{ feature = sparse_feature, rows = sparse_rows, values = sparse_values }}
            end
        elseif k == "d" then
            local dictionary_count = u:unpackArrayHeader()
            dictionary_columns = {{}}
            for i = 1, dictionary_count do
                u:unpackArrayHeader()
                local dictionary_feature = unpack_value(u)
                local dictionary_values = read_string_array(u)
                local dictionary_ids = read_int_array(u)
                dictionary_columns[i] = {{ feature = dictionary_feature, values = dictionary_values, ids = dictionary_ids }}
            end
        else u:skipValue() end
    end
    u:close()
    for i = 1, #dictionary_columns do
        local dictionary_column = dictionary_columns[i]
        local decoded = {{}}
        for row = 1, #dictionary_column.ids do
            local dictionary_id = dictionary_column.ids[row]
            if dictionary_id ~= nil and dictionary_id > 0 then
                decoded[row] = dictionary_column.values[dictionary_id]
            end
        end
        features[#features + 1] = dictionary_column.feature
        columns[#columns + 1] = decoded
    end
    local type_name = response_types[tid]
    if type_name == nil then error("unknown wire type id: " .. tostring(tid)) end
    local fs_type = cached_type(ts, type_name)
    if fs_type == nil then error("unknown UIMA type: " .. tostring(type_name)) end
    local setter = generated_setters[tid]
    local sofa_feature = cached_feature(type_name, fs_type, "sofa")
    local batch_applier = generated_batch_appliers[tid]
    local can_use_batch_applier = batch_applier ~= nil and generated_batch_direct_features[tid] ~= nil
    if can_use_batch_applier then
        local direct_features = generated_batch_direct_features[tid]
        for i = 1, #features do
            if direct_features[features[i]] ~= true then can_use_batch_applier = false end
        end
        if can_use_batch_applier then
            for i = 1, #sparse_columns do
                if direct_features[sparse_columns[i].feature] ~= true then can_use_batch_applier = false end
            end
        end
    end
    if can_use_batch_applier then
        local row_count = declared_row_count or 0
        if row_count <= 0 then row_count = payload_row_count or 0 end
        if row_count <= 0 then row_count = batch_row_count(refs, begins, ends, columns, sparse_columns) end
        batch_applier(inputCas, cas, type_name, fs_type, kind, refs, begins, ends, features, columns, sparse_columns, sofa_feature, row_count)
        return
    end
    local sparse_by_row = {{}}
    for i = 1, #sparse_columns do
        local sparse = sparse_columns[i]
        for j = 1, #sparse.rows do
            local sparse_row = sparse.rows[j]
            if sparse_by_row[sparse_row] == nil then sparse_by_row[sparse_row] = {{}} end
            sparse_by_row[sparse_row][#sparse_by_row[sparse_row] + 1] = {{ feature = sparse.feature, value = sparse.values[j] }}
        end
    end
    local feature_plan = make_feature_plan(tid, type_name, fs_type, features)
    local index_mode = index_state[type_name]
    local row_count = declared_row_count or 0
    if row_count <= 0 then row_count = payload_row_count or 0 end
    if row_count <= 0 then row_count = batch_row_count(refs, begins, ends, columns, sparse_columns) end
    for row = 1, row_count do
        local fs
        local direct_state = new_instance_state[type_name]
        if direct_state ~= false then
            if direct_state == true then
                fs = luajava.newInstance(type_name, inputCas)
            else
                local ok, created = pcall(function() return luajava.newInstance(type_name, inputCas) end)
                if ok then
                    new_instance_state[type_name] = true
                    fs = created
                else
                    new_instance_state[type_name] = false
                end
            end
        end
        if fs ~= nil and kind == "ann" then
            fs:setBegin(begins[row] or 0)
            fs:setEnd(ends[row] or 0)
        elseif fs == nil and kind == "ann" then
            fs = cas:createAnnotation(fs_type, begins[row] or 0, ends[row] or 0)
        elseif fs == nil then
            fs = cas:createFS(fs_type)
        end
        if kind ~= "ann" and sofa_feature ~= nil then fs:setFeatureValue(sofa_feature, inputCas:getSofa()) end
        if refs[row] ~= nil then fs_refs[refs[row]] = fs end
        for col = 1, #features do
            local column = columns[col]
            local value = nil
            if column ~= nil then value = column[row] end
            if value ~= nil then
                local handled = false
                if setter ~= nil then handled = setter(fs, features[col], value) end
                if not handled then
                    local planned = feature_plan[col]
                    if planned then set_feature_with_range(fs, planned.feature, planned.range, value) end
                end
            end
        end
        local sparse_values = sparse_by_row[row]
        if sparse_values ~= nil then
            for sparse_index = 1, #sparse_values do
                local sparse_value = sparse_values[sparse_index]
                if sparse_value.value ~= nil then
                    local handled = false
                    if setter ~= nil then handled = setter(fs, sparse_value.feature, sparse_value.value) end
                    if not handled then
                        local name = feature_name(tid, sparse_value.feature)
                        set_feature(fs, cached_feature(type_name, fs_type, name), sparse_value.value)
                    end
                end
            end
        end
        if index_mode == true then
            fs:addToIndexes()
        elseif index_mode == false then
            cas:addFsToIndexes(fs)
        else
            local ok_index = pcall(function() fs:addToIndexes() end)
            index_state[type_name] = ok_index
            index_mode = ok_index
            if not ok_index then cas:addFsToIndexes(fs) end
        end
    end
end

local function apply_direct_batch(inputCas, cas, ts, payload, declared_row_count)
    local u = MessagePack:newDefaultUnpacker(payload)
    local payload_count = u:unpackArrayHeader()
    local tid = u:unpackInt()
    local kind_code = u:unpackInt()
    local kind = "fs"
    if kind_code == 1 then kind = "ann" end
    local refs = read_nullable_long_array(u)
    local begins = read_delta_packed_int_array(u)
    local ends = read_delta_packed_int_array(u)
    local features = read_int_array(u)
    local col_count = u:unpackArrayHeader()
    local columns = {{}}
    for i = 1, col_count do columns[i] = read_feature_value_array(u, tid, features[i]) end
    local sparse_columns = read_direct_sparse_columns(u, tid)
    local dictionary_columns = read_direct_dictionary_columns(u)
    local payload_row_count = 0
    if payload_count >= 10 then payload_row_count = u:unpackInt() end
    u:close()

    for i = 1, #dictionary_columns do
        local dictionary_column = dictionary_columns[i]
        local decoded = {{}}
        for row = 1, #dictionary_column.ids do
            local dictionary_id = dictionary_column.ids[row]
            if dictionary_id ~= nil and dictionary_id > 0 then
                decoded[row] = dictionary_column.values[dictionary_id]
            end
        end
        features[#features + 1] = dictionary_column.feature
        columns[#columns + 1] = decoded
    end

    local type_name = response_types[tid]
    if type_name == nil then error("unknown wire type id: " .. tostring(tid)) end
    local fs_type = cached_type(ts, type_name)
    if fs_type == nil then error("unknown UIMA type: " .. tostring(type_name)) end
    local batch_applier = generated_batch_appliers[tid]
    if batch_applier == nil then error("direct batch has no generated applier for: " .. tostring(type_name)) end
    local row_count = declared_row_count or 0
    if row_count <= 0 then row_count = payload_row_count or 0 end
    if row_count <= 0 then row_count = batch_row_count(refs, begins, ends, columns, sparse_columns) end
    batch_applier(
        inputCas,
        cas,
        type_name,
        fs_type,
        kind,
        refs,
        begins,
        ends,
        features,
        columns,
        sparse_columns,
        cached_feature(type_name, fs_type, "sofa"),
        row_count
    )
end

local function apply_direct_multi_batch(inputCas, cas, ts, payload)
    local u = MessagePack:newDefaultUnpacker(payload)
    local count = u:unpackArrayHeader()
    for i = 1, count do
        local size = u:unpackBinaryHeader()
        apply_direct_batch(inputCas, cas, ts, u:readPayload(size), 0)
    end
    u:close()
end

local function read_start(payload)
    response_types = manifest.types or {{}}
    response_features = manifest.features or {{}}
    response_ranges = manifest.ranges or {{}}
    if byte_len(payload) == 0 then return end
    local u = MessagePack:newDefaultUnpacker(payload)
    local size = u:unpackMapHeader()
    for _ = 1, size do
        local k = u:unpackString()
        if k == "types" then
            local type_count = u:unpackArrayHeader()
            response_types = {{}}
            for i = 1, type_count do response_types[i] = u:unpackString() end
        elseif k == "features" then
            local type_count = u:unpackArrayHeader()
            response_features = {{}}
            for i = 1, type_count do
                local feature_count = u:unpackArrayHeader()
                response_features[i] = {{}}
                for j = 1, feature_count do response_features[i][j] = u:unpackString() end
            end
        elseif k == "ranges" then
            local type_count = u:unpackArrayHeader()
            response_ranges = {{}}
            for i = 1, type_count do
                local feature_count = u:unpackArrayHeader()
                response_ranges[i] = {{}}
                for j = 1, feature_count do response_ranges[i][j] = u:unpackString() end
            end
        else u:skipValue() end
    end
    u:close()
end

function deserialize(inputCas, inputStream)
    fs_refs = {{}}
    pending_refs = {{}}
    local saw_start = false
    local cas = inputCas:getCas()
    local ts = cas:getTypeSystem()
    while true do
        local chunk, err = read_chunk(inputStream)
        if not chunk then
            if err == "eof" then error("missing END chunk") end
            error("malformed chunk stream: " .. tostring(err))
        end
        if chunk.type == CHUNK_START then
            if saw_start then error("duplicate START chunk") end
            saw_start = true
            read_start(chunk.payload)
        elseif chunk.type == CHUNK_SOFA then
            local u = MessagePack:newDefaultUnpacker(chunk.payload)
            local size = u:unpackMapHeader()
            local data, mime, lang = nil, nil, nil
            for _ = 1, size do
                local k = u:unpackString()
                if k == "data" then data = u:unpackString()
                elseif k == "mimeType" then mime = u:unpackString()
                elseif k == "language" then lang = u:unpackString()
                else u:skipValue() end
            end
            u:close()
            if data and mime then
                inputCas:setSofaDataString(data, mime)
                if lang and #lang > 0 then inputCas:setDocumentLanguage(lang) end
            end
        elseif chunk.type == CHUNK_ROW_BATCH then
            apply_row_batch(inputCas, cas, ts, chunk.payload)
        elseif chunk.type == CHUNK_COLUMN_BATCH then
            apply_column_batch(inputCas, cas, ts, chunk.payload, chunk.row_count)
        elseif chunk.type == CHUNK_COMPRESSED_BATCH then
            apply_column_batch(inputCas, cas, ts, inflate_bytes(chunk.payload), chunk.row_count)
        elseif chunk.type == CHUNK_DIRECT_BATCH then
            apply_direct_batch(inputCas, cas, ts, chunk.payload, chunk.row_count)
        elseif chunk.type == CHUNK_DIRECT_MULTI_BATCH then
            apply_direct_multi_batch(inputCas, cas, ts, chunk.payload)
        elseif chunk.type == CHUNK_ERROR then
            local message = "received ERROR chunk"
            if chunk.payload ~= nil then
                local ok, decoded = pcall(function()
                    local u = MessagePack:newDefaultUnpacker(chunk.payload)
                    local size = u:unpackMapHeader()
                    local parts = {{}}
                    for _ = 1, size do
                        local k = u:unpackString()
                        if k == "message" or k == "title" or k == "status" then
                            parts[#parts + 1] = tostring(k) .. "=" .. tostring(unpack_value(u))
                        else
                            u:skipValue()
                        end
                    end
                    u:close()
                    return table.concat(parts, "; ")
                end)
                if ok and decoded ~= nil and #decoded > 0 then message = message .. ": " .. decoded end
            end
            error(message)
        elseif chunk.type == CHUNK_END then
            for i = 1, #pending_refs do
                local p = pending_refs[i]
                if p.ref ~= nil and fs_refs[p.ref] ~= nil then p.fs:setFeatureValue(p.feature, fs_refs[p.ref]) end
            end
            return
        else
            error("unknown chunk type: " .. tostring(chunk.type))
        end
    end
end
"""


def lua_generated_setters(manifest: dict[str, Any]) -> str:
    """Generate Lua setter functions for each type's features."""
    import json as _json
    lines: list[str] = []
    types = manifest["types"]
    features_by_type = manifest["features"]
    for index, type_name in enumerate(types, start=1):
        features = features_by_type[index - 1] if index - 1 < len(features_by_type) else []
        if not features:
            continue
        lines.append(f"generated_setters[{index}] = function(fs, feature_id, value)")
        lines.append("    if value == nil then return true end")
        lines.append('    if type(value) == "string" and string.sub(value, 1, 5) == "$ref:" then return false end')
        first = True
        for feature_id, feature in enumerate(features, start=1):
            if not feature or feature in {"begin", "end", "type", "ref", "features"}:
                continue
            method = "set" + feature[:1].upper() + feature[1:]
            prefix = "if" if first else "elseif"
            first = False
            state_key = _json.dumps(f"{index}:{feature}")
            lines.append(f"    {prefix} feature_id == {feature_id} then")
            lines.append(f"        local state = generated_setter_state[{state_key}]")
            lines.append("        if state == false then return false end")
            lines.append(f"        if state == true then fs:{method}(value); return true end")
            lines.append(f"        local ok = pcall(function() fs:{method}(value) end)")
            lines.append(f"        generated_setter_state[{state_key}] = ok")
            lines.append("        return ok")
        lines.append("    end")
        lines.append("    return false")
        lines.append("end")
    return "\n".join(lines)


def lua_generated_batch_appliers(manifest: dict[str, Any]) -> str:
    """Generate Lua batch applier functions for each type."""
    import json as _json
    lines: list[str] = []
    types = manifest["types"]
    features_by_type = manifest["features"]
    ranges_by_type = manifest.get("ranges", [])
    primitive_ranges = {"string", "byte", "short", "integer", "long", "boolean", "float", "double"}
    for type_id, type_name in enumerate(types, start=1):
        features = features_by_type[type_id - 1] if type_id - 1 < len(features_by_type) else []
        ranges = ranges_by_type[type_id - 1] if type_id - 1 < len(ranges_by_type) else []
        direct_features: list[tuple[int, str, str]] = []
        for feature_id, feature in enumerate(features, start=1):
            if not feature or feature in {"begin", "end", "type", "ref", "features"}:
                continue
            feature_range = ranges[feature_id - 1] if feature_id - 1 < len(ranges) else "any"
            direct_features.append((feature_id, feature, feature_range))
        if not direct_features:
            continue
        lines.append(f"generated_batch_direct_features[{type_id}] = {{}}")
        for feature_id, _, _ in direct_features:
            lines.append(f"generated_batch_direct_features[{type_id}][{feature_id}] = true")
        lines.append(
            f"generated_batch_appliers[{type_id}] = function(inputCas, cas, type_name, fs_type, kind, refs, begins, ends, features, columns, sparse_columns, sofa_feature, row_count)"
        )
        for feature_id, _, _ in direct_features:
            lines.append(f"    local col_{feature_id} = nil")
        for feature_id, feature, _ in direct_features:
            escaped_feature = _json.dumps(feature)
            lines.append(f"    local feature_{feature_id} = cached_feature(type_name, fs_type, {escaped_feature})")
            lines.append(f"    local range_{feature_id} = nil")
            lines.append(f"    if feature_{feature_id} ~= nil then range_{feature_id} = feature_{feature_id}:getRange():getName() end")
        lines.append("    for col = 1, #features do")
        first = True
        for feature_id, _, _ in direct_features:
            prefix = "if" if first else "elseif"
            first = False
            lines.append(f"        {prefix} features[col] == {feature_id} then col_{feature_id} = columns[col]")
        lines.append("        end")
        lines.append("    end")
        lines.append("    local created = nil")
        lines.append("    if #sparse_columns > 0 then created = {} end")
        lines.append("    local index_mode = index_state[type_name]")
        lines.append("    for row = 1, row_count do")
        lines.append("        local fs")
        lines.append("        local direct_state = new_instance_state[type_name]")
        lines.append("        if direct_state ~= false then")
        lines.append("            if direct_state == true then")
        lines.append("                fs = luajava.newInstance(type_name, inputCas)")
        lines.append("            else")
        lines.append("                local ok, created = pcall(function() return luajava.newInstance(type_name, inputCas) end)")
        lines.append("                if ok then")
        lines.append("                    new_instance_state[type_name] = true")
        lines.append("                    fs = created")
        lines.append("                else")
        lines.append("                    new_instance_state[type_name] = false")
        lines.append("                end")
        lines.append("            end")
        lines.append("        end")
        lines.append('        if fs ~= nil and kind == "ann" then')
        lines.append("            fs:setBegin(begins[row] or 0)")
        lines.append("            fs:setEnd(ends[row] or 0)")
        lines.append('        elseif fs == nil and kind == "ann" then')
        lines.append("            fs = cas:createAnnotation(fs_type, begins[row] or 0, ends[row] or 0)")
        lines.append("        elseif fs == nil then")
        lines.append("            fs = cas:createFS(fs_type)")
        lines.append("        end")
        lines.append('        if kind ~= "ann" and sofa_feature ~= nil then fs:setFeatureValue(sofa_feature, inputCas:getSofa()) end')
        lines.append("        if refs[row] ~= nil then fs_refs[refs[row]] = fs end")
        lines.append("        if created ~= nil then created[row] = fs end")
        for feature_id, _, feature_range in direct_features:
            lines.append(f"        if col_{feature_id} ~= nil then")
            lines.append(f"            local value_{feature_id} = col_{feature_id}[row]")
            lines.append(f"            if value_{feature_id} ~= nil then")
            if feature_range in primitive_ranges:
                setter = _lua_cas_setter(feature_range)
                lines.append(f"                if feature_{feature_id} ~= nil then fs:{setter}(feature_{feature_id}, value_{feature_id}) end")
            else:
                lines.append(f"                if feature_{feature_id} ~= nil then")
                lines.append(f"                    local direct_ok = false")
                lines.append(f"                    if generated_setters[{type_id}] ~= nil then direct_ok = generated_setters[{type_id}](fs, {feature_id}, value_{feature_id}) end")
                lines.append(f"                    if not direct_ok then set_feature_with_range(fs, feature_{feature_id}, range_{feature_id}, value_{feature_id}) end")
                lines.append(f"                end")
            lines.append("            end")
            lines.append("        end")
        lines.append("        if index_mode == true then")
        lines.append("            fs:addToIndexes()")
        lines.append("        elseif index_mode == false then")
        lines.append("            cas:addFsToIndexes(fs)")
        lines.append("        else")
        lines.append("            local ok_index = pcall(function() fs:addToIndexes() end)")
        lines.append("            index_state[type_name] = ok_index")
        lines.append("            index_mode = ok_index")
        lines.append("            if not ok_index then cas:addFsToIndexes(fs) end")
        lines.append("        end")
        lines.append("    end")
        lines.append("    if created ~= nil then")
        lines.append("        for sparse_index = 1, #sparse_columns do")
        lines.append("            local sparse = sparse_columns[sparse_index]")
        first_sparse = True
        for feature_id, _, feature_range in direct_features:
            prefix = "if" if first_sparse else "elseif"
            first_sparse = False
            lines.append(f"            {prefix} sparse.feature == {feature_id} then")
            lines.append("                for j = 1, #sparse.rows do")
            lines.append("                    local fs = created[sparse.rows[j]]")
            lines.append("                    local value = sparse.values[j]")
            lines.append("                    if fs ~= nil and value ~= nil then")
            if feature_range in primitive_ranges:
                setter = _lua_cas_setter(feature_range)
                lines.append(f"                        if feature_{feature_id} ~= nil then fs:{setter}(feature_{feature_id}, value) end")
            else:
                lines.append(f"                        if feature_{feature_id} ~= nil then")
                lines.append(f"                            local direct_ok = false")
                lines.append(f"                            if generated_setters[{type_id}] ~= nil then direct_ok = generated_setters[{type_id}](fs, {feature_id}, value) end")
                lines.append(f"                            if not direct_ok then set_feature_with_range(fs, feature_{feature_id}, range_{feature_id}, value) end")
                lines.append(f"                        end")
            lines.append("                    end")
            lines.append("                end")
        lines.append("            end")
        lines.append("        end")
        lines.append("    end")
        lines.append("end")
    return "\n".join(lines)
