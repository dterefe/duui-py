"""Standalone utility functions for the MsgPack Lua codec."""

from __future__ import annotations

import struct
from typing import Any, cast

from duui_py.codecs.msgpack_lua.wire import WirePlan
from duui_py.models import DuuiResult, SoFa, SoFaAnnotationSpans, sofa_kind, sofa_to_wire_data
from duui_py.models.uima import Annotation, FeatureStructure, normalize_uima_value


# ── Varint encoding ──────────────────────────────────────────────────────────
# Variable-length integer encoding (unsigned). Each byte uses 7 bits for data,
# MSB signals continuation. Small values (<128) use 1 byte instead of 4.


def _varint_encode(value: int) -> bytes:
    """Encode a non-negative integer as unsigned varint."""
    buf = bytearray()
    while value >= 0x80:
        buf.append((value & 0x7F) | 0x80)
        value >>= 7
    buf.append(value & 0x7F)
    return bytes(buf)


def _varint_decode(data: bytes, offset: int = 0) -> tuple[int, int]:
    """Decode an unsigned varint from *data* starting at *offset*.
    Returns ``(value, bytes_consumed)``.
    """
    value = 0
    shift = 0
    i = offset
    while i < len(data):
        byte = data[i]
        value |= (byte & 0x7F) << shift
        shift += 7
        i += 1
        if not (byte & 0x80):
            return value, i - offset
    raise ValueError("truncated varint")


def _varint_encode_signed(value: int) -> bytes:
    """Encode a signed integer using ZigZag + unsigned varint."""
    return _varint_encode((value << 1) ^ (value >> 63))


def _varint_decode_signed(data: bytes, offset: int = 0) -> tuple[int, int]:
    """Decode a signed varint (ZigZag). Returns ``(value, bytes_consumed)``."""
    u, consumed = _varint_decode(data, offset)
    return (-(u & 1) ^ (u >> 1), consumed)


# ── Delta encoding for packed i32 columns ────────────────────────────────────


def _pack_i32_column_delta(values: list[int | None]) -> bytes:
    """Pack a column of int32 values using delta + varint encoding.

    None values are signalled by a 0x00 sentinel byte.
    Non-None values are encoded as zigzag(delta) + 1 via unsigned varint.
    Adding 1 avoids collision: zigzag(0) = 0 -> we store 1 -> b'\\x01'.
    """
    if not values:
        return b""
    out = bytearray()
    prev = 0
    for value in values:
        if value is None:
            out.append(0x00)  # sentinel for None
        else:
            delta = value - prev
            prev = value
            # zigzag + 1 so that delta=0 encodes as 1 -> b'\\x01' (not b'\\x00')
            zz = (delta << 1) ^ (delta >> 63)
            out.extend(_varint_encode(zz + 1))
    return bytes(out)


def _unpack_i32_column_delta(data: bytes) -> list[int | None]:
    """Reverse of :func:`_pack_i32_column_delta`."""
    if not data:
        return []
    out: list[int | None] = []
    offset = 0
    prev = 0
    while offset < len(data):
        if data[offset] == 0x00:
            out.append(None)
            offset += 1
        else:
            zz_plus_1, consumed = _varint_decode(data, offset)
            zz = zz_plus_1 - 1
            delta = (-(zz & 1)) ^ (zz >> 1)
            prev += delta
            out.append(prev)
            offset += consumed
    return out


# ── Varint-based chunk length encoding ───────────────────────────────────────


def _encode_chunk_length(length: int) -> bytes:
    """Encode a payload length as varint instead of fixed 4-byte big-endian.

    For the common case of payloads < 16 KB this saves 2-3 bytes per chunk.
    """
    return _varint_encode(length)


def _decode_chunk_length(data: bytes, offset: int = 0) -> tuple[int, int]:
    """Decode a varint-encoded chunk length.

    Returns ``(length, bytes_consumed)``.
    """
    return _varint_decode(data, offset)


# ── Original helpers preserved for backward compatibility ────────────────────


def _feature_union(plan: WirePlan, items: list[FeatureStructure]) -> list[str]:
    return _feature_union_from_maps([item.feature_map() for item in items])


def _is_feature_structure_like(item: Any) -> bool:
    return (
        isinstance(getattr(item, "type", None), str)
        and callable(getattr(item, "feature_map", None))
        and hasattr(item, "ref")
    )


def _wire_item_kind(item: Any) -> str:
    if isinstance(item, Annotation) or bool(getattr(item, "__duui_annotation__", False)):
        return "ann"
    return "fs"


