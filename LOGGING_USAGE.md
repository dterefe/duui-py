# DUUI Python Framework - Logging Module

## Overview

A comprehensive logging, metrics, and error reporting system with real-time event streaming via Server-Sent Events (SSE).

## Features

- **Event Context Management**: Request-scoped logging with flexible identifiers
- **Log Events**: Standard log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Metric Events**: Resource metrics (CPU, memory, disk, network) with time spans
- **Error Events**: Structured error reporting with stack traces and recovery suggestions
- **Real-time Streaming**: SSE endpoint `/v2/events` for live event streaming
- **Error Handling**: Decorators and context managers for clean error reporting
- **System Metrics**: Automatic collection of system/process metrics

## Quick Start

### 1. Basic Setup in Annotator

```python
from duui_py.annotator import DuuiAnnotator
from duui_py.logging import (
    get_event_logger, 
    configure_logger,
    StreamSink,
    ConsoleSink,
    configure_stream_manager,
    EventContext,
    create_event_context_from_request
)

class MyAnnotator(DuuiAnnotator):
    def __init__(self, config_path: str | None = None, config: dict | None = None):
        super().__init__(config_path, config)
        
        # Configure logging
        stream_manager = configure_stream_manager(default_ttl_minutes=5)
        stream_sink = StreamSink(stream_manager)
        console_sink = ConsoleSink()  # For debugging
        
        configure_logger(
            sinks=[stream_sink, console_sink],
            default_context={"annotator": self.config.descriptor.name},
            annotator_descriptor=self.config.descriptor,
            start_background_worker=True
        )
        
        self.logger = get_event_logger()
```

### 2. Using Logging in Process Method

```python
async def process(self, doc):
    # Set request context from event-context parameter
    event_context_param = self.request.headers.get("x-event-context", "")
    context = create_event_context_from_request(
        event_context_param=event_context_param,
        request_id=self.request.id,
        artifact_id=doc.id
    )
    
    await self.logger.info(f"Processing document {doc.id}")
    
    try:
        # Your processing logic
        result = await self._process_document(doc)
        
        # Log metrics
        await self.logger.metric(
            category="cpu",
            name="cpu_percent",
            value=45.5,
            unit="percent",
            interval_ms=1000
        )
        
        return result
        
    except Exception as e:
        await self.logger.error_event(
            error_type=type(e).__name__,
            message=str(e),
            stack_trace=traceback.format_exc(),
            recovery_suggestion="Check input format"
        )
        raise
```

### 3. Error Handling Decorators

```python
from duui_py.logging import log_errors, error_context

@log_errors(log_level="ERROR", recovery_suggestion="Retry with valid input")
async def process_document(doc):
    # Function automatically logs any exceptions
    ...

# Context manager for error handling
def process_with_context(doc):
    with error_context("document_processing", recovery_suggestion="Check document format"):
        # Any exception here gets logged
        result = process_doc(doc)
        return result
```

## Event Streaming (SSE)

### Client Setup

```javascript
// JavaScript client
const eventSource = new EventSource('/v2/events?identifiers=annotator=my-annotator,replica=replica-1');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received event:', data);
};

// Register a stream with custom TTL
fetch('/v2/events/register', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        identifiers: {
            annotator_id: 'my-annotator',
            replica_id: 'replica-1',
            application_id: 'my-app'
        },
        ttl_minutes: 10,
        client_info: {
            user_agent: 'MyClient/1.0',
            remote_addr: '192.168.1.1'
        }
    })
});
```

### Python Client

```python
import sseclient
import requests

# Register stream first
response = requests.post(
    'http://localhost:8000/v2/events/register',
    json={
        'identifiers': {'annotator_id': 'test-annotator', 'replica_id': 'replica-1'},
        'ttl_minutes': 5
    }
)
stream_id = response.json()['stream_id']

# Connect to SSE stream
messages = sseclient.SSEClient(
    f'http://localhost:8000/v2/events/stream/{stream_id}'
)

for msg in messages:
    event = json.loads(msg.data)
    print(f"Event: {event['type']} - {event.get('message', '')}")
```

