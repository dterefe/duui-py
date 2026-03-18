from __future__ import annotations

from .core import (
    Event,
    EventType,
    LogLevel,
    LogEvent,
    MetricEvent,
    ErrorEvent,
    EventLogger,
    EventSink,
    StreamSink,
    ConsoleSink,
    get_event_logger,
    configure_logger,
)
from .context import (
    EventContext,
    get_event_context,
    set_event_context,
    clear_event_context,
    create_event_context_from_request,
    parse_event_context_param,
    update_event_context,
)
from .streaming import (
    StreamManager,
    get_stream_manager,
    configure_stream_manager,
    StreamRegistrationRequest,
    StreamRegistrationResponse,
    StreamInfo,
    router as events_router,
)
from .metrics import MetricCollector, get_metric_collector, configure_metric_collector
from .errors import log_errors, error_context, log_exception, log_error_message

__all__ = [
    # Core events and logger
    "Event",
    "EventType",
    "LogLevel",
    "LogEvent",
    "MetricEvent",
    "ErrorEvent",
    "EventLogger",
    "EventSink",
    "StreamSink",
    "ConsoleSink",
    "get_event_logger",
    "configure_logger",
    # Context management
    "EventContext",
    "get_event_context",
    "set_event_context",
    "clear_event_context",
    "create_event_context_from_request",
    "parse_event_context_param",
    "update_event_context",
    # Streaming
    "StreamManager",
    "get_stream_manager",
    "configure_stream_manager",
    "StreamRegistrationRequest",
    "StreamRegistrationResponse",
    "StreamInfo",
    "events_router",
    # Metrics
    "MetricCollector",
    "get_metric_collector",
    "configure_metric_collector",
    # Error handling
    "log_errors",
    "error_context",
    "log_exception",
    "log_error_message",
]
