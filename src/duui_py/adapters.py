from __future__ import annotations

import inspect
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

from fastapi import HTTPException, Request, Response

from duui_py.annotator import DuuiAnnotator, V1AsyncProcess, V1Payload, V1Process
from duui_py.codecs.base import Codec
from duui_py.errors import DuuiHttpError, log_duui_error, wrap_exception
from duui_py.models import AnnotatorConfig, DuuiError, DuuiResult, V1RequestEnvelope
from duui_py.models.uima import Annotation, FeatureStructure, SoFa, SoFaAnnotationSpans, SoFaBase, sofa_kind
from duui_py.models.uima_typesystem.texttechnologylab.annotation.types import AnnotatorMetaData, DocumentModification
from duui_py.utils.mime import matches_mime_type

RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")


@dataclass(frozen=True)
class AsyncChunkedAdapterConfig:
    max_partial_buffer_bytes: int = 64 * 1024 * 1024
    max_chunk_payload_bytes: int | None = None


def _merge_results(base: DuuiResult, chunk: DuuiResult) -> DuuiResult:
    if chunk.sofa is not None:
        base.sofa = chunk.sofa
    if chunk.annotations:
        base.annotations.extend(chunk.annotations)
    if chunk.feature_structures:
        base.feature_structures.extend(chunk.feature_structures)
    if chunk.meta is not None:
        base.meta = chunk.meta
    if chunk.modification_meta is not None:
        base.modification_meta = chunk.modification_meta
    if chunk.errors:
        base.errors.extend(chunk.errors)
    return base


def _merge_output_item(base: DuuiResult, item: Any) -> DuuiResult:
    if isinstance(item, DuuiResult):
        return _merge_results(base, item)
    if isinstance(item, DuuiError):
        base.errors.append(item)
    elif isinstance(item, SoFaBase):
        base.sofa = item
    elif isinstance(item, Annotation):
        base.annotations.append(item)
    elif isinstance(item, AnnotatorMetaData):
        base.meta = item
    elif isinstance(item, DocumentModification):
        base.modification_meta = item
    elif isinstance(item, FeatureStructure):
        base.feature_structures.append(item)
    elif isinstance(item, str):
        base.errors.append(item)
    else:
        raise HTTPException(status_code=500, detail=f"unsupported annotator output item: {type(item).__name__}")
    return base


