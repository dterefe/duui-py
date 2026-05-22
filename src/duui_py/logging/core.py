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
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


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

    def __init__(self, endpoint: str, headers: Optional[Dict[str, str]] = None, timeout_seconds: float = 2.0):
        self.endpoint = endpoint
        self.headers = headers or {}
        self.timeout_seconds = timeout_seconds

    async def send(self, event: AnyEvent) -> None:
        payload = event.model_dump_json().encode("utf-8")

        def post() -> None:
            request = urllib.request.Request(
                self.endpoint,
                data=payload,
                headers={"Content-Type": "application/json", **self.headers},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
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
    
    async def _enqueue_event(self, event: AnyEvent) -> None:
        """Enqueue an event for async processing."""
        if self._queue is None:
            # If not started, send synchronously
            await self._send_event(event)
        else:
            try:
                self._queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest event to make room
                try:
                    self._queue.get_nowait()
                    self._queue.put_nowait(event)
                except asyncio.QueueEmpty:
                    pass  # Should not happen
    
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

    async def emit(self, event: AnyEvent) -> None:
        await self._enqueue_event(event)
    
    async def log(
        self,
        level: LogLevel,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a message with the specified level."""
        trace_id, span_id = self._trace_context()
        event = LogEvent(
            severity_text=level.value,
            severity_number=_severity_number(level),
            body=message,
            attributes={**self._build_event_context(), **(extra or {})},
            scope=self._scope(),
            trace_id=trace_id,
            span_id=span_id,
        )
        await self._enqueue_event(event)
    
    async def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug message."""
        await self.log(LogLevel.DEBUG, message, extra)
    
    async def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log an info message."""
        await self.log(LogLevel.INFO, message, extra)
    
    async def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a warning message."""
        await self.log(LogLevel.WARNING, message, extra)
    
    async def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log an error message."""
        await self.log(LogLevel.ERROR, message, extra)
    
    async def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log a critical message."""
        await self.log(LogLevel.CRITICAL, message, extra)
    
    async def metric(
        self,
        category: str,
        name: str,
        value: float,
        unit: str,
        interval_ms: int = 0,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """Log a metric."""
        trace_id, span_id = self._trace_context()
        attributes = {**self._build_event_context(), **(tags or {}), "duui.metric.category": category}
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
        await self._enqueue_event(event)

    async def histogram(
        self,
        category: str,
        name: str,
        histogram: Dict[str, Any],
        unit: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        trace_id, span_id = self._trace_context()
        attributes = {**self._build_event_context(), **(tags or {}), "duui.metric.category": category}
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
        await self._enqueue_event(event)
    
    async def error_event(
        self,
        error_type: str,
        message: str,
        stack_trace: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a structured error event."""
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
        await self._enqueue_event(event)

    async def span(
        self,
        *,
        name: str,
        start_time_unix_nano: int,
        end_time_unix_nano: int,
        status_code: int,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        trace_id, span_id = self._trace_context()
        await self._enqueue_event(
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

    async def summary(self, *, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        trace_id, span_id = self._trace_context()
        await self._enqueue_event(
            SummaryEvent(
                name=name,
                attributes={**self._build_event_context(), **(attributes or {})},
                scope=self._scope(),
                trace_id=trace_id,
                span_id=span_id,
            )
        )


def _severity_number(level: LogLevel) -> int:
    return {
        LogLevel.DEBUG: 5,
        LogLevel.INFO: 9,
        LogLevel.WARNING: 13,
        LogLevel.ERROR: 17,
        LogLevel.CRITICAL: 21,
    }[level]


# Global logger instance
_logger_instance: Optional[EventLogger] = None
_logger_context: ContextVar[Optional[EventLogger]] = ContextVar("event_logger", default=None)


def get_event_logger() -> EventLogger:
    """Get the global event logger instance."""
    global _logger_instance
    if _logger_instance is None:
        raise RuntimeError("Event logger not configured. Call configure_logger() first.")
    return _logger_instance


def get_event_logger_or_none() -> Optional[EventLogger]:
    """Get the global event logger instance when logging is configured."""
    return _logger_instance


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
