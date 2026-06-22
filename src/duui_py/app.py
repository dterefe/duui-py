from __future__ import annotations

from collections.abc import AsyncIterator
import inspect
from pathlib import Path
import sys

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from typing import Any, TypeVar, cast

from duui_py.adapters import RequestAdapter, _invoke_v1, default_request_adapter
from duui_py.annotator import DuuiAnnotator
from duui_py.codecs.base import Codec
from duui_py.logging import (
    clear_event_context,
    configure_logger,
    configure_metric_collector,
    configure_stream_manager,
    create_event_context_from_request,
    set_event_context,
    EventSink,
    ConsoleSink,
    StreamSink,
    logger,
)
from duui_py.models import AnnotatorConfig
from duui_py.settings import set_settings_once
from duui_py.telemetry import create_stream_identifiers_from_request

RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")

EMPTY_TYPESYSTEM_XML = (
    b"<typeSystemDescription xmlns='http://uima.apache.org/resourceSpecifier'>"
    b"<types/></typeSystemDescription>"
)


def _validate_lua_communication_layer(codec: Codec[Any, Any]) -> None:
    content = codec.communication_layer_content()
    if (
        str(content.get("format", "")).lower() != "lua"
        or not str(content.get("spec", "")).strip()
    ):
        raise RuntimeError(
            "Invalid codec communication layer: expected non-empty Lua script"
        )


def _load_typesystem_xml(path: str, annotator_cls: type[Any]) -> bytes:
    resolved = _resolve_typesystem_path(path, annotator_cls)
    if resolved is not None:
        return resolved.read_bytes()
    return EMPTY_TYPESYSTEM_XML


def _resolve_typesystem_path(path: str, annotator_cls: type[Any]) -> Path | None:
    candidates = [Path(path)]
    module = sys.modules.get(annotator_cls.__module__)
    module_file = getattr(module, "__file__", None)
    if module_file and not Path(path).is_absolute():
        candidates.append(Path(module_file).resolve().parent / path)

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def create_app(
    annotator_cls: type[DuuiAnnotator[RequestT, ResponseT]],
    *,
    config_path: str | None = None,
    config: AnnotatorConfig | None = None,
    request_adapter: RequestAdapter[RequestT, ResponseT] | None = None,
) -> FastAPI:
    annotator = annotator_cls(config_path=config_path, config=config)
    cfg = annotator.config
    resolved_typesystem_path = _resolve_typesystem_path(cfg.typesystem_xml_path, annotator_cls)
    if resolved_typesystem_path is not None:
        cfg = cfg.model_copy(update={"typesystem_xml_path": str(resolved_typesystem_path)})
        annotator.config = cfg
    set_settings_once(cfg.meta.settings)

    settings = cfg.meta.settings
    codec: Codec[RequestT, ResponseT] = annotator.codec()
    _validate_lua_communication_layer(codec)
    adapter = request_adapter or cast(
        RequestAdapter[RequestT, ResponseT], default_request_adapter(codec)
    )

    app = FastAPI(title=cfg.descriptor.name, version=cfg.descriptor.version)
    app.state.request_adapter = adapter
    app.state.codec = codec
    app.state.annotator = annotator
    typesystem_xml = _load_typesystem_xml(cfg.typesystem_xml_path, annotator_cls)
    telemetry_service = None

    async def _invoke_optional_lifecycle(name: str) -> None:
        hook = getattr(annotator, name, None)
        if not callable(hook):
            return
        result = hook()
        if inspect.isawaitable(result):
            await result

    @app.get("/v1/typesystem")
    def get_typesystem() -> Response:
        return Response(content=typesystem_xml, media_type="application/xml")

    @app.get("/v1/communication_layer")
    def get_communication_layer() -> Response:
        return Response(
            content=str(codec.communication_layer_content()["spec"]),
            media_type="text/plain; charset=utf-8",
        )

    @app.get("/v1/details/input_output")
    def get_input_output() -> dict[str, Any]:
        d = cfg.descriptor
        return {
            "name": d.name,
            "version": d.version,
            "input": d.input.model_dump(),
            "output": d.output.model_dump(),
            "parameters": d.parameters,
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
            "parameters": d.parameters,
        }

    @app.post("/v1/process")
    async def post_process(request: Request) -> Response:
        if not settings.logging.enabled:
            return await adapter.handle(request, annotator, codec, cfg)

        logger().trace("Process request accepted", path=str(request.url.path))
        try:
            response = await adapter.handle(request, annotator, codec, cfg)
        except Exception as exc:
            logger().critical(
                "Process request failed before response",
                exception=type(exc).__name__,
                path=str(request.url.path),
            )
            raise
        logger().debug("Process response prepared", path=str(request.url.path))
        return response

    @app.on_event("startup")
    async def start_annotator() -> None:
        if telemetry_service is not None:
            telemetry_service.start()
        await _invoke_optional_lifecycle("startup")

    @app.on_event("shutdown")
    async def stop_annotator() -> None:
        await _invoke_optional_lifecycle("shutdown")

    logging_settings = settings.logging
    if logging_settings.enabled:
        stream_manager = configure_stream_manager(
            default_ttl_minutes=logging_settings.stream_timeout_minutes,
            max_queue_size=logging_settings.max_queue_size,
        )
        sinks: list[EventSink] = [
            cast(EventSink, StreamSink(stream_manager)),
            cast(EventSink, ConsoleSink()),
        ]

        telemetry_service = configure_logger(
            sinks=sinks,
            default_context={
                "annotator_name": cfg.descriptor.name,
                "annotator_version": cfg.descriptor.version,
            },
            annotator_descriptor=cfg.descriptor,
            start_background_worker=False,
        )

        metric_collector = configure_metric_collector(
            collection_interval_seconds=logging_settings.metrics_collection_interval_seconds,
            include_process_metrics=logging_settings.include_process_metrics,
            include_system_metrics=logging_settings.include_system_metrics,
            include_disk_metrics=logging_settings.include_disk_metrics,
            include_network_metrics=logging_settings.include_network_metrics,
            start_immediately=False,
        )

        @app.on_event("startup")
        async def start_observability() -> None:
            telemetry_service.start()
            metric_collector.start()

        @app.on_event("shutdown")
        async def stop_observability() -> None:
            await metric_collector.stop()
            await telemetry_service.stop()
            await stream_manager.stop()

        @app.get("/v2/events")
        async def stream_events(request: Request) -> StreamingResponse:
            identifiers = create_stream_identifiers_from_request(request)
            ttl_param = request.query_params.get("ttl_minutes")
            ttl_minutes = (
                int(ttl_param) if ttl_param else logging_settings.stream_timeout_minutes
            )
            stream = await stream_manager.open_stream(
                identifiers=identifiers, ttl_minutes=ttl_minutes
            )

            async def event_generator() -> AsyncIterator[bytes]:
                try:
                    async for event in stream.events():
                        yield event
                finally:
                    await stream_manager.remove_stream(stream.stream_id)

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        @app.middleware("http")
        async def event_context_middleware(request: Request, call_next):
            event_context_param = request.query_params.get("event-context")
            event_context = create_event_context_from_request(
                request,
                event_context_param=event_context_param,
                request_id=request.headers.get("x-request-id"),
            )
            set_event_context(event_context)
            try:
                return await call_next(request)
            finally:
                clear_event_context()

    return app