## Event Context Parameters

The `event-context` parameter can be passed as a query parameter or header:

```
# Query parameter format
/v1/process?event-context=annotator=my-annotator,artifact=doc123,replica=replica-1

# Or as header
X-Event-Context: annotator=my-annotator,artifact=doc123,replica=replica-1,application=my-app
```

Supported identifiers:
- `annotator`: Annotator ID
- `artifact`: Document/artifact ID  
- `replica`: Replica ID (for load balancing)
- `application`: Application ID
- `request_id`: Request ID (can also come from headers)

## Metrics Collection

### System Metrics (Automatic)

The `MetricCollector` automatically collects:
- CPU usage (percent)
- Memory usage (RSS, virtual)
- Disk I/O (read/write bytes)
- Network I/O (sent/received bytes)
- Process metrics (threads, file descriptors)

```python
from duui_py.logging import configure_metric_collector, get_metric_collector

# Configure automatic metrics collection
collector = configure_metric_collector(
    interval_seconds=5,  # Collect every 5 seconds
    include_system_metrics=True,
    include_process_metrics=True,
    include_disk_metrics=True,
    include_network_metrics=True
)

# Start collection
collector.start()
```

### Custom Metrics

```python
await logger.metric(
    category="custom",
    name="processing_time",
    value=125.5,
    unit="milliseconds",
    interval_ms=1000,
    tags={"operation": "document_processing"}
)
```

## Configuration

### Annotator Config Settings

```json
{
  "meta": {
    "settings": {
      "logging": {
        "enabled": true,
        "stream_timeout_minutes": 5,
        "max_queue_size": 1000,
        "metrics_collection_interval_seconds": 5,
        "include_system_metrics": true,
        "include_process_metrics": true,
        "include_disk_metrics": true,
        "include_network_metrics": true
      }
    }
  }
}
```

### Environment Variables

```
DUUI_LOGGING_ENABLED=true
DUUI_STREAM_TIMEOUT_MINUTES=5
DUUI_METRICS_INTERVAL_SECONDS=5
```

## API Endpoints

### `/v2/events/register` (POST)
Register a new event stream.

**Request:**
```json
{
  "identifiers": {
    "annotator_id": "my-annotator",
    "replica_id": "replica-1",
    "application_id": "my-app"
  },
  "ttl_minutes": 5,
  "client_info": {
    "user_agent": "MyClient/1.0",
    "remote_addr": "192.168.1.1"
  }
}
```

**Response:**
```json
{
  "stream_id": "uuid-here",
  "expires_at": "2024-01-01T12:00:00Z",
  "stream_url": "/v2/events/stream/uuid-here"
}
```

### `/v2/events/stream/{stream_id}` (GET)
SSE stream for receiving events.

### `/v2/events/list` (GET)
List active streams.

### `/v2/events/{stream_id}/info` (GET)
Get stream information.

## Architecture Notes

### Stream Isolation
- Each application gets separate streams
- Within an application, streams are separated by annotator ID
- Within an annotator, streams can be separated by replica ID
- This allows for Kubernetes/Swarm deployments with multiple replicas

### Concurrency Safety
- StreamManager is thread-safe and async-safe
- Multiple concurrent streams are supported
- Stream registration uses atomic operations

### Network Considerations
- Works behind university firewalls (SSE over HTTP)
- Supports containerized deployments
- Handles network interruptions with stream timeouts

## Troubleshooting

### Import Issues
If you encounter recursion errors, ensure type aliases don't have circular references:
- Use `Any` instead of recursive types temporarily
- Consider PEP 695 type aliases for production

### Stream Not Receiving Events
1. Check stream registration was successful
2. Verify identifiers match the context being logged
3. Check stream hasn't expired (default TTL: 5 minutes)
4. Ensure client is properly handling SSE connection

### Performance
- Events are queued asynchronously
- Background worker processes events
- Queue size is configurable (default: 1000 events)
- Old events are dropped when queue is full