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
      "domain": {
        "sofa": { "mimeType": "text/plain; charset=utf-8", "language": "x-unspecified" },
        "optional_types": []
      },
      "optional_inputs": []
    },
    "output": {
      "sofa": { "mimeType": "text/plain; charset=utf-8", "language": "x-unspecified" },
      "types": []
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
from duui_py.codecs.msgpack_v1 import DuuiBinV1MsgpackCodec
from duui_py.models import DuuiDocument, DuuiResult
from duui_py.logging import (
    configure_logger, 
    StreamSink, 
    ConsoleSink, 
    configure_stream_manager,
    EventContext,
    create_event_context_from_request,
    get_event_logger
)
from duui_py.logging.errors import log_errors


class MyAnnotator(DuuiAnnotator[DuuiDocument, DuuiResult]):
    config_path = "annotator_config.example.json"
    
    def __init__(self, config_path: str | None = None, config: dict | None = None):
        super().__init__(config_path, config)
        
        # Configure logging and event streaming
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
    
    def codec(self) -> DuuiBinV1MsgpackCodec:
        return DuuiBinV1MsgpackCodec()
    
    @log_errors(log_level="ERROR", recovery_suggestion="Check input format")
    async def process(self, doc: DuuiDocument) -> DuuiResult:
        # Set request context from event-context parameter
        event_context_param = self.request.headers.get("x-event-context", "")
        context = create_event_context_from_request(
            event_context_param=event_context_param,
            request_id=self.request.id,
            artifact_id=doc.id
        )
        
        await self.logger.info(f"Processing document {doc.id}")
        
        # Your processing logic here
        result = await self._process_document(doc)
        
        # Log metrics
        await self.logger.metric(
            category="processing",
            name="document_processing_time",
            value=125.5,
            unit="milliseconds",
            interval_ms=1000
        )
        
        return result
    
    async def _process_document(self, doc: DuuiDocument) -> DuuiResult:
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

### Real-time Event Streaming (SSE)

The framework provides Server-Sent Events (SSE) streaming via the `/v2/events` endpoint:

```js
// JavaScript client
const eventSource = new EventSource('/v2/events?identifiers=annotator=my-annotator,replica=replica-1');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received event:', data);
};
```

### Python client

```py3
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

# Connect to SSE stream
messages = sseclient.SSEClient('http://localhost:8000/v2/events/stream/{stream_id}')
for msg in messages:
    event = json.loads(msg.data)
    print(f"Event: {event['type']} - {event.get('message', '')}")
```

### Event Context Parameters

Pass event context as query parameter or header:

```
# Query parameter format
/v1/process?event-context=annotator=my-annotator,artifact=doc123,replica=replica-1

# Or as header
X-Event-Context: annotator=my-annotator,artifact=doc123,replica=replica-1,application=my-app
```

## Metrics Collection

### Automatic System Metrics

```py3
from duui_py.logging import configure_metric_collector

# Configure automatic metrics collection
collector = configure_metric_collector(
    interval_seconds=5,
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
- `GET /v1/communication_layer` → codec information
- `POST /v1/process` → the processing endpoint

### Logging and monitoring endpoints

- `POST /v2/events/register` → register a new event stream
- `GET /v2/events/stream/{stream_id}` → SSE stream for receiving events
- `GET /v2/events/list` → list active streams
- `GET /v2/events/{stream_id}/info` → get stream information

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
│   │   ├── msgpack_v1/       # DUUI-BIN v1 MessagePack codec
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