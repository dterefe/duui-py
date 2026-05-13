# duui-py

**Python framework for building DUUI annotators** with comprehensive logging, metrics, and real-time event streaming.

This is a standalone Python package extracted from the main DUUI-UIMA repository to provide a reusable framework for building DUUI-compatible annotators with modern Python tooling.

## Features

- **FastAPI server scaffold** with full DUUI protocol support
- **Generic codec interface** (default: DUUI-BIN v1 MessagePack codec)
- **Config-driven** `/v1/details/input_output`, `/v1/typesystem`, `/v1/documentation`
- **Strong validation** (mime types, SofA payload, config schema)
- **Comprehensive logging system** with real-time event streaming via Server-Sent Events (SSE)
- **Resource metrics collection** (CPU, memory, disk, network)
- **Structured error handling** with stack traces and recovery suggestions
- **Request-scoped logging context** for distributed tracing
- **Concurrency-safe stream management** for containerized/Kubernetes deployments

## Installation

### From source (editable install)

```bash
pip install -e /path/to/duui-py
```

### From PyPI (once published)

```bash
pip install duui-py
```

## Dependencies

Runtime dependencies (automatically installed):
- `fastapi>=0.110.0`
- `msgpack>=1.0.7`
- `pydantic>=2.6.0`
- `typing-extensions>=4.9.0`
- `psutil>=5.9.0`

Optional development dependencies:
- `uvicorn>=0.27.0`

## Quick Start

### 1. Create a config file

Start from `annotator_config.example.json`:

```json
{
  "meta": {
    "implementation_lang": "Python",
    "meta": {},
    "settings": {
      "validation": {
        "strict_mime_validation": true,
        "strict_input_mime_check": true,
        "strict_output_mime_check": true,
        "strict_sofa_data_type_validation": true,
        "strict_descriptor_mime_pattern_validation": true
      },
      "limits": {
        "request_max_bytes": null,
        "response_max_bytes": null
      },
      "errors": {
        "fail_on_codec_error": true,
        "include_validation_details": true
      },
      "logging": {
        "enabled": true,
        "stream_timeout_minutes": 5,
        "max_queue_size": 1000,
        "metrics_collection_interval_seconds": 5
      }
    }
  },
  "descriptor": {
    "name": "my-annotator",
    "version": "0.0.0",
    "input": {
      "text": {
        "default": {
          "mimeType": "text/plain; charset=utf-8",
          "languages": ["x-unspecified"],
          "types": {}
        }
      },
      "types": {}
    },
    "output": {
      "text": {
        "default": {
          "mimeType": "text/plain; charset=utf-8",
          "languages": ["x-unspecified"],
          "types": {}
        }
      },
      "types": {}
    }
  },
  "typesystem_xml_path": "TypeSystem.xml",
  "parameters_schema": {}
}
```

### 2. Implement an annotator class

```py3
from __future__ import annotations

from duui_py.annotator import DuuiAnnotator
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import V1RequestEnvelope, DuuiResult
from duui_py.logging import get_event_logger
from duui_py.logging.errors import log_errors


class MyAnnotator(DuuiAnnotator[V1RequestEnvelope, DuuiResult]):
    config_path = "annotator_config.example.json"
    
    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)
    
    @log_errors(recovery_suggestion="Check input format")
    async def process(self, doc: V1RequestEnvelope) -> DuuiResult:
        logger = get_event_logger()
        await logger.info("Processing document", {"parameters": dict(doc.parameters)})

        result = await self._process_document(doc)
        
        await logger.metric(
            category="processing",
            name="document_processing_time",
            value=125.5,
            unit="ms",
            interval_ms=1000
        )
        
        return result
    
    async def _process_document(self, doc: V1RequestEnvelope) -> DuuiResult:
        # Implement your annotation logic
        raise NotImplementedError
```

### 3. Expose the FastAPI app

```py3
from duui_py.app import create_app

app = create_app(MyAnnotator)
```

### 4. Run locally

```bash
uvicorn my_module:app --host 0.0.0.0 --port 9714
```

## Logging and Event Streaming

`duui-py` models all annotator telemetry as events. Java DUUI can subscribe to these events and correlate them with its own `DUUIEvent`s via trace/task/artifact context.

Event kinds:

- `log`: structured log messages with levels `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `metric`: named numeric measurements with category, unit, interval, and tags
- `error`: structured failures with error type, stack trace, and recovery suggestion

When logging is enabled in `annotator_config.json`, `create_app(...)` configures:

- a request-scoped event context middleware
- the global event logger returned by `get_event_logger()`
- an SSE stream manager under `/v2/events`
- optional automatic process/system metrics

You normally do not configure this manually in the annotator class.

### Annotator Logging Snippets

```py3
from time import time

from duui_py.logging import get_event_logger
from duui_py.logging.errors import log_errors
from duui_py.models.uima import sofa_text_value


