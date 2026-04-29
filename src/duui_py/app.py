from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator
from enum import Enum
import inspect

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from typing import Any, TypeVar, cast

from duui_py.annotator import DuuiAnnotator, V1AsyncProcess, V1Payload, V1Process
from duui_py.codecs.base import Codec, StreamingRequestDecoder, StreamingResponseEncoder
from duui_py.logging import (
    clear_event_context,
    configure_logger,
    configure_metric_collector,
    configure_stream_manager,
    create_event_context_from_request,
    get_event_logger,
    set_event_context,
    ConsoleSink,
    EventSink,
    StreamSink,
)
from duui_py.logging.streaming import router as events_router
from duui_py.models import AnnotatorConfig, V1RequestEnvelope, DuuiResult
from duui_py.models.uima import FeatureStructure
from duui_py.models.uima import SoFa, SoFaAnnotationSpans, SoFaBytes, SoFaText, SoFaURI, sofa_kind
from duui_py.settings import set_settings_once
from duui_py.utils.mime import matches_mime_type

RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")


class ProcessingMode(str, Enum):
    NORMAL = "normal"
    STREAMING = "streaming"


def _validate_lua_communication_layer(codec: Codec[Any, Any]) -> None:
    content = codec.communication_layer_content()
    if str(content.get("format", "")).lower() != "lua" or not str(content.get("spec", "")).strip():
        raise RuntimeError("Invalid codec communication layer: expected non-empty Lua script")


def _is_async_iterable(value: object) -> bool:
    return hasattr(value, "__aiter__")


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


def _merge_documents(base: V1RequestEnvelope, chunk: V1RequestEnvelope) -> V1RequestEnvelope:
    if chunk.parameters:
        merged = dict(base.parameters)
        merged.update(chunk.parameters)
        base.parameters = merged
    if chunk.view:
        base.view = chunk.view
    if chunk.sofa is not None:
        base.sofa = chunk.sofa
    if chunk.fs:
        base.fs.extend(chunk.fs)
    return base


def _determine_processing_mode(codec: Codec[Any, Any]) -> ProcessingMode:
    if isinstance(codec, StreamingRequestDecoder) and isinstance(codec, StreamingResponseEncoder):
        return ProcessingMode.STREAMING
    return ProcessingMode.NORMAL


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

    mode = ""
    if isinstance(sofa, SoFaAnnotationSpans):
        mode = "annotation_spans"

    if domain == "annotation" or mode == "annotation_spans":
        span_alias = "default"
        if hasattr(sofa, "annotationType") and getattr(sofa, "annotationType", ""):
            span_alias = "default"
        return domain, span_alias, io_desc.resolve(domain, span_alias)

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
) -> AsyncIterator[DuuiResult]:
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
        async for part in cast(AsyncIterable[DuuiResult], returned_obj):
            yield part
        return

    returned = returned_obj
    if inspect.isawaitable(returned):
        returned = await cast(Any, returned)
    if returned is None:
        yield DuuiResult()
    else:
        yield cast(DuuiResult, returned)


def _validate_output_mime(cfg: AnnotatorConfig, result: DuuiResult) -> None:
    if result.sofa is None:
        return
    actual = result.sofa.mimeType
    output_mimes = _iter_descriptor_mimes(cfg.descriptor.output)
    if output_mimes and not any(matches_mime_type(pattern, actual) for pattern in output_mimes):
        raise HTTPException(status_code=500, detail=f"annotator returned unsupported output sofa.mimeType: {actual}")


