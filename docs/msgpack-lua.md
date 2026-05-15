# Generated MsgPack/Lua Codec

Current examples use `MsgPackLuaCodec`.

```python
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec


def codec(self) -> MsgPackLuaCodec:
    return MsgPackLuaCodec(self.config)
```

The codec generates the Lua script served by:

```text
GET /v1/communication_layer
```

The examples do not ship hand-written Lua scripts. The descriptor-generated Lua handles the DUUI side:

- serializes text, byte, URI, and annotation-span SofA input
- serializes configured input annotations into msgpack chunks
- deserializes annotation chunks into CAS annotations
- deserializes feature-structure chunks into CAS feature structures when their type exists
- propagates codec errors as DUUI process failures

## Request In Python

`process(...)` receives a `V1RequestEnvelope`.

```python
from duui_py.models.uima import sofa_text_value


async def process(self, doc):
    text = sofa_text_value(doc.sofa) or ""
    parameters = dict(doc.parameters)
    incoming_feature_structures = doc.fs
```

Example decoded request:

```text
sofa:
  mimeType = text/plain; charset=utf-8
  language = en
  text = "Frankfurt am Main ist eine Stadt."
parameters:
  backend_url = http://127.0.0.1:9000
fs:
  de.tudarmstadt.ukp.dkpro.core.api.ner.type.Location [0, 17]
```

## Streaming Response

Annotators yield minimal items:

```python
yield GeoNamesEntity(begin=0, end=17, name="Frankfurt am Main", countryCode="DE")
yield AnnotatorMetaData(name=self.config.descriptor.name, version=self.config.descriptor.version)
yield DocumentModification(user=self.config.descriptor.name)
```

The codec frames those items as:

```text
CHUNK_START
CHUNK_ANNOTATION          GeoNamesEntity
CHUNK_FEATURE_STRUCTURE   AnnotatorMetaData
CHUNK_FEATURE_STRUCTURE   DocumentModification
CHUNK_END
```

For GNFinder with two verified taxa, a live response produces this chunk-type sequence:

```text
[1, 3, 3, 4, 4, 5]
```

That is `START`, two annotations, two feature structures, and `END`.

## Whole-Body Compatibility

`MsgPackLuaCodec` still has `decode_request(...)` and `encode_response(...)` for compatibility. The current examples use the stream methods through `AsyncChunkedRequestAdapter`.