@log_errors(recovery_suggestion="Check the incoming sofa text and annotator parameters.")
async def process(self, doc):
    started = time()
    logger = get_event_logger()
    text = sofa_text_value(doc.sofa) or ""

    await logger.info(
        "Processing started",
        {"characters": len(text), "parameters": dict(doc.parameters)},
    )

    await logger.debug(
        "Model invocation configured",
        {"model": "example-model", "batch_size": 32},
    )

    # annotator work happens here
    matches = 2

    elapsed_ms = int((time() - started) * 1000)
    await logger.metric(
        category="processing",
        name="matches",
        value=matches,
        unit="count",
        interval_ms=elapsed_ms,
        tags={"component": "example"},
    )

    await logger.info(
        "Processing completed",
        {"matches": matches, "elapsed_ms": elapsed_ms},
    )
```

Structured error events can be emitted directly, although `@log_errors(...)` is the normal path:

```py3
try:
    ...
except Exception as error:
    await logger.error_event(
        error_type=type(error).__name__,
        message=str(error),
        stack_trace=traceback.format_exc(),
        recovery_suggestion="Validate input payload and annotator parameters.",
    )
    raise
```

`await logger.info(...)` and the other logger calls are cooperative async calls. They do not block the OS thread; they enqueue/send events through the async logging path and yield to the event loop when needed.

### Real-time Event Streaming (SSE)

The framework provides Server-Sent Events (SSE) streaming via `/v2/events`.

First register a stream:

```bash
curl -s -X POST http://localhost:9714/v2/events/connect \
  -H 'Content-Type: application/json' \
  -d '{
    "annotator_id": "gnfinder-replica-0",
    "replica_id": "gnfinder-replica-0",
    "request_id": "manual-test",
    "ttl_minutes": 5
  }'
```

Response:

```json
{
  "stream_id": "0bd2edd2-3d5f-480f-9a9b-58ac08fca7c4",
  "expires_at": "2026-05-13T10:30:58.000000Z"
}
```

Then subscribe:

```bash
curl -N "http://localhost:9714/v2/events/stream?stream_id=0bd2edd2-3d5f-480f-9a9b-58ac08fca7c4"
```

Each SSE item is a JSON event:

```text
data: {"type":"log","timestamp":"2026-05-13T10:25:58.123Z","event_id":"...","context":{"trace_id":"...","task_id":"...","artifact_id":"..."},"level":"INFO","message":"Processing started","extra":{"characters":42}}
```

JavaScript client:

```js
const streamId = "0bd2edd2-3d5f-480f-9a9b-58ac08fca7c4";
const eventSource = new EventSource(`/v2/events/stream?stream_id=${streamId}`);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received event:', data);
};
```

### Python client

```py3
import json

import sseclient
import requests

# Register stream first
response = requests.post(
    'http://localhost:9714/v2/events/connect',
    json={
        'annotator_id': 'test-annotator',
        'replica_id': 'replica-1',
        'ttl_minutes': 5
    }
)
stream_id = response.json()["stream_id"]

# Connect to SSE stream
messages = sseclient.SSEClient(f'http://localhost:9714/v2/events/stream?stream_id={stream_id}')
for msg in messages:
    event = json.loads(msg.data)
    print(f"Event: {event['type']} - {event.get('message', '')}")
```

### Event Context Parameters

DUUI Java sends `event-context` on `/v1/process` requests so annotator-side logs can be correlated with Java-side pipeline events.

```
# Query parameter format
/v1/process?event-context=trace_id=...,span_id=...,task_id=...,artifact_id=...,component_id=...

# Request id header
x-request-id: 1f3df44b-7eb6-4c65-8b57-1c3d9016b519
```

The request middleware parses this context and every `logger.info(...)`, `logger.metric(...)`, and `logger.error_event(...)` emitted during that request inherits it.

### GNFinder Example Output

This is a shortened output from the Java DUUI GNFinder XMI pipeline test using the real `examples/gnfinder-msgpack-lua` annotator. Java DUUI and remote annotator events share the same `trace`, `task`, and `artifact` ids:

```text
[LOG] INFO duui.executor - Executing stage remote-gnfinder for artifact bd2451ab-725b-4923-811a-a8e2e92324ea trace=f4262e736b109637a9f90d8ccc2d7872 task=2be8a310-4de1-4194-b487-6fae82533d1d artifact=bd2451ab-725b-4923-811a-a8e2e92324ea
[LOG] INFO duui.v1 - Sending artifact bd2451ab-725b-4923-811a-a8e2e92324ea to v1 annotator gnfinder-replica-0 trace=f4262e736b109637a9f90d8ccc2d7872 task=2be8a310-4de1-4194-b487-6fae82533d1d artifact=bd2451ab-725b-4923-811a-a8e2e92324ea

