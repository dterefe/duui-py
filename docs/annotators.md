# Annotators and Apps

An annotator is a Python class that subclasses `DuuiAnnotator` and returns a `DuuiResult`.

Every current example follows this shape:

```python
from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import V1RequestEnvelope, DuuiResult


class ExampleAnnotator(DuuiAnnotator[V1RequestEnvelope, DuuiResult]):
    config = ...

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> DuuiResult:
        return DuuiResult()


app = create_app(ExampleAnnotator)
```

Run it with Uvicorn:

```bash
PYTHONPATH=../../src uvicorn example_annotator:app --host 0.0.0.0 --port 9714
```

What `create_app` does:

- exposes DUUI V1 endpoints
- serves the annotator descriptor
- serves the configured type system XML
- validates request and response MIME types
- configures logging, metrics, and error capture
- calls `process(...)` for normal V1 requests

## Output

Annotators return `DuuiResult`.

```python
from duui_py.models import DuuiResult

return DuuiResult(
    annotations=[...],
    feature_structures=[...],
    meta=...,
    modification_meta=...,
)
```

Example output shape after encoding back into DUUI:

```text
annotations:
  org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon [0, 12] "Homo sapiens"
feature structures:
  org.texttechnologylab.annotation.AnnotatorMetaData
  org.texttechnologylab.annotation.DocumentModification
```

Use `annotations` for UIMA annotation types. Use `feature_structures` for non-annotation types such as metadata, comments, and relation objects.
