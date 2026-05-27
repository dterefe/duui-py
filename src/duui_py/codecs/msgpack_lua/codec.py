from __future__ import annotations

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

    def __init__(self, config: AnnotatorConfig):
        self.config = config
        self.descriptor = config.descriptor
        self.plan = WirePlan.from_config(config)

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
            "version": 2,
            "spec": self._generate_lua_script(),
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
                payload = zlib.decompress(payload)
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
        ordered_groups = self._dependency_ordered_groups(grouped)
        columnar = self.plan.columnar
        chunks: list[Chunk] = []

        def flush_direct(payloads: list[tuple[int, int, bytes]]) -> None:
            if not payloads:
                return
            row_count = sum(row_count for _, row_count, _ in payloads)
            if len(payloads) == 1:
                type_id, rows, payload = payloads[0]
                chunks.append((CHUNK_DIRECT_BATCH, payload, type_id, rows, 0))
                return
            with timed_profile_field("pack_msgpack_ms"):
                payload = msgpack.packb([item[2] for item in payloads], use_bin_type=True)
            chunks.append((CHUNK_DIRECT_MULTI_BATCH, payload, 0, row_count, 0))

        direct_payloads: list[tuple[int, int, bytes]] = []
        for kind, type_name, group in ordered_groups:
            if self.plan.protocol == "runtime-msgpack-direct" and self._can_direct_batch(type_name, group):
                direct_payloads.append((
                    self.plan.type_id(type_name),
                    len(group),
                    self._direct_batch_payload(kind, type_name, group),
                ))
                continue
            flush_direct(direct_payloads)
            direct_payloads = []
            if columnar:
                payload = self._column_batch_payload(kind, type_name, group)
                type_id = self.plan.type_id(type_name)
                if self.plan.compressed:
                    with timed_profile_field("compress_ms"):
                        payload = zlib.compress(payload, level=1)
                    chunks.append((CHUNK_COMPRESSED_BATCH, payload, type_id, len(group), 0))
                else:
                    chunks.append((CHUNK_COLUMN_BATCH, payload, type_id, len(group), 0))
            else:
                chunks.append((CHUNK_ROW_BATCH, self._row_batch_payload(kind, type_name, group), self.plan.type_id(type_name), len(group), 0))
        flush_direct(direct_payloads)
        return chunks

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

    def _direct_batch_payload(self, kind: str, type_name: str, items: list[Any]) -> bytes:
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
            payload = [
                self.plan.type_id(type_name),
                1 if kind == "ann" else 0,
                refs if any(ref is not None for ref in refs) else None,
                _pack_i32_column([item.begin for item in items]),
                _pack_i32_column([item.end for item in items]),
                dense_feature_ids,
                dense_columns,
                sparse_columns if sparse_columns else None,
                dictionary_columns if dictionary_columns else None,
            ]
            profile = current_wire_profile()
            if profile is not None:
                profile.set_plan(protocol=self.plan.protocol, compression=self.plan.compression)
                profile.rows += len(items)
                profile.feature_columns += len(features)
        with timed_profile_field("pack_msgpack_ms"):
            return msgpack.packb(payload, use_bin_type=True)
        with timed_profile_field("pack_msgpack_ms"):
            return msgpack.packb(self._direct_batch_value(kind, type_name, items), use_bin_type=True)

    def _column_batch_payload(self, kind: str, type_name: str, items: list[Any]) -> bytes:
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
                payload["bp"] = _pack_i32_column(begins)
                payload["ep"] = _pack_i32_column(ends)
            else:
                payload["b"] = begins
                payload["e"] = ends
            refs = [item.ref for item in items]
            if any(ref is not None for ref in refs):
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
        return len(pending) >= self.plan.max_rows or pending_bytes >= self.plan.max_bytes

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
        if isinstance(unpacked.get("bp"), bytes):
            begins = _unpack_i32_column(cast(bytes, unpacked["bp"]))
        if isinstance(unpacked.get("ep"), bytes):
            ends = _unpack_i32_column(cast(bytes, unpacked["ep"]))
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
        generated_setters = self._lua_generated_setters()
        generated_batch_appliers = self._lua_generated_batch_appliers()
        script_kind = "Descriptor-generated runtime" if self.plan.runtime else "Descriptor-generated"
        return f"""-- {script_kind} DUUI MsgPack Lua wire protocol v2 for {self.descriptor.name}
-- Protocol: {self.plan.protocol}; compression: {self.plan.compression}

if MessagePack == nil then MessagePack = luajava.bindClass("org.msgpack.core.MessagePack") end
if JCasUtil == nil then JCasUtil = luajava.bindClass("org.apache.uima.fit.util.JCasUtil") end
if DUUIBytes == nil then DUUIBytes = luajava.bindClass("org.texttechnologylab.duui.communication.DUUIBytes") end
if ByteArrayOutputStream == nil then ByteArrayOutputStream = luajava.bindClass("java.io.ByteArrayOutputStream") end
if Inflater == nil then Inflater = luajava.bindClass("java.util.zip.Inflater") end

local descriptor = json.decode([=[{descriptor_json}]=])
local manifest = json.decode([=[{manifest_json}]=])
local input_types = json.decode([=[{input_types_json}]=])
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
        local it = ann_list:listIterator()
        while it:hasNext() do p:packInt(it:next():getBegin()) end
        p:packString("e"); p:packArrayHeader(ann_list:size())
        it = ann_list:listIterator()
        while it:hasNext() do p:packInt(it:next():getEnd()) end
        p:packString("c"); p:packArrayHeader(1); p:packArrayHeader(ann_list:size())
        it = ann_list:listIterator()
        while it:hasNext() do p:packString(it:next():getCoveredText() or "") end
        local out = p:toByteArray(); p:close()
        write_chunk(outputStream, CHUNK_COLUMN_BATCH, out, tid, ann_list:size(), 0)
        return
    end
    local rows = {{}}
    local it = ann_list:listIterator()
    while it:hasNext() do
        local ann = it:next()
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

local function apply_column_batch(inputCas, cas, ts, payload)
    local u = MessagePack:newDefaultUnpacker(payload)
    local size = u:unpackMapHeader()
    local tid, kind, features, refs, begins, ends, columns, sparse_columns, dictionary_columns = nil, "fs", {{}}, {{}}, {{}}, {{}}, {{}}, {{}}, {{}}
    for _ = 1, size do
        local k = u:unpackString()
        if k == "t" then tid = u:unpackInt()
        elseif k == "k" then kind = u:unpackString()
        elseif k == "f" then features = read_feature_array(u)
        elseif k == "r" then refs = read_long_array(u)
        elseif k == "b" then begins = read_int_array(u)
        elseif k == "e" then ends = read_int_array(u)
        elseif k == "bp" then begins = read_packed_int_array(u)
        elseif k == "ep" then ends = read_packed_int_array(u)
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
        batch_applier(inputCas, cas, type_name, fs_type, kind, refs, begins, ends, features, columns, sparse_columns, sofa_feature, batch_row_count(refs, begins, ends, columns, sparse_columns))
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
    local row_count = batch_row_count(refs, begins, ends, columns, sparse_columns)
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

local function apply_direct_batch(inputCas, cas, ts, payload)
    local u = MessagePack:newDefaultUnpacker(payload)
    u:unpackArrayHeader()
    local tid = u:unpackInt()
    local kind_code = u:unpackInt()
    local kind = "fs"
    if kind_code == 1 then kind = "ann" end
    local refs = read_nullable_long_array(u)
    local begins = read_packed_int_array(u)
    local ends = read_packed_int_array(u)
    local features = read_int_array(u)
    local col_count = u:unpackArrayHeader()
    local columns = {{}}
    for i = 1, col_count do columns[i] = read_feature_value_array(u, tid, features[i]) end
    local sparse_columns = read_direct_sparse_columns(u, tid)
    local dictionary_columns = read_direct_dictionary_columns(u)
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
        batch_row_count(refs, begins, ends, columns, sparse_columns)
    )
end

local function apply_direct_multi_batch(inputCas, cas, ts, payload)
    local u = MessagePack:newDefaultUnpacker(payload)
    local count = u:unpackArrayHeader()
    for i = 1, count do
        local size = u:unpackBinaryHeader()
        apply_direct_batch(inputCas, cas, ts, u:readPayload(size))
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
            apply_column_batch(inputCas, cas, ts, chunk.payload)
        elseif chunk.type == CHUNK_COMPRESSED_BATCH then
            apply_column_batch(inputCas, cas, ts, inflate_bytes(chunk.payload))
        elseif chunk.type == CHUNK_DIRECT_BATCH then
            apply_direct_batch(inputCas, cas, ts, chunk.payload)
        elseif chunk.type == CHUNK_DIRECT_MULTI_BATCH then
            apply_direct_multi_batch(inputCas, cas, ts, chunk.payload)
        elseif chunk.type == CHUNK_ERROR then
            error("received ERROR chunk")
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

    def _lua_generated_setters(self) -> str:
        lines: list[str] = []
        manifest = self.plan.manifest()
        types = manifest["types"]
        features_by_type = manifest["features"]
        for index, type_name in enumerate(types, start=1):
            features = features_by_type[index - 1] if index - 1 < len(features_by_type) else []
            if not features:
                continue
            lines.append(f"generated_setters[{index}] = function(fs, feature_id, value)")
            lines.append("    if value == nil then return true end")
            lines.append("    if type(value) == \"string\" and string.sub(value, 1, 5) == \"$ref:\" then return false end")
            first = True
            for feature_id, feature in enumerate(features, start=1):
                if not feature or feature in {"begin", "end", "type", "ref", "features"}:
                    continue
                method = "set" + feature[:1].upper() + feature[1:]
                prefix = "if" if first else "elseif"
                first = False
                state_key = json.dumps(f"{index}:{feature}")
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

    def _lua_generated_batch_appliers(self) -> str:
        lines: list[str] = []
        manifest = self.plan.manifest()
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
                escaped_feature = json.dumps(feature)
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
            lines.append("        if fs ~= nil and kind == \"ann\" then")
            lines.append("            fs:setBegin(begins[row] or 0)")
            lines.append("            fs:setEnd(ends[row] or 0)")
            lines.append("        elseif fs == nil and kind == \"ann\" then")
            lines.append("            fs = cas:createAnnotation(fs_type, begins[row] or 0, ends[row] or 0)")
            lines.append("        elseif fs == nil then")
            lines.append("            fs = cas:createFS(fs_type)")
            lines.append("        end")
            lines.append("        if kind ~= \"ann\" and sofa_feature ~= nil then fs:setFeatureValue(sofa_feature, inputCas:getSofa()) end")
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