def _feature_union_from_maps(feature_maps: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for fmap in feature_maps:
        for name, value in fmap.items():
            if value is not None and name not in seen:
                seen.add(name)
                out.append(name)
    return out


def _should_sparse_column(values: list[Any]) -> bool:
    if len(values) < 8:
        return False
    present = sum(1 for value in values if value is not None)
    if present == 0:
        return True
    return present * 4 <= len(values) * 3


def _should_dictionary_column(values: list[Any]) -> bool:
    if len(values) < 16:
        return False
    non_null = sum(1 for value in values if value is not None)
    present_values = [
        value
        for value in values
        if isinstance(value, str) and not value.startswith("$ref:")
    ]
    present = len(present_values)
    if present != non_null:
        return False
    if present < 8 or present * 4 <= len(values) * 3:
        return False
    unique_values = list(dict.fromkeys(present_values))
    if len(unique_values) >= present:
        return False
    raw_bytes = sum(len(value.encode("utf-8")) + 1 for value in present_values)
    dictionary_bytes = sum(len(value.encode("utf-8")) + 1 for value in unique_values)
    id_bytes = len(values) * (1 if len(unique_values) <= 127 else 3)
    return len(unique_values) * 5 <= present * 4 and dictionary_bytes + id_bytes + 8 < raw_bytes


def _dictionary_column(values: list[Any]) -> tuple[list[str], list[int]]:
    dictionary: list[str] = []
    by_value: dict[str, int] = {}
    ids: list[int] = []
    for value in values:
        if isinstance(value, str) and not value.startswith("$ref:"):
            dictionary_id = by_value.get(value)
            if dictionary_id is None:
                dictionary.append(value)
                dictionary_id = len(dictionary)
                by_value[value] = dictionary_id
            ids.append(dictionary_id)
        else:
            ids.append(0)
    return dictionary, ids


def _lua_cas_setter(feature_range: str) -> str:
    return {
        "string": "setStringValue",
        "byte": "setByteValue",
        "short": "setShortValue",
        "integer": "setIntValue",
        "long": "setLongValue",
        "float": "setFloatValue",
        "double": "setDoubleValue",
        "boolean": "setBooleanValue",
    }.get(feature_range, "setFeatureValue")


def _wire_value(value: Any) -> Any:
    normalized = normalize_uima_value(value)
    if isinstance(normalized, dict) and set(normalized.keys()) == {"$ref"}:
        return f"$ref:{int(normalized['$ref'])}"
    if isinstance(normalized, list):
        return [_wire_value(item) for item in normalized]
    if isinstance(normalized, dict):
        return {str(key): _wire_value(item) for key, item in normalized.items()}
    return normalized


def _wire_feature_value(value: Any) -> Any:
    normalized = normalize_uima_value(value)
    if isinstance(normalized, dict) and set(normalized.keys()) == {"$ref"}:
        return f"$ref:{int(normalized['$ref'])}"
    if isinstance(normalized, (str, int, float, bool)):
        return normalized
    return None


def _feature_ref_ids(value: Any) -> list[int]:
    normalized = normalize_uima_value(value)
    if isinstance(normalized, dict):
        if set(normalized.keys()) == {"$ref"}:
            return [int(normalized["$ref"])]
        out: list[int] = []
        for item in normalized.values():
            out.extend(_feature_ref_ids(item))
        return out
    if isinstance(normalized, list):
        out: list[int] = []
        for item in normalized:
            out.extend(_feature_ref_ids(item))
        return out
    return []


def _from_wire_value(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("$ref:"):
        return {"$ref": int(value[5:])}
    return normalize_uima_value(value)


def _pack_i32_column(values: list[int | None]) -> bytes:
    out = bytearray()
    for value in values:
        out.extend(struct.pack(">i", int(value) if value is not None else -1))
    return bytes(out)


def _unpack_i32_column(values: bytes) -> list[int | None]:
    out: list[int | None] = []
    for offset in range(0, len(values), 4):
        if offset + 4 > len(values):
            break
        value = struct.unpack(">i", values[offset:offset + 4])[0]
        out.append(None if value == -1 else value)
    return out


def _input_types(descriptor: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []

    def add(value: Any) -> None:
        if isinstance(value, str) and value and value not in seen:
            seen.add(value)
            out.append(value)

    for type_list in descriptor.input.types.values():
        for type_name in type_list:
            add(type_name)
    for domain in ("text", "bytes", "uri", "annotation"):
        spec = getattr(descriptor.input, domain, None)
        if spec is None:
            continue
        for _, alternative in spec.iter_alternatives():
            for type_list in alternative.types.values():
                for type_name in type_list:
                    add(type_name)
    return out


def _type_name(type_names: list[str], value: Any) -> str:
    if isinstance(value, int) and 1 <= value <= len(type_names):
        return type_names[value - 1]
    if isinstance(value, str):
        return value
    raise ValueError(f"unknown wire type id: {value!r}")


def _feature_names_from_ids(features_by_type: list[list[str]], type_id_value: Any, raw_features: Any) -> list[str]:
    if not isinstance(raw_features, list):
        return []
    if isinstance(type_id_value, int) and 1 <= type_id_value <= len(features_by_type):
        table = features_by_type[type_id_value - 1]
        names: list[str] = []
        for value in raw_features:
            if isinstance(value, int) and 1 <= value <= len(table):
                names.append(table[value - 1])
            elif isinstance(value, str):
                names.append(value)
            else:
                names.append(str(value))
        return names
    return [str(value) for value in raw_features]


def _fs_from_parts(kind: str, type_name: str, ref: Any, begin: Any, end: Any, features: dict[str, Any]) -> FeatureStructure:
    if kind == "ann":
        return Annotation(type=type_name, begin=int(begin or 0), end=int(end or 0), ref=cast(int | None, ref), features=features)
    return FeatureStructure(type=type_name, begin=cast(int | None, begin), end=cast(int | None, end), ref=cast(int | None, ref), features=features)


def _get(values: Any, index: int) -> Any:
    if isinstance(values, list) and index < len(values):
        return values[index]
    return None