def create_app(
    annotator_cls: type[DuuiAnnotator[RequestT, ResponseT]],
    *,
    config_path: str | None = None,
    config: AnnotatorConfig | None = None,
) -> FastAPI:
    annotator = annotator_cls(config_path=config_path, config=config)
    cfg = annotator.config
    set_settings_once(cfg.meta.settings)

    settings = cfg.meta.settings
    limits = settings.limits
    errors = settings.errors
    validation = settings.validation
    codec: Codec[RequestT, ResponseT] = annotator.codec()
    _validate_lua_communication_layer(codec)
    process_mode = _determine_processing_mode(codec)

    app = FastAPI(title=cfg.descriptor.name, version=cfg.descriptor.version)
    typesystem_xml = open(cfg.typesystem_xml_path, "rb").read()
    logger = None

    @app.get("/v1/typesystem")
    def get_typesystem() -> Response:
        return Response(content=typesystem_xml, media_type="application/xml")

    @app.get("/v1/communication_layer")
    def get_communication_layer() -> Response:
        return Response(content=str(codec.communication_layer_content()["spec"]), media_type="text/plain; charset=utf-8")

    @app.get("/v1/details/input_output")
    def get_input_output() -> dict[str, Any]:
        d = cfg.descriptor
        return {"name": d.name, "version": d.version, "input": d.input.model_dump(), "output": d.output.model_dump()}

    @app.get("/v1/documentation")
    def get_documentation() -> dict[str, Any]:
        d = cfg.descriptor
        return {
            "annotator_name": d.name,
            "version": d.version,
            "description": cfg.description,
            "implementation_lang": cfg.meta.implementation_lang,
            "meta": cfg.meta.meta,
            "parameters": cfg.parameters_schema,
        }

    @app.post("/v1/process")
    async def post_process(request: Request) -> Response:
        if logger is not None:
            await logger.info(f"Process request started ({process_mode.value})")

        async def _process_doc(doc: V1RequestEnvelope) -> DuuiResult:
            if validation.strict_mime_validation and validation.strict_input_mime_check:
                _resolve_domain_alias_for_sofa(cfg.descriptor.input, doc.sofa)

            if isinstance(annotator, V1Process):
                merged = DuuiResult()
                async for item in _invoke_v1(cast(V1Process[Any, DuuiResult], annotator), doc, cfg.descriptor.input):
                    _merge_results(merged, item)
                _validate_output_mime(cfg, merged)
                return merged

            result = await annotator.process(cast(RequestT, doc))
            if isinstance(result, DuuiResult):
                _validate_output_mime(cfg, result)
                return result
            raise HTTPException(status_code=500, detail="non-V1 annotator returned unsupported response type")

        if process_mode == ProcessingMode.STREAMING:
            async def limited_body_stream() -> AsyncIterator[bytes]:
                total = 0
                async for chunk in request.stream():
                    if chunk == b"":
                        break
                    total += len(chunk)
                    if limits.request_max_bytes is not None and total > limits.request_max_bytes:
                        raise HTTPException(status_code=413, detail="request payload too large")
                    yield chunk

            try:
                decoded_input = await cast(StreamingRequestDecoder[RequestT], codec).decode_request_stream(limited_body_stream())
            except Exception as exc:  # noqa: BLE001
                detail = f"request decode failed: {exc}" if errors.include_validation_details else "request decode failed"
                raise HTTPException(status_code=400 if errors.fail_on_codec_error else 422, detail=detail) from exc

            async def iter_docs() -> AsyncIterator[V1RequestEnvelope]:
                if _is_async_iterable(decoded_input):
                    async for item in cast(AsyncIterable[Any], decoded_input):
                        if not isinstance(item, V1RequestEnvelope):
                            raise HTTPException(status_code=500, detail="streaming mode expects V1RequestEnvelope input")
                        yield item
                    return
                item = cast(Any, decoded_input)
                if not isinstance(item, V1RequestEnvelope):
                    raise HTTPException(status_code=500, detail="streaming mode expects V1RequestEnvelope input")
                yield item

            async def run_stream() -> AsyncIterator[ResponseT]:
                if isinstance(annotator, V1AsyncProcess):
                    params: dict[str, Any] = {}
                    batch_mode = "await_full_input"
                    batch_n = 1
                    pending: list[V1RequestEnvelope] = []

                    async for item in iter_docs():
                        if item.parameters:
                            params = dict(item.parameters)
                            batch_mode = str(params.get("batch.mode") or "await_full_input")
                            try:
                                batch_n = max(1, int(params.get("batch.n") or 1))
                            except Exception:
                                batch_n = 1

                        pending.append(item)
                        if batch_mode == "every_n_spans" and len(pending) >= batch_n:
                            merged = pending[0]
                            for extra in pending[1:]:
                                _merge_documents(merged, extra)
                            yield cast(ResponseT, await _process_doc(merged))
                            pending = []

                    if pending:
                        merged = pending[0]
                        for extra in pending[1:]:
                            _merge_documents(merged, extra)
                        yield cast(ResponseT, await _process_doc(merged))
                    return

                base: V1RequestEnvelope | None = None
                async for item in iter_docs():
                    if base is None:
                        base = V1RequestEnvelope(parameters=dict(item.parameters), view=item.view, sofa=item.sofa, fs=list(item.fs))
                    else:
                        _merge_documents(base, item)

                if base is None:
                    raise HTTPException(status_code=400, detail="empty streaming input")
                yield cast(ResponseT, await _process_doc(base))

            async def validated_result_stream() -> AsyncIterator[ResponseT]:
                async for result in run_stream():
                    yield result

            try:
                encoded_stream = await cast(StreamingResponseEncoder[ResponseT], codec).encode_response_stream(validated_result_stream())
            except Exception as exc:  # noqa: BLE001
                detail = f"response encode failed: {exc}" if errors.include_validation_details else "response encode failed"
                raise HTTPException(status_code=500 if errors.fail_on_codec_error else 422, detail=detail) from exc

            async def limited_response_stream() -> AsyncIterator[bytes]:
                total = 0
                async for chunk in encoded_stream:
                    total += len(chunk)
                    if limits.response_max_bytes is not None and total > limits.response_max_bytes:
                        raise HTTPException(status_code=500, detail="response payload too large")
                    yield chunk

            response = StreamingResponse(limited_response_stream(), media_type=codec.response_media_type)
            if logger is not None:
                await logger.info("Process request completed successfully")
            return response

        body = await request.body()
        if limits.request_max_bytes is not None and len(body) > limits.request_max_bytes:
            raise HTTPException(status_code=413, detail="request payload too large")

        try:
            doc = codec.decode_request(body)
        except Exception as exc:  # noqa: BLE001
            detail = f"request decode failed: {exc}" if errors.include_validation_details else "request decode failed"
            raise HTTPException(status_code=400 if errors.fail_on_codec_error else 422, detail=detail) from exc

        if not isinstance(doc, V1RequestEnvelope):
            result = await annotator.process(cast(RequestT, doc))
            response_body = codec.encode_response(cast(ResponseT, result))
            return Response(content=response_body, media_type=codec.response_media_type)

        result = await _process_doc(doc)

        try:
            response_body = codec.encode_response(cast(ResponseT, result))
        except Exception as exc:  # noqa: BLE001
            detail = f"response encode failed: {exc}" if errors.include_validation_details else "response encode failed"
            raise HTTPException(status_code=500 if errors.fail_on_codec_error else 422, detail=detail) from exc

        if limits.response_max_bytes is not None and len(response_body) > limits.response_max_bytes:
            raise HTTPException(status_code=500, detail="response payload too large")

        response = Response(content=response_body, media_type=codec.response_media_type)
        if logger is not None:
            await logger.info("Process request completed successfully")
        return response

    logging_settings = settings.logging
    if logging_settings.enabled:
        stream_manager = configure_stream_manager(default_ttl_minutes=logging_settings.stream_timeout_minutes)
        sinks: list[EventSink] = [cast(EventSink, StreamSink(stream_manager))]
        import os
        if os.environ.get("DUUI_DEBUG_LOGGING"):
            sinks.append(cast(EventSink, ConsoleSink()))

        configure_logger(
            sinks=sinks,
            default_context={"annotator_name": cfg.descriptor.name, "annotator_version": cfg.descriptor.version},
            annotator_descriptor=cfg.descriptor,
            start_background_worker=True,
        )

        configure_metric_collector(
            collection_interval_seconds=logging_settings.metrics_collection_interval_seconds,
            include_process_metrics=logging_settings.include_process_metrics,
            include_system_metrics=logging_settings.include_system_metrics,
            include_disk_metrics=logging_settings.include_disk_metrics,
            include_network_metrics=logging_settings.include_network_metrics,
            start_immediately=True,
        )

        app.include_router(events_router)

        @app.middleware("http")
        async def event_context_middleware(request: Request, call_next):
            event_context_param = request.query_params.get("event-context")
            event_context = create_event_context_from_request(
                event_context_param=event_context_param,
                request_id=request.headers.get("x-request-id"),
            )
            set_event_context(event_context)
            try:
                return await call_next(request)
            finally:
                clear_event_context()

        logger = get_event_logger()

    return app
