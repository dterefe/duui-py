from __future__ import annotations

import asyncio
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from typing import Any, TypeVar

from duui_py.annotator import DuuiAnnotator
from duui_py.codecs.base import Codec
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

    app = FastAPI(title=cfg.descriptor.name, version=cfg.descriptor.version)
    typesystem_xml = open(cfg.typesystem_xml_path, "rb").read()

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
            "input": {
                "domain": {
                    "sofa": {"mimeType": d.input.domain.sofa.mimeType, "language": d.input.domain.sofa.language},
                    "optional_types": list(d.input.domain.optional_types),
                },
                "optional_inputs": [
                    {
                        "type": it.type,
                        "exclude": {
                            "features": list(it.exclude.features),
                            "ranges": list(it.exclude.ranges),
                            "types": list(it.exclude.types),
                        },
                    }
                    for it in d.input.optional_inputs
                ],
            },
            "output": {
                "sofa": {"mimeType": d.output.sofa.mimeType, "language": d.output.sofa.language},
                "types": list(d.output.types),
            },
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
            expected = cfg.descriptor.input.domain.sofa.mimeType
            if validation.strict_mime_validation and validation.strict_input_mime_check and not matches_mime_type(expected, doc.sofa.mimeType):
                raise HTTPException(
                    status_code=415,
                    detail=(
                        f"unsupported sofa.mimeType: {doc.sofa.mimeType} (expected {expected})"
                        if errors.include_validation_details
                        else "unsupported sofa.mimeType"
                    ),
                )

        result: ResponseT = await annotator.process(doc)

        if isinstance(result, DuuiResult) and result.sofa is not None:
            expected = cfg.descriptor.output.sofa.mimeType
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

        return Response(content=response_body, media_type=codec.response_media_type)

    # Configure logging if enabled
    if logging_settings.enabled:
        # Configure stream manager
        stream_manager = configure_stream_manager(
            default_ttl_minutes=logging_settings.stream_timeout_minutes
        )
        
        # Create sinks - use typing.cast to help type checker
        from typing import cast, List as TypingList
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
        
        # Get logger for enhancing the process endpoint
        logger = get_event_logger()
        
        # Store the original post_process function
        original_post_process = post_process
        
        # Create a new version with logging
        @app.post("/v1/process")
        async def logged_post_process(request: Request) -> Response:
            await logger.info("Process request started")
            
            try:
                response = await original_post_process(request)
                await logger.info("Process request completed successfully")
                return response
            except HTTPException as e:
                await logger.error(f"Process request failed with HTTP {e.status_code}: {e.detail}")
                raise
            except Exception as e:
                await logger.error(f"Process request failed with unexpected error: {e}")
                raise

    return app
