# spaCy Annotator with Lua + MsgPack for duui-py Framework

This example demonstrates how to migrate an existing DUUI annotator to use the duui-py framework while maintaining Lua marshalling with msgpack serialization.

## Overview

This example shows a complete integration of:
1. **duui-py framework** - Modern Python framework for building DUUI annotators
2. **LuaCustomCodec** - Custom codec for Lua communication with msgpack serialization
3. **spaCy NLP library** - For natural language processing tasks
4. **Real-time logging and event streaming** - Using duui-py's logging system
5. **Comprehensive metrics collection** - System and process metrics

## Files

- `spacy_annotator.py` - Main Python annotator using duui-py framework
- `spacy_communication.lua` - Lua script for msgpack serialization/deserialization  
- `TypeSystemSpacy.xml` - UIMA TypeSystem definition
- `annotator_config.json` - Annotator configuration
- `README.md` - This documentation
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Python package configuration (optional)

## Quick Start

### 1. Install dependencies

```bash
# Install duui-py framework (editable install)
pip install -e /path/to/duui-py

# Install example dependencies
pip install -r requirements.txt
```

### 2. Install spaCy models

```bash
# Download spaCy models
python -m spacy download en_core_web_sm
python -m spacy download de_core_news_sm
python -m spacy download fr_core_news_sm
```

### 3. Run the annotator

```bash
# Navigate to example directory
cd examples/spacy-lua-msgpack

# Run the FastAPI server
uvicorn spacy_annotator:app --host 0.0.0.0 --port 9714 --reload
```

### 4. Test the annotator

```bash
# Test using curl
curl -X POST http://localhost:9714/v1/process \
  -H "Content-Type: application/x-msgpack" \
  --data-binary @<(echo '{"text": "Hello world, this is a test.", "lang": "en", "parameters": {}}' | msgpack-python)
```

## Features

### Lua + MsgPack Integration

The example uses `LuaCustomCodec` which:
- Uses Lua scripts for CAS serialization/deserialization on the Java side
- Uses msgpack for efficient binary serialization between Java and Python
- Maintains compatibility with existing DUUI infrastructure

### Real-time Logging and Event Streaming

The annotator integrates with duui-py's logging system:
- **Server-Sent Events (SSE)** via `/v2/events` endpoint
- **Request-scoped logging context** for distributed tracing
- **Automatic metrics collection** (CPU, memory, disk, network)
- **Structured error handling** with recovery suggestions

### Configuration

The `annotator_config.json` provides:
- **Model configuration** - spaCy model selection
- **Validation settings** - MIME type and data validation
- **Logging configuration** - Event streaming and metrics collection
- **TypeSystem reference** - UIMA TypeSystem XML path

## Integration with Java DUUI Pipeline

This annotator can be used from Java DUUI pipelines using the standard DUUI protocol:

```xml
<!-- Java pipeline configuration -->
<annotator>
  <implementation>org.texttechnologylab.annotation.spacy.SpacyAnnotator</implementation>
  <parameters>
    <parameter name="model_name" value="en_core_web_sm"/>
  </parameters>
</annotator>
```

## Logging and Monitoring

### Event Streaming

Connect to the event stream:

```javascript
// JavaScript client
const eventSource = new EventSource('/v2/events?identifiers=annotator=spacy-lua-msgpack,replica=1');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Event:', data.type, data.message);
};
```

### Metrics Collection

The annotator automatically collects:
- **System metrics**: CPU, memory, disk usage
- **Process metrics**: Python process statistics  
- **Network metrics**: Network I/O statistics
- **Custom metrics**: Document processing time, annotation counts

## Migration Guide

If you have an existing spaCy annotator in the DUUI-UIMA repository, follow these steps:

### 1. Update Dependencies

Replace direct spaCy imports with duui-py framework:

```python
# Old: Direct spaCy integration
# New: Use duui-py framework
from duui_py.annotator import DuuiAnnotator
from duui_py.codecs.lua_custom import LuaCustomCodec
```

### 2. Implement Codec

Create a `LuaCustomCodec` with msgpack serialization:

```python
def codec(self) -> LuaCustomCodec:
    with open("spacy_communication.lua", "r") as f:
        lua_script = f.read()
    
    def decode_request(body: bytes) -> SpacyRequest:
        data = msgpack.unpackb(body, raw=False, strict_map_key=False)
        return SpacyRequest(**data)
    
    def encode_response(result: SpacyResponse) -> bytes:
        return msgpack.packb(result.model_dump(by_alias=True, exclude_none=True), use_bin_type=True)
    
    return LuaCustomCodec(
        communication_lua=lua_script,
        request_media_type="application/x-msgpack",
        response_media_type="application/x-msgpack",
        decode_request=decode_request,
        encode_response=encode_response,
        name="spacy-lua-msgpack",
    )
```

### 3. Add Logging Integration

Configure logging and metrics:

```python
from duui_py.logging import configure_logger, StreamSink, ConsoleSink, configure_stream_manager

stream_manager = configure_stream_manager(default_ttl_minutes=5)
stream_sink = StreamSink(stream_manager)
console_sink = ConsoleSink()

configure_logger(
    sinks=[stream_sink, console_sink],
    default_context={"annotator": self.config.descriptor.name},
    annotator_descriptor=self.config.descriptor,
    start_background_worker=True,
)
```

### 4. Update Configuration

Create `annotator_config.json` with proper metadata and TypeSystem reference.

## Performance Considerations

### Model Caching

The example uses `@lru_cache` to cache spaCy models, preventing repeated loading:

```python
@lru_cache(maxsize=2)
def load_spacy_model(model_name: str, variant: str = "") -> spacy.Language:
    return spacy.load(model_name, enable=enabled_tools)
```

### Thread Safety

- **Model loading**: Thread-safe with `Lock`
- **Logging**: Async-safe with duui-py's logging system
- **Metrics collection**: Background worker with configurable intervals

### Network Efficiency

- **MsgPack**: Binary serialization reduces payload size by ~30-50% compared to JSON
- **SSE**: Efficient real-time event streaming over HTTP
- **Connection pooling**: HTTP/1.1 keep-alive for repeated requests

## Troubleshooting

### Common Issues

1. **Missing spaCy models**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **MsgPack serialization errors**:
   - Ensure msgpack-python is installed: `pip install msgpack-python`
   - Check that Lua script matches Python data models

3. **Lua script errors**:
   - Verify Lua script path in `codec()` method
   - Check that required Java classes are available in classpath

4. **Event streaming not working**:
   - Check that logging is enabled in config: `"logging": {"enabled": true}`
   - Verify SSE client connection to `/v2/events` endpoint

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check event streams:

```bash
curl http://localhost:9714/v2/events/list
```

## License

This example is part of the duui-py framework, licensed under AGPL-3.0.

## Support

For issues and questions:
- [duui-py GitHub Issues](https://github.com/dterefe/duui-py/issues)
- Check existing DUUI-UIMA documentation
- Review duui-py framework documentation