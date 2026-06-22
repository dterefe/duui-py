from __future__ import annotations

import hashlib
import json
import struct
import time
import zlib
from collections.abc import AsyncIterable, AsyncIterator, Iterable
from typing import Any, cast

import msgpack

from duui_py.codecs.base import Codec
from duui_py.codecs.profiling import current_wire_profile, timed_profile_field
from duui_py.codecs.msgpack_lua.wire import WirePlan
from duui_py.codecs.msgpack_lua._helpers import (
    _dictionary_column,
    _feature_names_from_ids,
    _feature_ref_ids,
    _feature_union_from_maps,
    _from_wire_value,
    _fs_from_parts,
    _get,
    _input_types,
    _is_feature_structure_like,
    _pack_i32_column,
    _pack_i32_column_delta,
    _should_dictionary_column,
    _should_sparse_column,
    _type_name,
    _unpack_i32_column,
    _unpack_i32_column_delta,
    _varint_encode,
    _wire_feature_value,
    _wire_item_kind,
)
from duui_py.codecs.msgpack_lua._luascript import (
    generate_lua_script,
    lua_generated_batch_appliers,
    lua_generated_setters,
)

# Optional zstandard support
try:
    import zstandard as _zstd
    _HAS_ZSTD = True
except ImportError:
    _HAS_ZSTD = False
