# Events, Logging, Metrics, and Errors

When logging is enabled, `create_app` exposes one event endpoint:

```text
GET /v2/events
```

The endpoint is server-sent events. There is no polling route for the normal event protocol.

```bash
curl -N 'http://127.0.0.1:9714/v2/events?ttl_minutes=5'
```

Initial output:

```text
event: handshake
data: {"stream_id":"..."}
```

## Logs

Annotators use the normal event logger for human-readable lifecycle and debug messages. It is a no-op when event logging is not configured.

```python
from duui_py.logging import get_event_logger_or_none


async def process(self, doc):
    logger = get_event_logger_or_none()
    if logger is not None:
        await logger.info("GNFinder processing started", extra={"text_length": len(text)})

    ...

    if logger is not None:
        await logger.info("GNFinder processing completed", extra={"matches": matches})
```

Example SSE log payload:

```text
data: {"type":"log","level":"info","message":"GNFinder processing completed",...}
```

## Metrics

Annotators use the small `metrics` helper for counters, gauges, and timings.

```python
from time import time

from duui_py.metrics import metrics


async def process(self, doc):
    started = time()
    matches = 0

    for item in find_matches(doc):
        matches += 1
        yield item

    elapsed_ms = int((time() - started) * 1000)
    await metrics.count("gnfinder_taxon_matches", matches)
    await metrics.timing("gnfinder_processing_ms", elapsed_ms)
```

Timer form:

```python
async with metrics.timer("geonames_backend_lookup_ms"):
    response = await backend.lookup(payload)
```

Example SSE metric payload:

```text
data: {"type":"metric","category":"processing","name":"gnfinder_taxon_matches","value":2.0,"unit":"count",...}
```

## Errors

Annotators raise HTTP-status based errors. The adapter logs them automatically and emits a DUUI error chunk.

```python
from duui_py.errors import unavailable, unprocessable


if not backend_url:
    unprocessable("GeoNames backend URL is required", parameter="backend_url")

try:
    response = backend.lookup(payload)
except TimeoutError:
    unavailable("GeoNames backend timed out", backend_url=backend_url)
```

The emitted error chunk carries the status and retryability:

```json
{
  "message": "GeoNames backend timed out",
  "status": 503,
  "title": "Service Unavailable",
  "retryable": true,
  "detail": {
    "backend_url": "http://127.0.0.1:9000"
  }
}
```

Default retryable statuses are `408`, `425`, `429`, `502`, `503`, and `504`.
