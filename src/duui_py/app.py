from __future__ import annotations

import inspect
from collections.abc import AsyncIterable, AsyncIterator
from enum import Enum

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Any, TypeVar, cast

from duui_py.annotator import DuuiAnnotator, V1Process, V2Process, V2ProcessChunks
from duui_py.codecs.base import Codec, StreamingRequestDecoder, StreamingResponseEncoder
from duui_py.logging import (
    configure_logger,
    configure_stream_manager,
    configure_metric_collector,
    get_event_logger,
    create_event_context_from_request,
    set_event_context,
    clear_event_context,
    EventContext,
    EventSink,
    StreamSink,
    ConsoleSink,
)
from duui_py.logging.streaming import router as events_router
from duui_py.models import AnnotatorConfig, DuuiDocument, DuuiResult
from duui_py.settings import set_settings_once
from duui_py.utils.mime import matches_mime_type

RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")


def _validate_lua_communication_layer(codec: Codec[Any, Any]) -> None:
    content = codec.communication_layer_content()
    format_value = str(content.get("format", "")).lower()
    spec_value = content.get("spec")
    if format_value != "lua" or not isinstance(spec_value, str) or not spec_value.strip():
        raise RuntimeError(
            "Invalid codec communication layer: only Lua script communication layers are supported "
            "(expected {'format': 'lua', 'spec': '<non-empty string>'})."
        )


def _is_async_iterable(value: object) -> bool:
    return hasattr(value, "__aiter__")


async def _maybe_await(value: object) -> object:
    if inspect.isawaitable(value):
        return await value
    return value


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


def _merge_documents(base: DuuiDocument, chunk: DuuiDocument) -> DuuiDocument:
    if chunk.parameters:
        merged_parameters = dict(base.parameters)
        merged_parameters.update(chunk.parameters)
        base.parameters = merged_parameters
    if chunk.view:
        base.view = chunk.view
    if chunk.sofa is not None:
        base.sofa = chunk.sofa
    if chunk.fs:
        base.fs.extend(chunk.fs)
    return base


class ProcessingMode(str, Enum):
    NORMAL = "normal"
    STREAMING = "streaming"