async def _exception_to_error_item(exc: BaseException, *, operation: str) -> DuuiError:
    if isinstance(exc, DuuiHttpError):
        error = exc
    elif isinstance(exc, HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        error = DuuiHttpError(exc.status_code, detail)
    else:
        error = wrap_exception(exc)
    await log_duui_error(error, operation=operation)
    return error.to_duui_error()


def _iter_descriptor_mimes(io_desc: Any) -> list[str]:
    out: list[str] = []
    for domain in ("text", "bytes", "uri", "annotation"):
        spec = getattr(io_desc, domain, None)
        if spec is None:
            continue
        for _, alt in spec.iter_alternatives():
            if alt.mimeType:
                out.append(alt.mimeType)
    return out


def _resolve_domain_alias_for_sofa(io_desc: Any, sofa: SoFa) -> tuple[str, str, Any]:
    kind = sofa_kind(sofa)
    domain = "annotation" if kind == "annotation_spans" else kind

    if domain == "annotation" or isinstance(sofa, SoFaAnnotationSpans):
        return domain, "default", io_desc.resolve(domain, "default")

    spec = getattr(io_desc, domain, None)
    if spec is None:
        raise HTTPException(status_code=415, detail=f"descriptor domain '{domain}' not configured")

    actual = sofa.mimeType
    for alias, alt in spec.iter_alternatives():
        if alt.mimeType and matches_mime_type(alt.mimeType, actual):
            return domain, alias, io_desc.resolve(domain, alias)

    raise HTTPException(status_code=415, detail=f"unsupported sofa.mimeType: {actual}")


def _find_fs_for_type(fs_items: list[FeatureStructure], type_name: str) -> list[FeatureStructure]:
    suffix = type_name.split(".")[-1]
    return [item for item in fs_items if item.type == type_name or item.type.endswith(f".{suffix}")]


def _build_feature_structure_map(
    resolved_types: dict[str, list[str]],
    fs_items: list[FeatureStructure],
    parameters: dict[str, Any],
) -> dict[str, list[FeatureStructure]]:
    out: dict[str, list[FeatureStructure]] = {}
    try_fallback = bool(parameters.get("recovery.try_fallback", False))

    for type_alias, candidates in resolved_types.items():
        if not candidates:
            raise HTTPException(status_code=422, detail=f"type alias '{type_alias}' has no candidates")

        pref_key = f"pref.{type_alias}"
        preferred = parameters.get(pref_key)
        chosen: list[FeatureStructure] | None = None

        if isinstance(preferred, str):
            if preferred not in candidates:
                raise HTTPException(status_code=422, detail=f"invalid preferred type for '{type_alias}': {preferred}")
            selected = _find_fs_for_type(fs_items, preferred)
            if selected:
                chosen = selected
            elif not try_fallback:
                raise HTTPException(status_code=422, detail=f"preferred type '{preferred}' for '{type_alias}' not present")

        if chosen is None:
            for candidate in candidates:
                selected = _find_fs_for_type(fs_items, candidate)
                if selected:
                    chosen = selected
                    break

        if chosen is None:
            raise HTTPException(status_code=422, detail=f"missing required feature structures for '{type_alias}'")

        out[type_alias] = chosen

    return out


async def _invoke_v1(
    annotator: V1Process[Any, DuuiResult],
    doc: V1RequestEnvelope,
    descriptor_io: Any,
) -> AsyncIterator[Any]:
    _, _, resolved = _resolve_domain_alias_for_sofa(descriptor_io, doc.sofa)
    payload_cls = cast(type[V1Payload], getattr(annotator, "payload_model", V1Payload))
    fs_map = _build_feature_structure_map(resolved.types, list(doc.fs), dict(doc.parameters))
    payload = payload_cls.model_validate({"view": doc.view, "feature_structures": fs_map})

    kind = sofa_kind(doc.sofa)
    if kind == "text":
        method = getattr(annotator, "process_text", None)
    elif kind == "bytes":
        method = getattr(annotator, "process_bytes", None)
    elif kind == "uri":
        method = getattr(annotator, "process_uri", None)
    else:
        method = getattr(annotator, "process_spans", None)

    if method is None:
        raise HTTPException(status_code=422, detail=f"missing processor for sofa subtype '{kind}'")

    returned_obj = method(doc.sofa, payload, dict(doc.parameters))
    if isinstance(annotator, V1AsyncProcess):
        if inspect.isawaitable(returned_obj):
            returned_obj = await cast(Any, returned_obj)
        if returned_obj is None:
            return
        async for part in cast(AsyncIterable[Any], returned_obj):
            yield part
        return

    returned = returned_obj
    if inspect.isawaitable(returned):
        returned = await cast(Any, returned)
    yield DuuiResult() if returned is None else cast(DuuiResult, returned)


def _validate_output_mime(cfg: AnnotatorConfig, result: DuuiResult) -> None:
    validation = cfg.meta.settings.validation
    if not (validation.strict_mime_validation and validation.strict_output_mime_check):
        return
    if result.sofa is None:
        return
    actual = result.sofa.mimeType
    output_mimes = _iter_descriptor_mimes(cfg.descriptor.output)
    if output_mimes and not any(matches_mime_type(pattern, actual) for pattern in output_mimes):
        raise HTTPException(status_code=500, detail=f"annotator returned unsupported output sofa.mimeType: {actual}")


def _validate_output_item_mime(cfg: AnnotatorConfig, item: Any) -> None:
    if isinstance(item, DuuiResult):
        _validate_output_mime(cfg, item)
    elif isinstance(item, SoFaBase):
        _validate_output_mime(cfg, DuuiResult(sofa=item))


async def _process_v1_or_simple(
    annotator: DuuiAnnotator[Any, Any],
    cfg: AnnotatorConfig,
    doc: V1RequestEnvelope,
) -> DuuiResult:
    validation = cfg.meta.settings.validation
    if validation.strict_mime_validation and validation.strict_input_mime_check:
        _resolve_domain_alias_for_sofa(cfg.descriptor.input, doc.sofa)

    if isinstance(annotator, V1Process):
        merged = DuuiResult()
        try:
            async for item in _invoke_v1(cast(V1Process[Any, DuuiResult], annotator), doc, cfg.descriptor.input):
                _validate_output_item_mime(cfg, item)
                _merge_output_item(merged, item)
        except Exception as exc:  # noqa: BLE001
            _merge_output_item(merged, await _exception_to_error_item(exc, operation="process"))
        _validate_output_mime(cfg, merged)
        return merged

    returned = annotator.process(doc)
    if hasattr(returned, "__aiter__"):
        merged = DuuiResult()
        try:
            async for item in cast(AsyncIterable[Any], returned):
                _validate_output_item_mime(cfg, item)
                _merge_output_item(merged, item)
        except Exception as exc:  # noqa: BLE001
            _merge_output_item(merged, await _exception_to_error_item(exc, operation="process"))
        return merged

    try:
        result = await returned
    except Exception as exc:  # noqa: BLE001
        return DuuiResult(errors=[await _exception_to_error_item(exc, operation="process")])
    if isinstance(result, DuuiResult):
        _validate_output_mime(cfg, result)
        return result
    raise HTTPException(status_code=500, detail="non-V1 annotator returned unsupported response type")


async def _iter_v1_or_simple(
    annotator: DuuiAnnotator[Any, Any],
    cfg: AnnotatorConfig,
    doc: V1RequestEnvelope,
) -> AsyncIterator[Any]:
    validation = cfg.meta.settings.validation
    if validation.strict_mime_validation and validation.strict_input_mime_check:
        _resolve_domain_alias_for_sofa(cfg.descriptor.input, doc.sofa)

    if isinstance(annotator, V1Process):
        try:
            async for item in _invoke_v1(cast(V1Process[Any, DuuiResult], annotator), doc, cfg.descriptor.input):
                _validate_output_item_mime(cfg, item)
                yield item
        except Exception as exc:  # noqa: BLE001
            yield await _exception_to_error_item(exc, operation="process")
        return

    returned = annotator.process(doc)
    if hasattr(returned, "__aiter__"):
        try:
            async for item in cast(AsyncIterable[Any], returned):
                _validate_output_item_mime(cfg, item)
                yield item
        except Exception as exc:  # noqa: BLE001
            yield await _exception_to_error_item(exc, operation="process")
        return

    try:
        result = await returned
    except Exception as exc:  # noqa: BLE001
        yield await _exception_to_error_item(exc, operation="process")
        return
    if isinstance(result, DuuiResult):
        _validate_output_mime(cfg, result)
        yield result
        return
    raise HTTPException(status_code=500, detail="non-V1 annotator returned unsupported response type")


class RequestAdapter(Generic[RequestT, ResponseT]):
    async def handle(
        self,
        request: Request,
        annotator: DuuiAnnotator[RequestT, ResponseT],
        codec: Codec[RequestT, ResponseT],
        cfg: AnnotatorConfig,
    ) -> Response:
        raise NotImplementedError


class SynchronousRequestAdapter(RequestAdapter[RequestT, ResponseT]):
    async def handle(
        self,
        request: Request,
        annotator: DuuiAnnotator[RequestT, ResponseT],
        codec: Codec[RequestT, ResponseT],
        cfg: AnnotatorConfig,
    ) -> Response:
        limits = cfg.meta.settings.limits
        errors = cfg.meta.settings.errors

        body = await request.body()
        if limits.request_max_bytes is not None and len(body) > limits.request_max_bytes:
            raise HTTPException(status_code=413, detail="request payload too large")

        try:
            doc = codec.decode_request(body)
        except Exception as exc:  # noqa: BLE001
            detail = f"request decode failed: {exc}" if errors.include_validation_details else "request decode failed"
            raise HTTPException(status_code=400 if errors.fail_on_codec_error else 422, detail=detail) from exc

        if isinstance(doc, V1RequestEnvelope):
            result = cast(ResponseT, await _process_v1_or_simple(cast(DuuiAnnotator[Any, Any], annotator), cfg, doc))
        else:
            result = await annotator.process(doc)

        try:
            response_body = codec.encode_response(result)
        except Exception as exc:  # noqa: BLE001
            detail = f"response encode failed: {exc}" if errors.include_validation_details else "response encode failed"
            raise HTTPException(status_code=500 if errors.fail_on_codec_error else 422, detail=detail) from exc

        if limits.response_max_bytes is not None and len(response_body) > limits.response_max_bytes:
            raise HTTPException(status_code=500, detail="response payload too large")

        return Response(content=response_body, media_type=codec.response_media_type)


def _supports_async_chunks(codec: object) -> bool:
    return callable(getattr(codec, "decode_request_stream", None)) and callable(getattr(codec, "encode_response", None))


class AsyncChunkedRequestAdapter(RequestAdapter[V1RequestEnvelope, Any]):
    def __init__(self, config: AsyncChunkedAdapterConfig | None = None):
        self.config = config or AsyncChunkedAdapterConfig()

    async def handle(
        self,
        request: Request,
        annotator: DuuiAnnotator[V1RequestEnvelope, Any],
        codec: Codec[V1RequestEnvelope, Any],
        cfg: AnnotatorConfig,
    ) -> Response:
        if not _supports_async_chunks(codec):
            raise HTTPException(status_code=500, detail="codec does not support async chunked request handling")

        limits = cfg.meta.settings.limits
        errors = cfg.meta.settings.errors

        async def limited_stream() -> AsyncIterator[bytes]:
            total = 0
            async for part in request.stream():
                if part == b"":
                    break
                total += len(part)
                if limits.request_max_bytes is not None and total > limits.request_max_bytes:
                    raise HTTPException(status_code=413, detail="request payload too large")
                yield part

        try:
            doc = await cast(Any, codec).decode_request_stream(
                limited_stream(),
                max_partial_buffer_bytes=self.config.max_partial_buffer_bytes,
                max_chunk_payload_bytes=self.config.max_chunk_payload_bytes,
            )
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            detail = f"request decode failed: {exc}" if errors.include_validation_details else "request decode failed"
            raise HTTPException(status_code=400 if errors.fail_on_codec_error else 422, detail=detail) from exc

        result = await _process_v1_or_simple(cast(DuuiAnnotator[Any, Any], annotator), cfg, doc)

        try:
            response_body = codec.encode_response(cast(Any, result))
        except Exception as exc:  # noqa: BLE001
            detail = f"response encode failed: {exc}" if errors.include_validation_details else "response encode failed"
            raise HTTPException(status_code=500 if errors.fail_on_codec_error else 422, detail=detail) from exc

        if limits.response_max_bytes is not None and len(response_body) > limits.response_max_bytes:
            raise HTTPException(status_code=500, detail="response payload too large")

        return Response(content=response_body, media_type=codec.response_media_type)


def default_request_adapter(codec: Codec[Any, Any]) -> RequestAdapter[Any, Any]:
    if _supports_async_chunks(codec):
        return AsyncChunkedRequestAdapter()
    return SynchronousRequestAdapter()