from duui_py.models import (
    AnnotatorConfig,
    V1RequestEnvelope,
    DuuiError,
    DuuiResult,
    SoFa,
    SoFaAnnotationSpans,
    sofa_annotation_type,
    sofa_default_for_mime,
    sofa_from_wire,
    sofa_kind,
    sofa_to_wire_data,
)
from duui_py.models.uima import (
    Annotation,
    FeatureStructure,
    SoFaBase,
    normalize_uima_value,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.types import (
    AnnotatorMetaData,
    DocumentModification,
)

CHUNK_START = 0x01
CHUNK_SOFA = 0x02
CHUNK_ANNOTATION = 0x03
CHUNK_FEATURE_STRUCTURE = 0x04
CHUNK_END = 0x05
CHUNK_ERROR = 0x06
CHUNK_ROW_BATCH = 0x10
CHUNK_COLUMN_BATCH = 0x11
CHUNK_COMPRESSED_BATCH = 0x12
CHUNK_DIRECT_BATCH = 0x13
CHUNK_DIRECT_MULTI_BATCH = 0x14

Chunk = tuple[int, bytes] | tuple[int, bytes, int, int, int]


class MsgPackLuaCodec(Codec[V1RequestEnvelope, DuuiResult]):
    """Descriptor-generated Lua transport with batched generic UIMA payloads."""

    name = "msgpack-lua"
    request_media_type = "application/x-msgpack"
    response_media_type = "application/x-msgpack"

    # Lua script cache
    _lua_script_cache: dict[str, str] = {}
    _compressor_cache: dict[str, Any] = {}
    _decompressor_cache: dict[str, Any] = {}

    def __init__(self, config: AnnotatorConfig):
        self.config = config
        self.descriptor = config.descriptor
        self.plan = WirePlan.from_config(config)
        # Adaptive batch sizing
        self._adaptive_max_rows: int | None = None
        self._adaptive_max_bytes: int | None = None

    # ── Zstandard helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _zstd_compress(data: bytes, level: int = 1) -> bytes:
        if "zstd" not in MsgPackLuaCodec._compressor_cache:
            if not _HAS_ZSTD:
                raise RuntimeError("zstandard package not installed; use 'pip install zstandard'")
            MsgPackLuaCodec._compressor_cache["zstd"] = _zstd.ZstdCompressor(level=level)
        return MsgPackLuaCodec._compressor_cache["zstd"].compress(data)

    @staticmethod
    def _zstd_decompress(data: bytes) -> bytes:
        if "zstd" not in MsgPackLuaCodec._decompressor_cache:
            if not _HAS_ZSTD:
                raise RuntimeError("zstandard package not installed; use 'pip install zstandard'")
            MsgPackLuaCodec._decompressor_cache["zstd"] = _zstd.ZstdDecompressor()
        return MsgPackLuaCodec._decompressor_cache["zstd"].decompress(data)

    @staticmethod
    def _compress_payload(data: bytes, compression: str, level: int = 1) -> bytes:
        if compression == "zstd":
            return MsgPackLuaCodec._zstd_compress(data, level=level)
        # zlib fallback
        return zlib.compress(data, level=level)

    @staticmethod
    def _decompress_payload(data: bytes, compression: str) -> bytes:
        if compression == "zstd":
            return MsgPackLuaCodec._zstd_decompress(data)
        # zlib fallback
        return zlib.decompress(data)

    def _default_input_mime(self) -> str:
        resolved = self.descriptor.input.first_available()
        return resolved.mimeType if resolved and resolved.mimeType else "text/plain; charset=utf-8"

    def _default_input_language(self) -> str:
        resolved = self.descriptor.input.first_available()
        if resolved and resolved.languages:
            return resolved.languages[0]
        return "x-unspecified"

    def communication_layer_content(self) -> dict[str, str | int]:
        script = self._generate_lua_script()
        return {
            "kind": "custom",
            "format": "lua",
            "version": 2,
            "spec": script,
        }

    def decode_request(self, body: bytes) -> V1RequestEnvelope:
        return self._decode_chunks(self._parse_chunked_stream(body))

    async def decode_request_stream(
        self,
        body: AsyncIterable[bytes],
        *,
        max_partial_buffer_bytes: int = 64 * 1024 * 1024,
        max_chunk_payload_bytes: int | None = None,
    ) -> V1RequestEnvelope:
        chunks = self._iter_chunked_stream(
            body,
            max_partial_buffer_bytes=max_partial_buffer_bytes,
            max_chunk_payload_bytes=max_chunk_payload_bytes,
        )
        return await self._decode_async_chunks(chunks)

    def encode_response(self, result: DuuiResult) -> bytes:
        items = self._result_items(result)
        self._ensure_manifest_items(items)
        chunks: list[Chunk] = [(CHUNK_START, self._start_payload())]
        chunks.extend(self._sofa_chunks(result.sofa) if result.sofa is not None else [])
        chunks.extend(self._batch_chunks(items, windowed=False))
        chunks.extend(self._error_chunks(result.errors))
        chunks.append((CHUNK_END, b""))
        return self._serialize_chunks(chunks)

    async def encode_response_stream(self, results: AsyncIterable[Any]) -> AsyncIterator[bytes]:
        yield self._serialize_chunk(CHUNK_START, self._start_payload())
        pending: list[FeatureStructure] = []
        pending_bytes = 0
        async for item in results:
            for output in self._output_items(item):
                if isinstance(output, SoFaBase):
                    for chunk in self._sofa_chunks(output):
                        yield self._serialize_chunk(*chunk)
                elif isinstance(output, (Annotation, FeatureStructure)) or _is_feature_structure_like(output):
                    pending.append(output)
                    pending_bytes += self._estimate_item_bytes(output)
                    if self._should_flush(pending, pending_bytes):
                        for chunk in self._batch_chunks(pending, windowed=True):
                            yield self._serialize_chunk(*chunk)
                        pending.clear()
                        pending_bytes = 0
                elif isinstance(output, DuuiError) or isinstance(output, str):
                    for chunk in self._error_chunks([output]):
                        yield self._serialize_chunk(*chunk)
        if pending:
            for chunk in self._batch_chunks(pending, windowed=True):
                yield self._serialize_chunk(*chunk)
        yield self._serialize_chunk(CHUNK_END, b"")

    def _decode_chunks(self, chunks: Iterable[tuple[int, bytes]]) -> V1RequestEnvelope:
        return self._decode_chunk_iter(iter(chunks))

    async def _decode_async_chunks(self, chunks: AsyncIterable[tuple[int, bytes]]) -> V1RequestEnvelope:
        seen_start = False
        saw_end = False
        parameters: dict[str, Any] = {}
        view = ""
        type_names: list[str] = []
        features_by_type: list[list[str]] = []
        sofa_payload: SoFa | None = None
        fs_items: list[FeatureStructure] = []

        def set_sofa(value: SoFa) -> None:
            nonlocal sofa_payload
            sofa_payload = value

        async for chunk_type, payload in chunks:
            if saw_end:
                raise ValueError("END chunk may only appear at stream end")
            if chunk_type == CHUNK_START:
                if seen_start:
                    raise ValueError("START chunk may only appear at stream beginning")
                seen_start = True
                parameters, view, type_names, features_by_type = self._decode_start_payload(payload)
                continue
            if not seen_start:
                raise ValueError("first chunk must be START")
            if chunk_type == CHUNK_END:
                if payload:
                    raise ValueError("END chunk must not contain payload")
                saw_end = True
                continue
            self._decode_data_chunk(chunk_type, payload, type_names, features_by_type, fs_items, set_sofa)

        if not seen_start:
            raise ValueError("empty chunk stream")
        if not saw_end:
            raise ValueError("chunk stream must end with END")
        return self._request_from_parts(parameters, view, sofa_payload, fs_items)

    def _decode_chunk_iter(self, chunks: Iterable[tuple[int, bytes]]) -> V1RequestEnvelope:
        seen_start = False
        saw_end = False
        parameters: dict[str, Any] = {}
        view = ""
        type_names: list[str] = []
        features_by_type: list[list[str]] = []
        sofa_payload: SoFa | None = None
        fs_items: list[FeatureStructure] = []

        def set_sofa(value: SoFa) -> None:
            nonlocal sofa_payload
            sofa_payload = value

        for index, (chunk_type, payload) in enumerate(chunks):
            if saw_end:
                raise ValueError("END chunk may only appear at stream end")
            if chunk_type == CHUNK_START:
                if index != 0 or seen_start:
                    raise ValueError("START chunk may only appear at stream beginning")
                seen_start = True
                parameters, view, type_names, features_by_type = self._decode_start_payload(payload)
                continue
            if not seen_start:
                raise ValueError("first chunk must be START")
            if chunk_type == CHUNK_END:
                if payload:
                    raise ValueError("END chunk must not contain payload")
                saw_end = True
                continue
            self._decode_data_chunk(chunk_type, payload, type_names, features_by_type, fs_items, set_sofa)

        if not seen_start:
            raise ValueError("empty chunk stream")
        if not saw_end:
            raise ValueError("chunk stream must end with END")
        return self._request_from_parts(parameters, view, sofa_payload, fs_items)

    def _decode_data_chunk(
        self,
        chunk_type: int,
        payload: bytes,
        type_names: list[str],
        features_by_type: list[list[str]],
        fs_items: list[FeatureStructure],
        set_sofa: Any,
    ) -> None:
        started = time.perf_counter()
        payload_len = len(payload)
        try:
            if chunk_type == CHUNK_ERROR:
                raise ValueError(self._decode_error_payload(payload))
            if chunk_type == CHUNK_SOFA:
                set_sofa(self._decode_sofa_payload(payload))
                return
            if chunk_type == CHUNK_ANNOTATION or chunk_type == CHUNK_FEATURE_STRUCTURE:
                fs_items.append(self._decode_legacy_feature_structure(payload))
                return
            if chunk_type == CHUNK_COMPRESSED_BATCH:
                payload = self._decompress_payload(payload, self.plan.compression)
                chunk_type = CHUNK_COLUMN_BATCH
            if chunk_type == CHUNK_ROW_BATCH:
                fs_items.extend(self._decode_row_batch(payload, type_names, features_by_type))
                return
            if chunk_type == CHUNK_COLUMN_BATCH:
                fs_items.extend(self._decode_column_batch(payload, type_names, features_by_type))
                return
            raise ValueError(f"unknown chunk type: 0x{chunk_type:02X}")
        finally:
            profile = current_wire_profile()
            if profile is not None:
                profile.set_plan(protocol=self.plan.protocol, compression=self.plan.compression)
                profile.add_decoded_chunk(payload_len, (time.perf_counter() - started) * 1000.0)

    def _request_from_parts(
        self,
        parameters: dict[str, Any],
        view: str,
        sofa_payload: SoFa | None,
        fs_items: list[FeatureStructure],
    ) -> V1RequestEnvelope:
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

    def _result_items(self, result: DuuiResult) -> list[Any]:
        out: list[Any] = []
        out.extend(result.feature_structures)
        out.extend(result.annotations)
        if result.meta is not None:
            out.append(result.meta)
        if result.modification_meta is not None:
            out.append(result.modification_meta)
        return out

    def _output_items(self, item: Any) -> list[Any]:
        if isinstance(item, DuuiResult):
            out: list[Any] = []
            if item.sofa is not None:
                out.append(item.sofa)
            out.extend(self._result_items(item))
            out.extend(item.errors)
            return out
        if isinstance(item, (list, tuple)):
            out: list[Any] = []
            for value in item:
                out.extend(self._output_items(value))
            return out
        if isinstance(item, (SoFaBase, Annotation, FeatureStructure, DuuiError, str)):
            return [item]
        if _is_feature_structure_like(item):
            return [item]
        raise TypeError(f"unsupported output chunk item: {type(item).__name__}")

    def _batch_chunks(self, items: list[Any], *, windowed: bool) -> list[Chunk]:
        if not items:
            return []
        grouped: dict[tuple[str, str], list[Any]] = {}
        for item in items:
            kind = _wire_item_kind(item)
            grouped.setdefault((kind, item.type), []).append(item)
        referenced_refs: set[int] = set()
        for item in items:
            referenced_refs.update(_feature_ref_ids(item.feature_map()))
        ordered_groups = self._dependency_ordered_groups(grouped)
        columnar = self.plan.columnar
        chunks: list[Chunk] = []
        direct_payload_bytes = 0

        def flush_direct(payloads: list[tuple[int, int, bytes]]) -> None:
            nonlocal direct_payload_bytes
            if not payloads:
                return
            row_count = sum(row_count for _, row_count, _ in payloads)
            if len(payloads) == 1:
                type_id, rows, payload = payloads[0]
                chunks.append((CHUNK_DIRECT_BATCH, payload, type_id, rows, 0))
                direct_payload_bytes = 0
                return
            with timed_profile_field("pack_msgpack_ms"):
                payload = msgpack.packb([item[2] for item in payloads], use_bin_type=True)
            profile = current_wire_profile()
            if profile is not None:
                profile.direct_batches += len(payloads) - 1
            chunks.append((CHUNK_DIRECT_MULTI_BATCH, payload, 0, row_count, 0))
            direct_payload_bytes = 0

        direct_payloads: list[tuple[int, int, bytes]] = []
        for kind, type_name, group in ordered_groups:
            for window in self._group_windows(type_name, group):
                if self.plan.protocol == "runtime-msgpack-direct" and self._can_direct_batch(type_name, window):
                    payload = self._direct_batch_payload(kind, type_name, window, referenced_refs)
                    if direct_payloads and direct_payload_bytes + len(payload) > self.plan.max_bytes:
                        flush_direct(direct_payloads)
                        direct_payloads = []
                    direct_payloads.append((
                        self.plan.type_id(type_name),
                        len(window),
                        payload,
                    ))
                    direct_payload_bytes += len(payload)
                    continue
                flush_direct(direct_payloads)
                direct_payloads = []
                if columnar:
                    payload = self._column_batch_payload(kind, type_name, window, referenced_refs)
                    type_id = self.plan.type_id(type_name)
                    if self.plan.compressed:
                        with timed_profile_field("compress_ms"):
                            payload = self._compress_payload(payload, self.plan.compression, level=1)
                        chunks.append((CHUNK_COMPRESSED_BATCH, payload, type_id, len(window), 0))
                    else:
                        chunks.append((CHUNK_COLUMN_BATCH, payload, type_id, len(window), 0))
                else:
                    chunks.append((CHUNK_ROW_BATCH, self._row_batch_payload(kind, type_name, window), self.plan.type_id(type_name), len(window), 0))
        flush_direct(direct_payloads)
        return chunks

    def _group_windows(self, type_name: str, group: list[Any]) -> list[list[Any]]:
        if not group:
            return []
        max_rows = max(1, self.plan.max_rows)
        max_bytes = max(1024, self.plan.max_bytes)
        windows: list[list[Any]] = []
        current: list[Any] = []
        current_bytes = 0
        for item in group:
            item_bytes = self._estimate_item_bytes(item)
            if current and (len(current) >= max_rows or current_bytes + item_bytes > max_bytes):
                windows.append(current)
                current = []
                current_bytes = 0
            current.append(item)
            current_bytes += item_bytes
        if current:
            windows.append(current)
        return windows

    def _dependency_ordered_groups(
        self, grouped: dict[tuple[str, str], list[Any]]
    ) -> list[tuple[str, str, list[Any]]]:
        groups = [(key[0], key[1], value) for key, value in grouped.items()]
        if len(groups) < 2:
            return groups
        ref_owner: dict[int, int] = {}
        for group_index, (_, _, group) in enumerate(groups):
            for item in group:
                ref = getattr(item, "ref", None)
                if isinstance(ref, int):
                    ref_owner[ref] = group_index
        deps: dict[int, set[int]] = {index: set() for index in range(len(groups))}
        for group_index, (_, _, group) in enumerate(groups):
            for item in group:
                for ref_id in _feature_ref_ids(item.feature_map()):
                    owner = ref_owner.get(ref_id)
                    if owner is not None and owner != group_index:
                        deps[group_index].add(owner)
        ordered: list[int] = []
        visiting: set[int] = set()
        visited: set[int] = set()

        def visit(index: int) -> None:
            if index in visited:
                return
            if index in visiting:
                return
            visiting.add(index)
            for dependency in sorted(deps[index]):
                visit(dependency)
            visiting.remove(index)
            visited.add(index)
            ordered.append(index)

        for index in range(len(groups)):
            visit(index)
        return [groups[index] for index in ordered]

    def _ensure_manifest_items(self, items: list[Any]) -> None:
        for item in items:
            self.plan.type_id(item.type)
            planned = self.plan.features.setdefault(item.type, [])
            seen = set(planned)
            for name, value in item.feature_map().items():
                if self.plan.runtime and name not in seen:
                    continue
                if _wire_feature_value(value) is not None and name not in seen:
                    planned.append(name)
                    self.plan.ranges.setdefault(item.type, {})[name] = "any"
                    seen.add(name)

    def _row_batch_payload(self, kind: str, type_name: str, items: list[Any]) -> bytes:
        with timed_profile_field("build_batch_ms"):
            feature_maps = self._wire_feature_maps(type_name, items)
            features = _feature_union_from_maps(feature_maps)
            feature_ids = [self._feature_id(type_name, name) for name in features]
            rows = []
            for item, fmap in zip(items, feature_maps):
                rows.append([
                    item.ref,
                    item.begin,
                    item.end,
                    [fmap.get(name) for name in features],
                ])
            profile = current_wire_profile()
            if profile is not None:
                profile.set_plan(protocol=self.plan.protocol, compression=self.plan.compression)
                profile.rows += len(items)
                profile.feature_columns += len(features)
            payload = {"t": self.plan.type_id(type_name), "k": kind, "f": feature_ids, "rows": rows}
        with timed_profile_field("pack_msgpack_ms"):
            return msgpack.packb(payload, use_bin_type=True)

    def _can_direct_batch(self, type_name: str, items: list[Any]) -> bool:
        if type_name not in self.plan.type_ids:
            return False
        allowed = set(self.plan.features.get(type_name, []))
        if not allowed:
            return False
        for item in items:
            for name, value in item.feature_map().items():
                if _wire_feature_value(value) is not None and name not in allowed:
                    return False
        return True

    def _direct_batch_payload(
        self,
        kind: str,
        type_name: str,
        items: list[Any],
        referenced_refs: set[int],
    ) -> bytes:
        with timed_profile_field("build_batch_ms"):
            feature_maps = self._wire_feature_maps(type_name, items)
            features = _feature_union_from_maps(feature_maps)
            dense_feature_ids = []
            dense_columns = []
            sparse_columns = []
            dictionary_columns = []
            for name in features:
                feature_id = self._feature_id(type_name, name)
                values = [fmap.get(name) for fmap in feature_maps]
                if _should_dictionary_column(values):
                    dictionary, ids = _dictionary_column(values)
                    dictionary_columns.append([feature_id, dictionary, ids])
                elif _should_sparse_column(values):
                    present_rows = []
                    present_values = []
                    for row_index, value in enumerate(values, start=1):
                        if value is not None:
                            present_rows.append(row_index)
                            present_values.append(value)
                    sparse_columns.append([feature_id, present_rows, present_values])
                else:
                    dense_feature_ids.append(feature_id)
                    dense_columns.append(values)
            refs = [item.ref for item in items]
            include_refs = any(isinstance(ref, int) and ref in referenced_refs for ref in refs)
            payload = [
                self.plan.type_id(type_name),
                1 if kind == "ann" else 0,
                refs if include_refs else None,
                _pack_i32_column_delta([item.begin for item in items]),
                _pack_i32_column_delta([item.end for item in items]),
                dense_feature_ids,
                dense_columns,
                sparse_columns if sparse_columns else None,
                dictionary_columns if dictionary_columns else None,
                len(items),
            ]
            profile = current_wire_profile()
            if profile is not None:
                profile.set_plan(protocol=self.plan.protocol, compression=self.plan.compression)
                profile.rows += len(items)
                profile.feature_columns += len(features)
        with timed_profile_field("pack_msgpack_ms"):
            return msgpack.packb(payload, use_bin_type=True)

    def _column_batch_payload(
        self,
        kind: str,
        type_name: str,
        items: list[Any],
        referenced_refs: set[int],
    ) -> bytes:
        with timed_profile_field("build_batch_ms"):
            feature_maps = self._wire_feature_maps(type_name, items)
            features = _feature_union_from_maps(feature_maps)
            dense_feature_ids = []
            dense_columns = []
            sparse_columns = []
            dictionary_columns = []
            for name in features:
                feature_id = self._feature_id(type_name, name)
                values = [fmap.get(name) for fmap in feature_maps]
                if self.plan.runtime and _should_dictionary_column(values):
                    dictionary, ids = _dictionary_column(values)
                    dictionary_columns.append([feature_id, dictionary, ids])
                elif self.plan.runtime and _should_sparse_column(values):
                    present_rows = []
                    present_values = []
                    for row_index, value in enumerate(values, start=1):
                        if value is not None:
                            present_rows.append(row_index)
                            present_values.append(value)
                    sparse_columns.append([feature_id, present_rows, present_values])
                else:
                    dense_feature_ids.append(feature_id)
                    dense_columns.append(values)
            payload: dict[str, Any] = {
                "t": self.plan.type_id(type_name),
                "k": kind,
                "n": len(items),
                "f": dense_feature_ids,
                "c": dense_columns,
            }
            if sparse_columns:
                payload["s"] = sparse_columns
            if dictionary_columns:
                payload["d"] = dictionary_columns
            begins = [item.begin for item in items]
            ends = [item.end for item in items]
            if self.plan.protocol == "runtime-msgpack-packed":
                # Delta encoding for packed begin/end (~50% reduction for sequential offsets)
                payload["bp"] = _pack_i32_column_delta(begins)
                payload["ep"] = _pack_i32_column_delta(ends)
            else:
                payload["b"] = begins
                payload["e"] = ends
            refs = [item.ref for item in items]
            include_refs = any(isinstance(ref, int) and ref in referenced_refs for ref in refs)
            if include_refs:
                payload["r"] = refs
            profile = current_wire_profile()
            if profile is not None:
                profile.set_plan(protocol=self.plan.protocol, compression=self.plan.compression)
                profile.rows += len(items)
                profile.feature_columns += len(features)
        with timed_profile_field("pack_msgpack_ms"):
            return msgpack.packb(payload, use_bin_type=True)

    def _feature_id(self, type_name: str, feature_name: str) -> int:
        features = self.plan.features.setdefault(type_name, [])
        if feature_name not in features:
            features.append(feature_name)
            self.plan.ranges.setdefault(type_name, {})[feature_name] = "any"
        return features.index(feature_name) + 1

    def _wire_feature_maps(self, type_name: str, items: list[Any]) -> list[dict[str, Any]]:
        allowed = set(self.plan.features.get(type_name, []))
        descriptor_limited = self.plan.runtime and bool(allowed)
        maps: list[dict[str, Any]] = []
        for item in items:
            wire: dict[str, Any] = {}
            for name, value in item.feature_map().items():
                if descriptor_limited and name not in allowed:
                    continue
                encoded = _wire_feature_value(value)
                if encoded is not None:
                    wire[name] = encoded
            maps.append(wire)
        return maps

    def _should_flush(self, pending: list[FeatureStructure], pending_bytes: int = 0) -> bool:
        if not self.plan.windowed:
            return False
        # Adaptive batch sizing: if items are small (Tokens), use larger batches;
        # if items are large (Sentences), use smaller batches.
        if self._adaptive_max_rows is None:
            if pending:
                avg_bytes = pending_bytes / max(len(pending), 1)
                if avg_bytes < 64:  # tiny items like Tokens (~20 bytes)
                    self._adaptive_max_rows = min(self.plan.max_rows * 8, 65536)
                    self._adaptive_max_bytes = self.plan.max_bytes * 4
                elif avg_bytes < 256:  # small items
                    self._adaptive_max_rows = min(self.plan.max_rows * 4, 32768)
                    self._adaptive_max_bytes = self.plan.max_bytes * 2
                elif avg_bytes > 2048:  # large items like Sentences
                    self._adaptive_max_rows = max(self.plan.max_rows // 2, 16)
                    self._adaptive_max_bytes = self.plan.max_bytes
                else:
                    self._adaptive_max_rows = self.plan.max_rows
                    self._adaptive_max_bytes = self.plan.max_bytes
        max_rows = self._adaptive_max_rows or self.plan.max_rows
        max_bytes = self._adaptive_max_bytes or self.plan.max_bytes
        return len(pending) >= max_rows or pending_bytes >= max_bytes

    def _estimate_item_bytes(self, item: Any) -> int:
        total = 32 + len(item.type)
        for name, value in self._wire_feature_maps(item.type, [item])[0].items():
            total += len(name) + 4
            if value is None:
                continue
            if isinstance(value, str):
                total += len(value)
            elif isinstance(value, bytes):
                total += len(value)
            else:
                total += 16
        return total

    def _sofa_chunks(self, sofa: SoFa) -> list[Chunk]:
        payload_map: dict[str, Any] = {
            "type": "uima.cas.Sofa",
            "kind": sofa_kind(sofa),
            "mimeType": sofa.mimeType,
            "language": sofa.language,
            "data": sofa_to_wire_data(sofa),
        }
        annotation_type = sofa_annotation_type(sofa)
        if annotation_type:
            payload_map["annotationType"] = annotation_type
            payload_map["spans"] = list(cast(SoFaAnnotationSpans, sofa).spans)
        return [(CHUNK_SOFA, msgpack.packb(payload_map, use_bin_type=True))]

    def _error_chunks(self, errors: list[str | DuuiError]) -> list[Chunk]:
        chunks = []
        for error in errors:
            payload = error.model_dump(exclude_none=True) if isinstance(error, DuuiError) else {"message": str(error)}
            chunks.append((CHUNK_ERROR, msgpack.packb(payload, use_bin_type=True)))
        return chunks

    def _start_payload(self) -> bytes:
        if self.plan.runtime:
            payload = {
                "version": 2,
                "schemaHash": self.plan.schema_hash,
                "protocol": self.plan.protocol,
                "compression": self.plan.compression,
            }
        else:
            payload = self.plan.manifest()
        payload["parameters"] = {}
        payload["view"] = ""
        return msgpack.packb(payload, use_bin_type=True)

    def _decode_start_payload(self, payload: bytes) -> tuple[dict[str, Any], str, list[str], list[list[str]]]:
        if not payload:
            return {}, "", [], []
        start_payload = self._decode_msgpack_map(payload)
        raw_parameters = start_payload.get("parameters", {})
        parameters = {
            str(k): normalize_uima_value(v)
            for k, v in raw_parameters.items()
        } if isinstance(raw_parameters, dict) else {}
        view = start_payload.get("view", "")
        fallback_manifest = self.plan.manifest()
        raw_types = start_payload.get("types", fallback_manifest["types"])
        type_names = [str(value) for value in raw_types] if isinstance(raw_types, list) else []
        raw_features = start_payload.get("features", fallback_manifest["features"])
        features_by_type = [
            [str(feature) for feature in feature_list]
            for feature_list in raw_features
            if isinstance(feature_list, list)
        ] if isinstance(raw_features, list) else []
        return parameters, view if isinstance(view, str) else "", type_names, features_by_type

    def _decode_sofa_payload(self, payload: bytes) -> SoFa:
        unpacked = self._decode_msgpack_map(payload)
        mime_value = unpacked.get("mimeType", self._default_input_mime())
        lang_value = unpacked.get("language", self._default_input_language())
        if not isinstance(mime_value, str) or not isinstance(lang_value, str):
            raise ValueError("invalid SOFA payload mimeType/language")
        annotation_type = unpacked.get("annotationType")
        spans = unpacked.get("spans")
        return sofa_from_wire(
            mime_type=mime_value,
            language=lang_value,
            data=unpacked.get("data"),
            annotation_type=annotation_type if isinstance(annotation_type, str) else None,
            spans=[str(v) for v in spans] if isinstance(spans, list) else None,
        )

    def _decode_row_batch(self, payload: bytes, type_names: list[str], features_by_type: list[list[str]]) -> list[FeatureStructure]:
        unpacked = self._decode_msgpack_map(payload)
        type_id_value = unpacked.get("t")
        type_name = _type_name(type_names, type_id_value)
        kind = str(unpacked.get("k", "fs"))
        features = _feature_names_from_ids(features_by_type, type_id_value, unpacked.get("f", []))
        rows = unpacked.get("rows", [])
        out: list[FeatureStructure] = []
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, list) or len(row) < 4:
                    continue
                values = row[3] if isinstance(row[3], list) else []
                fmap = {
                    name: _from_wire_value(values[index])
                    for index, name in enumerate(features)
                    if index < len(values) and values[index] is not None
                }
                out.append(_fs_from_parts(kind, type_name, row[0], row[1], row[2], fmap))
        return out

    def _decode_column_batch(self, payload: bytes, type_names: list[str], features_by_type: list[list[str]]) -> list[FeatureStructure]:
        unpacked = self._decode_msgpack_map(payload)
        type_id_value = unpacked.get("t")
        type_name = _type_name(type_names, type_id_value)
        kind = str(unpacked.get("k", "fs"))
        features = _feature_names_from_ids(features_by_type, type_id_value, unpacked.get("f", []))
        refs = unpacked.get("r", [])
        begins = unpacked.get("b", [])
        ends = unpacked.get("e", [])
        row_count_value = unpacked.get("n")
        bp_raw = unpacked.get("bp")
        if isinstance(bp_raw, bytes):
            try:
                begins = _unpack_i32_column_delta(bp_raw)
            except Exception:
                begins = _unpack_i32_column(bp_raw)
        ep_raw = unpacked.get("ep")
        if isinstance(ep_raw, bytes):
            try:
                ends = _unpack_i32_column_delta(ep_raw)
            except Exception:
                ends = _unpack_i32_column(ep_raw)
        columns = unpacked.get("c", [])
        if not isinstance(columns, list):
            columns = []
        sparse_columns = unpacked.get("s", [])
        dictionary_columns = unpacked.get("d", [])
        if isinstance(dictionary_columns, list):
            for dictionary_column in dictionary_columns:
                if not isinstance(dictionary_column, list) or len(dictionary_column) < 3:
                    continue
                dictionary_features = _feature_names_from_ids(features_by_type, type_id_value, [dictionary_column[0]])
                dictionary = dictionary_column[1] if isinstance(dictionary_column[1], list) else []
                ids = dictionary_column[2] if isinstance(dictionary_column[2], list) else []
                if not dictionary_features:
                    continue
                features.append(dictionary_features[0])
                columns.append([
                    dictionary[value - 1]
                    if isinstance(value, int) and value > 0 and value <= len(dictionary)
                    else None
                    for value in ids
                ])
        row_count = row_count_value if isinstance(row_count_value, int) and row_count_value >= 0 else 0
        if row_count == 0:
            row_count = max(len(refs), len(begins), len(ends)) if all(isinstance(v, list) for v in (refs, begins, ends)) else 0
            if isinstance(columns, list):
                for column in columns:
                    if isinstance(column, list) and len(column) > row_count:
                        row_count = len(column)
        sparse_by_row: dict[int, list[tuple[str, Any]]] = {}
        if isinstance(sparse_columns, list):
            for sparse in sparse_columns:
                if not isinstance(sparse, list) or len(sparse) < 3:
                    continue
                sparse_features = _feature_names_from_ids(features_by_type, type_id_value, [sparse[0]])
                if not sparse_features:
                    continue
                rows = sparse[1] if isinstance(sparse[1], list) else []
                values = sparse[2] if isinstance(sparse[2], list) else []
                if len(rows) > row_count:
                    row_count = len(rows)
                for sparse_index, sparse_row in enumerate(rows):
                    if isinstance(sparse_row, int) and sparse_index < len(values):
                        sparse_by_row.setdefault(sparse_row - 1, []).append(
                            (sparse_features[0], values[sparse_index])
                        )
        out: list[FeatureStructure] = []
        for row_index in range(row_count):
            fmap = {}
            if isinstance(columns, list):
                for feature_index, name in enumerate(features):
                    if feature_index >= len(columns) or not isinstance(columns[feature_index], list):
                        continue
                    column = columns[feature_index]
                    if row_index < len(column) and column[row_index] is not None:
                        fmap[name] = _from_wire_value(column[row_index])
            for name, value in sparse_by_row.get(row_index, []):
                fmap[name] = _from_wire_value(value)
            out.append(_fs_from_parts(kind, type_name, _get(refs, row_index), _get(begins, row_index), _get(ends, row_index), fmap))
        return out

    def _decode_legacy_feature_structure(self, payload: bytes) -> FeatureStructure:
        unpacked = self._decode_msgpack_map(payload)
        raw_features = cast(dict[str, Any], unpacked.get("features", unpacked.get("f", {})))
        features = {str(k): normalize_uima_value(v) for k, v in raw_features.items()}
        covered_text = unpacked.get("coveredText")
        if isinstance(covered_text, str):
            features["coveredText"] = covered_text
        return FeatureStructure(
            ref=cast(int | None, unpacked.get("ref")),
            type=str(unpacked.get("type", unpacked.get("t", ""))),
            begin=cast(int | None, unpacked.get("begin", unpacked.get("b"))),
            end=cast(int | None, unpacked.get("end", unpacked.get("e"))),
            features=features,
        )
    def _decode_msgpack_map(self, payload: bytes) -> dict[str, Any]:
        unpacked = cast(object, msgpack.unpackb(payload, raw=False, strict_map_key=False))
        if not isinstance(unpacked, dict):
            raise ValueError("chunk payload must decode to msgpack map")
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
        header_len = 17 if self.plan.runtime else 5
        while offset < total:
            if total - offset < header_len:
                raise ValueError("truncated chunk header")
            chunk_type = data[offset]
            offset += 1
            payload_len = struct.unpack(">I", data[offset:offset + 4])[0]
            offset += 4
            if self.plan.runtime:
                offset += 12
            if total - offset < payload_len:
                raise ValueError("truncated chunk payload")
            chunks.append((chunk_type, data[offset:offset + payload_len]))
            offset += payload_len
        return chunks

    async def _iter_chunked_stream(
        self,
        data: AsyncIterable[bytes],
        *,
        max_partial_buffer_bytes: int,
        max_chunk_payload_bytes: int | None,
    ) -> AsyncIterator[tuple[int, bytes]]:
        buffer = bytearray()
        header_len = 17 if self.plan.runtime else 5
        async for part in data:
            if not part:
                continue
            buffer.extend(part)
            if len(buffer) > max_partial_buffer_bytes:
                raise ValueError("partial chunk buffer limit exceeded")
            while len(buffer) >= header_len:
                chunk_type = buffer[0]
                payload_len = struct.unpack(">I", buffer[1:5])[0]
                frame_len = header_len + payload_len
                if max_chunk_payload_bytes is not None and payload_len > max_chunk_payload_bytes:
                    raise ValueError("chunk payload too large")
                if frame_len > max_partial_buffer_bytes:
                    raise ValueError("partial chunk buffer limit exceeded")
                if len(buffer) < frame_len:
                    break
                yield chunk_type, bytes(buffer[header_len:frame_len])
                del buffer[:frame_len]
        if buffer:
            raise ValueError("truncated chunk stream")

    def _serialize_chunks(self, chunks: list[Chunk]) -> bytes:
        out = bytearray()
        for chunk in chunks:
            out.extend(self._serialize_chunk(*chunk))
        return bytes(out)

    def _serialize_chunk(
        self,
        chunk_type: int,
        payload: bytes,
        type_id: int = 0,
        row_count: int = 0,
        flags: int = 0,
    ) -> bytes:
        profile = self._record_chunk_profile(chunk_type, payload)
        header = bytes([chunk_type]) + struct.pack(">I", len(payload))
        if self.plan.runtime:
            sequence = profile.chunks if profile is not None else 0
            header += struct.pack(">IHHI", sequence, flags, type_id, row_count)
        return header + payload

    def _record_chunk_profile(self, chunk_type: int, payload: bytes) -> Any:
        profile = current_wire_profile()
        if profile is not None:
            profile.set_plan(protocol=self.plan.protocol, compression=self.plan.compression)
            profile.add_chunk(chunk_type, len(payload))
        return profile

    def _generate_lua_script(self) -> str:
        descriptor_json = json.dumps(self.descriptor.model_dump(), ensure_ascii=False)
        manifest_json = json.dumps(self.plan.manifest(), ensure_ascii=False)
        input_types_json = json.dumps(_input_types(self.descriptor), ensure_ascii=False)
        generated_setters = lua_generated_setters(self.plan.manifest())
        generated_batch_appliers = lua_generated_batch_appliers(self.plan.manifest())
        script_kind = "Descriptor-generated runtime" if self.plan.runtime else "Descriptor-generated"
        return generate_lua_script(
            descriptor_json=descriptor_json,
            manifest_json=manifest_json,
            input_types_json=input_types_json,
            generated_setters=generated_setters,
            generated_batch_appliers=generated_batch_appliers,
            script_kind=script_kind,
            annotator_name=self.descriptor.name,
            protocol=self.plan.protocol,
            compression=self.plan.compression,
        )

    def _generate_lua_script_cached(self) -> str:
        """Cache the generated Lua script and only regenerate when manifest changes."""
        manifest = self.plan.manifest()
        cache_key = self.plan.schema_hash
        cached = MsgPackLuaCodec._lua_script_cache.get(cache_key)
        if cached is not None:
            return cached
        script = self._generate_lua_script()
        MsgPackLuaCodec._lua_script_cache[cache_key] = script
        if len(MsgPackLuaCodec._lua_script_cache) > 64:
            oldest = next(iter(MsgPackLuaCodec._lua_script_cache))
            del MsgPackLuaCodec._lua_script_cache[oldest]
        return script