def _determine_processing_mode(codec: Codec[Any, Any], annotator: DuuiAnnotator[Any, Any]) -> ProcessingMode:
    del annotator
    codec_streaming = isinstance(codec, StreamingRequestDecoder) and isinstance(codec, StreamingResponseEncoder)
    if codec_streaming:
        return ProcessingMode.STREAMING
    return ProcessingMode.NORMAL


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
    validation = settings.validation
    limits = settings.limits
    errors = settings.errors
    logging_settings = settings.logging
    codec: Codec[RequestT, ResponseT] = annotator.codec()
    _validate_lua_communication_layer(codec)
    process_mode = _determine_processing_mode(codec, annotator)

    app = FastAPI(title=cfg.descriptor.name, version=cfg.descriptor.version)
    typesystem_xml = open(cfg.typesystem_xml_path, "rb").read()
    logger = None

    # Define the core endpoints first
    @app.get("/v1/typesystem")
    def get_typesystem() -> Response:
        return Response(content=typesystem_xml, media_type="application/xml")

    @app.get("/v1/communication_layer")
    def get_communication_layer() -> JSONResponse:
        return JSONResponse(content=codec.communication_layer_content(), media_type="application/json")

    @app.get("/v1/details/input_output")
    def get_input_output() -> dict[str, Any]:
        d = cfg.descriptor
        return {
            "name": d.name,
            "version": d.version,
            "input": d.input.model_dump(),
            "output": d.output.model_dump(),
        }

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
                decoded_input = await codec.decode_request_stream(limited_body_stream())
            except Exception as exc:  # noqa: BLE001
                detail = f"request decode failed: {exc}" if errors.include_validation_details else "request decode failed"
                if errors.fail_on_codec_error:
                    raise HTTPException(status_code=400, detail=detail) from exc
                raise HTTPException(status_code=422, detail=detail) from exc

            def validate_input_doc(doc: RequestT) -> RequestT:
                if isinstance(doc, DuuiDocument):
                    expected = cfg.descriptor.input.default_mime_type()
                    if (
                        validation.strict_mime_validation
                        and validation.strict_input_mime_check
                        and not matches_mime_type(expected, doc.sofa.mimeType)
                    ):
                        raise HTTPException(
                            status_code=415,
                            detail=(
                                f"unsupported sofa.mimeType: {doc.sofa.mimeType} (expected {expected})"
                                if errors.include_validation_details
                                else "unsupported sofa.mimeType"
                            ),
                        )
                return doc

            if _is_async_iterable(decoded_input):
                async def validated_input_stream() -> AsyncIterator[RequestT]:
                    async for doc in decoded_input:  # type: ignore[assignment]
                        yield validate_input_doc(doc)
                handoff_input: RequestT | AsyncIterable[RequestT] = validated_input_stream()
            else:
                handoff_input = validate_input_doc(decoded_input)  # type: ignore[arg-type]

            async def iter_input_documents() -> AsyncIterator[DuuiDocument]:
                if _is_async_iterable(handoff_input):
                    async for item in cast(AsyncIterable[Any], handoff_input):
                        if not isinstance(item, DuuiDocument):
                            raise HTTPException(status_code=500, detail="streaming mode expects DuuiDocument input")
                        yield item
                    return
                item = cast(Any, handoff_input)
                if not isinstance(item, DuuiDocument):
                    raise HTTPException(status_code=500, detail="streaming mode expects DuuiDocument input")
                yield item

            async def assemble_full_input() -> DuuiDocument:
                base: DuuiDocument | None = None
                async for item in iter_input_documents():
                    if base is None:
                        base = DuuiDocument(
                            parameters=dict(item.parameters),
                            view=item.view,
                            sofa=item.sofa,
                            fs=list(item.fs),
                        )
                    else:
                        _merge_documents(base, item)
                if base is None:
                    raise HTTPException(status_code=400, detail="empty streaming input")
                return base

            async def processed_output_stream() -> AsyncIterator[ResponseT]:
                if isinstance(annotator, V2ProcessChunks):
                    batch_size = max(1, int(getattr(annotator, "batch_size", 1)))
                    batch: list[DuuiDocument] = []
                    params: dict[str, Any] = {}
                    async for item in iter_input_documents():
                        if item.parameters:
                            params = dict(item.parameters)
                        batch.append(item)
                        if len(batch) >= batch_size:
                            async for out in annotator.v2_process_chunks(batch, params):
                                yield cast(ResponseT, out)
                            batch = []
                    if batch:
                        async for out in annotator.v2_process_chunks(batch, params):
                            yield cast(ResponseT, out)
                    return

                full_input = await assemble_full_input()
                if isinstance(annotator, V2Process):
                    async for out in annotator.v2_process(full_input, full_input.parameters):
                        yield cast(ResponseT, out)
                    return
                if isinstance(annotator, V1Process):
                    v1_result = DuuiResult()
                    returned = await annotator.v1_process(full_input, full_input.parameters, v1_result)
                    yield cast(ResponseT, returned if returned is not None else v1_result)
                    return

                result = await annotator.process(cast(RequestT, full_input))
                yield cast(ResponseT, result)

            async def validated_result_stream() -> AsyncIterator[ResponseT]:
                expected = cfg.descriptor.output.default_mime_type()
                async for result in processed_output_stream():
                    if isinstance(result, DuuiResult) and result.sofa is not None:
                        if (
                            validation.strict_mime_validation
                            and validation.strict_output_mime_check
                            and not matches_mime_type(expected, result.sofa.mimeType)
                        ):
                            raise HTTPException(
                                status_code=500,
                                detail=(
                                    f"annotator returned unsupported output sofa.mimeType: {result.sofa.mimeType} (expected {expected})"
                                    if errors.include_validation_details
                                    else "annotator returned unsupported output sofa.mimeType"
                                ),
                            )
                    yield result

            try:
                encoded_stream = await codec.encode_response_stream(validated_result_stream())
            except Exception as exc:  # noqa: BLE001
                detail = f"response encode failed: {exc}" if errors.include_validation_details else "response encode failed"
                if errors.fail_on_codec_error:
                    raise HTTPException(status_code=500, detail=detail) from exc
                raise HTTPException(status_code=422, detail=detail) from exc

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
            doc: RequestT = codec.decode_request(body)
        except Exception as exc:  # noqa: BLE001
            detail = f"request decode failed: {exc}" if errors.include_validation_details else "request decode failed"
            if errors.fail_on_codec_error:
                raise HTTPException(status_code=400, detail=detail) from exc
            raise HTTPException(status_code=422, detail=detail) from exc

        if isinstance(doc, DuuiDocument):
            expected = cfg.descriptor.input.default_mime_type()
            if validation.strict_mime_validation and validation.strict_input_mime_check and not matches_mime_type(expected, doc.sofa.mimeType):
                raise HTTPException(
                    status_code=415,
                    detail=(
                        f"unsupported sofa.mimeType: {doc.sofa.mimeType} (expected {expected})"
                        if errors.include_validation_details
                        else "unsupported sofa.mimeType"
                    ),
                )

        try:
            if isinstance(doc, DuuiDocument) and isinstance(annotator, V1Process):
                v1_result = DuuiResult()
                returned = await annotator.v1_process(doc, doc.parameters, v1_result)
                result = cast(ResponseT, returned if returned is not None else v1_result)
            elif isinstance(doc, DuuiDocument) and isinstance(annotator, V2Process):
                merged = DuuiResult()
                async for partial in annotator.v2_process(doc, doc.parameters):
                    _merge_results(merged, partial)
                result = cast(ResponseT, merged)
            else:
                result = await annotator.process(doc)
        except Exception as exc:  # noqa: BLE001
            if logger is not None:
                await logger.error(f"Process request failed with unexpected error: {exc}")
            raise

        if isinstance(result, DuuiResult) and result.sofa is not None:
            expected = cfg.descriptor.output.default_mime_type()
            if validation.strict_mime_validation and validation.strict_output_mime_check and not matches_mime_type(expected, result.sofa.mimeType):
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"annotator returned unsupported output sofa.mimeType: {result.sofa.mimeType} (expected {expected})"
                        if errors.include_validation_details
                        else "annotator returned unsupported output sofa.mimeType"
                    ),
                )

        try:
            response_body = codec.encode_response(result)
        except Exception as exc:  # noqa: BLE001
            detail = f"response encode failed: {exc}" if errors.include_validation_details else "response encode failed"
            if errors.fail_on_codec_error:
                raise HTTPException(status_code=500, detail=detail) from exc
            raise HTTPException(status_code=422, detail=detail) from exc

        if limits.response_max_bytes is not None and len(response_body) > limits.response_max_bytes:
            raise HTTPException(status_code=500, detail="response payload too large")

        response = Response(content=response_body, media_type=codec.response_media_type)
        if logger is not None:
            await logger.info("Process request completed successfully")
        return response

    # Configure logging if enabled
    if logging_settings.enabled:
        # Configure stream manager
        stream_manager = configure_stream_manager(
            default_ttl_minutes=logging_settings.stream_timeout_minutes
        )
        
        # Create sinks - use typing.cast to help type checker
        from typing import List as TypingList
        sinks: TypingList[EventSink] = [cast(EventSink, StreamSink(stream_manager))]
        # Add console sink for debugging in development
        import os
        if os.environ.get("DUUI_DEBUG_LOGGING"):
            sinks.append(cast(EventSink, ConsoleSink()))
        
        # Configure logger
        configure_logger(
            sinks=sinks,
            default_context={
                "annotator_name": cfg.descriptor.name,
                "annotator_version": cfg.descriptor.version,
            },
            annotator_descriptor=cfg.descriptor,
            start_background_worker=True,
        )
        
        # Configure metric collector
        configure_metric_collector(
            collection_interval_seconds=logging_settings.metrics_collection_interval_seconds,
            include_process_metrics=logging_settings.include_process_metrics,
            include_system_metrics=logging_settings.include_system_metrics,
            include_disk_metrics=logging_settings.include_disk_metrics,
            include_network_metrics=logging_settings.include_network_metrics,
            start_immediately=True,
        )
        
        # Add event streaming endpoints
        app.include_router(events_router)
        
        # Add middleware for event context
        @app.middleware("http")
        async def event_context_middleware(request: Request, call_next):
            # Extract event-context query parameter
            event_context_param = request.query_params.get("event-context")
            
            # Create event context
            event_context = create_event_context_from_request(
                event_context_param=event_context_param,
                request_id=request.headers.get("x-request-id"),
            )
            
            # Set context for this request
            set_event_context(event_context)
            
            try:
                response = await call_next(request)
                return response
            finally:
                # Clear context after request
                clear_event_context()
        
        # Set logger for core endpoint lifecycle messages
        logger = get_event_logger()

    return app
