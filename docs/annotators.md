# Annotators and Apps

An annotator is a Python class that subclasses `DuuiAnnotator`. Current examples receive a `V1RequestEnvelope` and yield individual output items. They do not build a large `DuuiResult` in normal operation.

```python
from collections.abc import AsyncIterator

from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import AnnotatorMetaData, DocumentModification, V1RequestEnvelope
from duui_py.models.uima import sofa_text_value
from duui_py.models.uima_typesystem.texttechnologylab.annotation.biofid.gnfinder.types import (
    VerifiedTaxon,
)


class ExampleAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = ...

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        text = sofa_text_value(doc.sofa) or ""
        start = text.find("Homo sapiens")
        if start >= 0:
            yield VerifiedTaxon(
                begin=start,
                end=start + len("Homo sapiens"),
                value="Homo sapiens",
                cardinality=2,
                oddsLog10=0.75,
                matchedName="Homo sapiens",
                matchedCanonicalSimple="Homo sapiens",
                matchedCanonicalFull="Homo sapiens",
                currentName="Homo sapiens",
                dataSourceId=0,
                recordId="example-0",
                sortScore=0.75,
                editDistance=0,
            )
        yield AnnotatorMetaData(name=self.config.descriptor.name, version=self.config.descriptor.version)
        yield DocumentModification(user=self.config.descriptor.name)


app = create_app(ExampleAnnotator, request_adapter=AsyncChunkedRequestAdapter())
```

Run it with Uvicorn:

```bash
PYTHONPATH=../../src uvicorn example_annotator:app --host 0.0.0.0 --port 9714
```

`create_app` exposes:

- `GET /v1/documentation`
- `GET /v1/typesystem`
- `GET /v1/communication_layer`
- `GET /v1/details/input_output`
- `POST /v1/process`
- `GET /v2/events` when logging is enabled

## Output Items

Current examples yield these item classes:

- `Annotation` subclasses for CAS annotations
- `FeatureStructure` subclasses for metadata, comments, relations, and other non-indexed structures
- `SoFa` objects when an annotator replaces or creates SofA data
- `DuuiError` or `str` for error chunks

The generated msgpack-lua codec maps yielded items to DUUI chunks:

```text
Annotation         -> CHUNK_ANNOTATION
FeatureStructure  -> CHUNK_FEATURE_STRUCTURE
SoFa              -> CHUNK_SOFA
DuuiError / str   -> CHUNK_ERROR
```

Example CAS result:

```text
org.texttechnologylab.annotation.biofid.gnfinder.VerifiedTaxon [0, 12] "Homo sapiens"
org.texttechnologylab.annotation.AnnotatorMetaData
org.texttechnologylab.annotation.DocumentModification
```
