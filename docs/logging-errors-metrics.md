# Logging, Metrics, and Errors

Current examples use:

```python
from duui_py.logging import get_event_logger_or_none, log_errors
```

Use `get_event_logger_or_none()` in annotators so direct local tests still work when no logger is configured.

```python
from time import time

from duui_py.logging import get_event_logger_or_none, log_errors
from duui_py.models.uima import sofa_text_value


@log_errors(recovery_suggestion="Check incoming text and parameters.")
async def process(self, doc):
    started = time()
    logger = get_event_logger_or_none()
    text = sofa_text_value(doc.sofa) or ""

    if logger:
        await logger.info("Processing started", {"characters": len(text)})

    annotations = []

    elapsed_ms = int((time() - started) * 1000)
    if logger:
        await logger.metric("processing", "annotations", len(annotations), "count", elapsed_ms)
        await logger.info("Processing completed", {"annotations": len(annotations), "elapsed_ms": elapsed_ms})

    return ...
```

Example event payloads:

```text
log INFO Processing started
  characters = 41

metric processing.annotations
  value = 2
  unit = count
  interval_ms = 3

log INFO Processing completed
  annotations = 2
  elapsed_ms = 3
```

`@log_errors(...)` catches exceptions, records a structured error event when logging is configured, and re-raises the exception so DUUI sees the failure.

Example error:

```text
error GeoNamesBackendMissing
  message = "GeoNames backend URL is required"
  recovery = "Start duui-geonames-fst and pass backend_url."
```
