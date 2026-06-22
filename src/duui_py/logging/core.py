from __future__ import annotations

import asyncio
import json
import urllib.request
from collections.abc import AsyncIterator
from contextvars import ContextVar
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from duui_py.telemetry import host_resource_attributes, now_unix_nano

if TYPE_CHECKING:
    from duui_py.models.config import AnnotatorDescriptor
    from duui_py.logging.streaming import StreamManager
    from duui_py.logging.context import EventContext
else:
    AnnotatorDescriptor = object


class EventType(str, Enum):
    LOG = "log"
    METRIC = "metric"
    ERROR = "error"
    SPAN = "span"
    SUMMARY = "summary"


class LogLevel(str, Enum):
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    WARNING = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"
    CRITICAL = "FATAL"


class Event(BaseModel):
    """OpenTelemetry-compatible base event envelope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type: EventType
    time_unix_nano: int = Field(default_factory=now_unix_nano)
    observed_time_unix_nano: int = Field(default_factory=now_unix_nano)
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    resource: Dict[str, str] = Field(default_factory=host_resource_attributes)
    scope: Dict[str, str] = Field(default_factory=dict)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


class LogEvent(Event):
    """OpenTelemetry-compatible log record."""

    type: EventType = EventType.LOG
    severity_text: str
    severity_number: int
    body: str


class MetricEvent(Event):
    """OpenTelemetry-compatible metric record."""

    type: EventType = EventType.METRIC
    name: str
    unit: str
    metric_type: str = "gauge"
    data_points: List[Dict[str, Any]] = Field(default_factory=list)


class ErrorEvent(Event):
    """Structured error record encoded as an OpenTelemetry ERROR log."""

    type: EventType = EventType.ERROR
    severity_text: str = "ERROR"
    severity_number: int = 17
    body: str


class SpanEvent(Event):
    type: EventType = EventType.SPAN
    name: str
    start_time_unix_nano: int
    end_time_unix_nano: int
    status_code: int = 200


class SummaryEvent(Event):
    type: EventType = EventType.SUMMARY
    name: str


# Type alias for any event
AnyEvent = Union[LogEvent, MetricEvent, ErrorEvent, SpanEvent, SummaryEvent]


class EventSink:
    """Abstract base class for event sinks."""

    async def send(self, event: AnyEvent) -> None:
        """Send an event to the sink."""
        raise NotImplementedError

    async def close(self) -> None:
        """Close the sink and release resources."""
        pass


class StreamSink(EventSink):
    """Sink that sends events to active streams."""

    def __init__(self, stream_manager: StreamManager):
        self.stream_manager = stream_manager

    def has_consumers(self) -> bool:
        return self.stream_manager.has_streams()

    async def send(self, event: AnyEvent) -> None:
        """Send event to all active streams."""
        await self.stream_manager.broadcast_event(event)


class ConsoleSink(EventSink):
    """Sink that prints events to console (for debugging)."""

    async def send(self, event: AnyEvent) -> None:
        """Print event to console."""
        print(f"{event.type.value}: {event.model_dump_json()}")


class OTLPSink(EventSink):
    """Dependency-free OTLP/HTTP JSON sink for DUUI telemetry events."""

    def __init__(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: float = 2.0,
    ):
        self.endpoint = endpoint
        self.headers = headers or {}
        self.timeout_seconds = timeout_seconds

    async def send(self, event: AnyEvent) -> None:
        payload = event.model_dump_json().encode("utf-8")

        def post() -> None:
            request = urllib.request.Request(
                self.endpoint,
                data=payload,
                headers=self.headers,
                method="POST",
            )
            with urllib.request.urlopen(
                request, timeout=self.timeout_seconds
            ) as response:
                response.read()

        await asyncio.to_thread(post)


class EventLogger:
    """Central logging class for handling events."""

    def __init__(
        self,
        sinks: Optional[List[EventSink]] = None,
        default_context: Optional[Dict[str, str]] = None,
        annotator_descriptor: Optional[AnnotatorDescriptor] = None,
    ):
        self.sinks = sinks or []
        self.default_context = default_context or {}
        self.annotator_descriptor = annotator_descriptor
        self._queue: Optional[asyncio.Queue] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._dropped_events = 0

    def has_active_sinks(self) -> bool:
        if not self.sinks:
            return False
        for sink in self.sinks:
            has_consumers = getattr(sink, "has_consumers", None)
            if not callable(has_consumers):
                return True
            try:
                if has_consumers():
                    return True
            except Exception:
                return True
        return False

    def start(self) -> None:
        """Start the background worker for async event processing."""
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=1000)
            self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self) -> None:
        """Stop the background worker and wait for completion."""
        if self._queue is not None:
            await self._queue.put(None)  # Sentinel to stop worker
            if self._worker_task:
                await self._worker_task
            self._queue = None
            self._worker_task = None

    async def _worker_loop(self) -> None:
        """Background worker that processes events from the queue."""
        if self._queue is None:
            return

        while True:
            event = await self._queue.get()
            if event is None:  # Sentinel to stop
                break

            try:
                await self._send_event(event)
            except Exception as e:
                # Log but don't crash worker
                print(f"Error sending event: {e}")
            finally:
                self._queue.task_done()

    async def _send_event(self, event: AnyEvent) -> None:
        """Send event to all sinks."""
        for sink in self.sinks:
            try:
                await sink.send(event)
            except Exception as e:
                print(f"Error in sink {sink.__class__.__name__}: {e}")

    def _enqueue_event(self, event: AnyEvent) -> None:
        """Enqueue an event for async processing."""
        if not self.has_active_sinks():
            return
        if self._queue is None:
            self._dropped_events += 1
            return
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            try:
                self._queue.get_nowait()
                self._queue.task_done()
                self._queue.put_nowait(event)
                self._dropped_events += 1
            except asyncio.QueueEmpty:
                self._dropped_events += 1

    def _build_event_context(self) -> Dict[str, str]:
        """Build context from default context and current event context."""
        from duui_py.logging.context import get_event_context

        context = self.default_context.copy()

        # Add current request context if available
        event_context = get_event_context()
        if event_context:
            context.update(event_context.context)
            context.update(event_context.otel_attributes())

        return context

    def _build_annotator_config(self) -> Optional[Dict[str, str]]:
        """Build annotator config info from descriptor."""
        if not self.annotator_descriptor:
            return None

        return {
            "name": self.annotator_descriptor.name,
            "version": self.annotator_descriptor.version,
        }

    def _trace_context(self) -> tuple[str | None, str | None]:
        from duui_py.logging.context import get_event_context

        context = get_event_context()
        if context is None:
            return None, None
        return context.trace_id, context.span_id

    def _scope(self) -> dict[str, str]:
        return {"name": "duui-py", "version": "0.1.0"}

    def _log_body(self, message: str, attributes: Dict[str, Any]) -> str:
        if not attributes:
            return message
        return f"{message} {json.dumps(_jsonable(attributes), sort_keys=True, separators=(',', ':'))}"

    def emit(self, event: AnyEvent) -> None:
        self._enqueue_event(event)

    def log(
        self,
        level: LogLevel,
        message: str,
        **attributes: Any,
    ) -> None:
        """Log a message with the specified level."""
        if not self.has_active_sinks():
            return
        trace_id, span_id = self._trace_context()
        event = LogEvent(
            severity_text=level.value,
            severity_number=_severity_number(level),
            body=self._log_body(message, attributes),
            attributes=self._build_event_context(),
            scope=self._scope(),
            trace_id=trace_id,
            span_id=span_id,
        )
        self._enqueue_event(event)

    def debug(self, message: str, **attributes: Any) -> None:
        """Log a debug message."""
        self.log(LogLevel.DEBUG, message, **attributes)

    def trace(self, message: str, **attributes: Any) -> None:
        """Log a trace message."""
        self.log(LogLevel.TRACE, message, **attributes)

    def info(self, message: str, **attributes: Any) -> None:
        """Log an info message."""
        self.log(LogLevel.INFO, message, **attributes)

    def warning(self, message: str, **attributes: Any) -> None:
        """Log a warning message."""
        self.warn(message, **attributes)

    def warn(self, message: str, **attributes: Any) -> None:
        """Log a warning message."""
        self.log(LogLevel.WARN, message, **attributes)

    def error(self, message: str, **attributes: Any) -> None:
        """Log an error message."""
        self.log(LogLevel.ERROR, message, **attributes)

    def critical(self, message: str, **attributes: Any) -> None:
        """Log a critical message."""
        self.fatal(message, **attributes)

    def fatal(self, message: str, **attributes: Any) -> None:
        """Log a fatal message."""
        self.log(LogLevel.FATAL, message, **attributes)

    def trace_backend_operation(
        self,
        annotator: str,
        operation: str,
        **telemetry: Any,
    ) -> None:
        self.trace(
            "DUUI annotator backend operation",
            annotator=annotator,
            operation=operation,
            **telemetry,
        )

    def trace_annotation_result(
        self,
        annotator: str,
        annotations: Any,
        *,
        counts: Dict[str, Any] | None = None,
        **metadata: Any,
    ) -> None:
        self.trace(
            "DUUI annotation results",
            annotator=annotator,
            annotation_count=_count_items(annotations),
            annotation_counts=counts or {},
            annotations=_jsonable(annotations),
            **metadata,
        )

    def debug_annotation_count(
        self,
        annotator: str,
        count: int,
        *,
        counts: Dict[str, Any] | None = None,
        **metadata: Any,
    ) -> None:
        self.debug(
            "DUUI annotation result count",
            annotator=annotator,
            annotation_count=count,
            annotation_counts=counts or {},
            **metadata,
        )

    def metric(
        self,
        category: str,
        name: str,
        value: float,
        unit: str,
        interval_ms: int = 0,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Log a metric."""
        if not self.has_active_sinks():
            return
        trace_id, span_id = self._trace_context()
        attributes = {
            **self._build_event_context(),
            **(tags or {}),
            "duui.metric.category": category,
        }
        event = MetricEvent(
            name=name,
            unit=unit,
            metric_type="sum" if unit == "count" else "gauge",
            data_points=[
                {
                    "time_unix_nano": now_unix_nano(),
                    "as_double": float(value),
                    "attributes": attributes,
                    "interval_ms": interval_ms,
                }
            ],
            attributes=attributes,
            scope=self._scope(),
            trace_id=trace_id,
            span_id=span_id,
        )
        self._enqueue_event(event)

    def histogram(
        self,
        category: str,
        name: str,
        histogram: Dict[str, Any],
        unit: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        if not self.has_active_sinks():
            return
        trace_id, span_id = self._trace_context()
        attributes = {
            **self._build_event_context(),
            **(tags or {}),
            "duui.metric.category": category,
        }
        event = MetricEvent(
            name=name,
            unit=unit,
            metric_type="histogram",
            data_points=[
                {
                    "time_unix_nano": now_unix_nano(),
                    "attributes": attributes,
                    **histogram,
                }
            ],
            attributes=attributes,
            scope=self._scope(),
            trace_id=trace_id,
            span_id=span_id,
        )
        self._enqueue_event(event)

    def error_event(
        self,
        error_type: str,
        message: str,
        stack_trace: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a structured error event."""
        if not self.has_active_sinks():
            return
        trace_id, span_id = self._trace_context()
        attributes = {
            **self._build_event_context(),
            **(extra or {}),
            "exception.type": error_type,
        }
        if stack_trace is not None:
            attributes["exception.stacktrace"] = stack_trace
        event = ErrorEvent(
            body=message,
            attributes=attributes,
            scope=self._scope(),
            trace_id=trace_id,
            span_id=span_id,
        )
        self._enqueue_event(event)

    def span(
        self,
        *,
        name: str,
        start_time_unix_nano: int,
        end_time_unix_nano: int,
        status_code: int,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.has_active_sinks():
            return
        trace_id, span_id = self._trace_context()
        self._enqueue_event(
            SpanEvent(
                name=name,
                start_time_unix_nano=start_time_unix_nano,
                end_time_unix_nano=end_time_unix_nano,
                status_code=status_code,
                attributes={**self._build_event_context(), **(attributes or {})},
                scope=self._scope(),
                trace_id=trace_id,
                span_id=span_id,
            )
        )

    def summary(
        self, *, name: str, attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        if not self.has_active_sinks():
            return
        trace_id, span_id = self._trace_context()
        self._enqueue_event(
            SummaryEvent(
                name=name,
                attributes={**self._build_event_context(), **(attributes or {})},
                scope=self._scope(),
                trace_id=trace_id,
                span_id=span_id,
            )
        )

    def lifecycle(
        self,
        event: str,
        *,
        status: str | None = None,
        phase_gid: str | None = None,
        domain: str | None = None,
        state: str | None = None,
        duration_ms: int | float | None = None,
        resource: Dict[str, str] | None = None,
        failure: BaseException | None = None,
        **attributes: Any,
    ) -> None:
        payload: dict[str, Any] = {
            "duui.phase.event": event,
            **attributes,
        }
        if status is not None:
            payload["duui.phase.status"] = status
        if phase_gid is not None:
            payload["duui.phase.gid"] = phase_gid
        if domain is not None:
            payload["duui.phase.domain"] = domain
        if state is not None:
            payload["duui.phase.state"] = state
        if duration_ms is not None:
            payload["duui.phase.duration.ms"] = duration_ms
        if failure is not None:
            payload["duui.failure.type"] = type(failure).__name__
            payload["duui.failure.message"] = str(failure)
        self.event(
            name=f"duui.phase.{event.lower()}",
            kind="lifecycle",
            severity=LogLevel.ERROR if failure is not None else LogLevel.INFO,
            message=f"DUUI phase {event.lower()}" + (f" {status}" if status else ""),
            resource=resource,
            **payload,
        )

    def event(
        self,
        name: str,
        *,
        kind: str = "log",
        severity: LogLevel | str = LogLevel.INFO,
        message: str | None = None,
        resource: Dict[str, str] | None = None,
        scope: Dict[str, str] | None = None,
        **attributes: Any,
    ) -> None:
        level = severity if isinstance(severity, LogLevel) else LogLevel[str(severity).upper()]
        trace_id, span_id = self._trace_context()
        event = LogEvent(
            severity_text=level.value,
            severity_number=_severity_number(level),
            body=message or name,
            attributes={
                **self._build_event_context(),
                "event.name": name,
                "event.kind": kind,
                **_jsonable(attributes),
            },
            resource={**host_resource_attributes(), **(resource or {})},
            scope={**self._scope(), **(scope or {})},
            trace_id=trace_id,
            span_id=span_id,
        )
        self._enqueue_event(event)


def _severity_number(level: LogLevel) -> int:
    return {
        LogLevel.TRACE: 1,
        LogLevel.DEBUG: 5,
        LogLevel.INFO: 9,
        LogLevel.WARN: 13,
        LogLevel.ERROR: 17,
        LogLevel.FATAL: 21,
    }[level]


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            out[str(key)] = _jsonable(item)
        return out
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, set):
        return [_jsonable(item) for item in sorted(value, key=str)]
    if isinstance(value, bytes):
        return {"bytes": len(value)}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump(mode="json")
        except Exception:
            return str(value)
    return str(value)


def _count_items(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, dict):
        return len(value)
    if isinstance(value, (list, tuple, set)):
        return len(value)
    return 1


# Global logger instance
_logger_instance: Optional[EventLogger] = None
_logger_context: ContextVar[Optional[EventLogger]] = ContextVar(
    "event_logger", default=None
)
_noop_logger = EventLogger()


def logger() -> EventLogger:
    """Return the current DUUI-Py telemetry logger.

    This is the public logging and telemetry entrypoint. Calls enqueue events
    without awaiting sink I/O.
    """
    current = _logger_context.get()
    if current is not None:
        return current
    return _logger_instance or _noop_logger


def configure_logger(
    sinks: Optional[List[EventSink]] = None,
    default_context: Optional[Dict[str, str]] = None,
    annotator_descriptor: Optional[AnnotatorDescriptor] = None,
    start_background_worker: bool = True,
) -> EventLogger:
    """Configure the global event logger."""
    global _logger_instance

    _logger_instance = EventLogger(
        sinks=sinks,
        default_context=default_context,
        annotator_descriptor=annotator_descriptor,
    )

    if start_background_worker:
        _logger_instance.start()

    return _logger_instance
