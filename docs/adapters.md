# Adapters and Processing

`create_app` delegates `POST /v1/process` to a request adapter. The adapter owns request/response IO; the annotator only works with decoded Python objects.

## Async Chunked Adapter

All current examples use `AsyncChunkedRequestAdapter`.

```python
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app


app = create_app(MyAnnotator, request_adapter=AsyncChunkedRequestAdapter())
```

This adapter:

- reads the request with `request.stream()`
- passes the byte stream to `codec.decode_request_stream(...)`
- invokes the annotator
- passes yielded items to `codec.encode_response_stream(...)`
- returns a `StreamingResponse`

It is the normal path for generated msgpack-lua examples. It does not call `await request.body()`.

Optional limits for partial chunk buffering:

```python
from duui_py.adapters import AsyncChunkedAdapterConfig, AsyncChunkedRequestAdapter


adapter = AsyncChunkedRequestAdapter(
    AsyncChunkedAdapterConfig(
        max_partial_buffer_bytes=64 * 1024 * 1024,
        max_chunk_payload_bytes=None,
    )
)
```

`max_partial_buffer_bytes` protects incomplete chunk assembly. It is not a full request buffer.

## Synchronous Adapter

`SynchronousRequestAdapter` exists for codecs that only expose whole-body encode/decode methods.

```python
from duui_py.adapters import SynchronousRequestAdapter


app = create_app(MyAnnotator, request_adapter=SynchronousRequestAdapter())
```

This adapter awaits the whole request body and returns one encoded response body. Do not use it for the current text examples.

## Default Selection

If no adapter is passed to `create_app`, `default_request_adapter(codec)` uses:

- `AsyncChunkedRequestAdapter` when the codec implements `decode_request_stream` and `encode_response_stream`
- `SynchronousRequestAdapter` otherwise

Examples pass the async adapter explicitly so the tested behavior is obvious at the app definition.