[LOG] INFO remote-log - Process request started (normal) trace=f4262e736b109637a9f90d8ccc2d7872 task=2be8a310-4de1-4194-b487-6fae82533d1d artifact=bd2451ab-725b-4923-811a-a8e2e92324ea
[LOG] INFO remote-log - GNFinder processing started trace=f4262e736b109637a9f90d8ccc2d7872 task=2be8a310-4de1-4194-b487-6fae82533d1d artifact=bd2451ab-725b-4923-811a-a8e2e92324ea
[LOG] DEBUG remote-log - GNFinder regex scan configured trace=f4262e736b109637a9f90d8ccc2d7872 task=2be8a310-4de1-4194-b487-6fae82533d1d artifact=bd2451ab-725b-4923-811a-a8e2e92324ea
[METRIC] processing trace=f4262e736b109637a9f90d8ccc2d7872 task=2be8a310-4de1-4194-b487-6fae82533d1d artifact=bd2451ab-725b-4923-811a-a8e2e92324ea
[LOG] INFO remote-log - GNFinder processing completed trace=f4262e736b109637a9f90d8ccc2d7872 task=2be8a310-4de1-4194-b487-6fae82533d1d artifact=bd2451ab-725b-4923-811a-a8e2e92324ea
```

## Metrics Collection

### Automatic System Metrics

```py3
from duui_py.logging import configure_metric_collector

# Configure automatic metrics collection
collector = configure_metric_collector(
    collection_interval_seconds=5,
    include_system_metrics=True,
    include_process_metrics=True,
    include_disk_metrics=True,
    include_network_metrics=True
)

# Start collection
collector.start()
```

### Custom Metrics

```py3
await logger.metric(
    category="custom",
    name="processing_time",
    value=125.5,
    unit="milliseconds",
    interval_ms=1000,
    tags={"operation": "document_processing"}
)
```

## Error Handling

### Decorator-based error handling

```py3
from duui_py.logging.errors import log_errors

@log_errors(log_level="ERROR", recovery_suggestion="Retry with valid input")
async def process_document(doc):
    # Function automatically logs any exceptions
    ...
```

### Context manager for error handling

```py3
from duui_py.logging.errors import error_context

def process_with_context(doc):
    with error_context("document_processing", recovery_suggestion="Check document format"):
        # Any exception here gets logged
        result = process_doc(doc)
        return result
```

## API Endpoints

### Standard DUUI endpoints

- `GET /v1/typesystem` → serves the TypeSystem XML
- `GET /v1/details/input_output` → emits the descriptor in DUUI format
- `GET /v1/documentation` → emits metadata + `parameters_schema`
- `GET /v1/communication_layer` → Lua communication script specification
- `POST /v1/process` → the processing endpoint

### Logging and monitoring endpoints

- `POST /v2/events/connect` → register a new event stream
- `GET /v2/events/stream?stream_id=...` → SSE stream for receiving events
- `GET /v2/events/list` → list active streams
- `GET /v2/events/info/{stream_id}` → get stream information
- `DELETE /v2/events/{stream_id}` → disconnect a stream

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

## Development

### Building from source

```bash
# Clone the repository
git clone https://github.com/your-org/duui-py.git
cd duui-py

# Install in development mode
pip install -e .

# Run tests
python test_package.py
```

### Package structure

```
duui-py/
├── src/duui_py/
│   ├── annotator.py           # Base annotator class
│   ├── app.py                # FastAPI app factory
│   ├── settings.py           # Framework settings
│   ├── version.py            # Package version
│   ├── codecs/               # Communication layer codecs
│   │   ├── base.py
│   │   ├── msgpack_lua/      # Descriptor-driven Lua + framed msgpack codec
│   │   └── lua_custom/       # Lua custom codec
│   ├── logging/              # Logging and monitoring module
│   │   ├── core.py           # Event models and logger
│   │   ├── context.py        # Event context management
│   │   ├── streaming.py      # SSE streaming implementation
│   │   ├── metrics.py        # Metrics collection
│   │   └── errors.py         # Error handling utilities
│   ├── models/               # Data models
│   │   ├── config.py         # Annotator configuration
│   │   ├── duui.py           # DUUI document models
│   │   ├── uima.py           # UIMA type system models
│   │   └── fs_builder.py     # Feature structure builder
│   └── utils/
│       └── mime.py           # MIME type utilities
├── pyproject.toml            # Package configuration
├── README.md                 # This file
├── LOGGING_USAGE.md          # Detailed logging documentation
├── annotator_config.example.json
└── test_package.py           # Package verification test
```

## License

AGPL-3.0 - See [LICENSE](LICENSE) for details.

## Migration from duui-py-framework

If you were using the `duui-py-framework` directory from the main DUUI-UIMA repository:

1. **Install the separate package**:
```bash
   pip install -e /path/to/duui-py
```

2. **Update Dockerfiles**:
```dockerfile
   # Old: COPY duui-py-framework /app/duui-py-framework
   # New: Use the package from PyPI or install from source
   RUN pip install duui-py
```

3. **Update imports** (no changes needed - same Python package name)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please use the [GitHub Issues](https://github.com/dterefe/duui-py/issues) page.
