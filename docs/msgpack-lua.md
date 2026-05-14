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

No example should ship a custom Lua script. The descriptor-generated Lua handles the DUUI side:

- serializes text, byte, URI, and annotation-span SofA input
- serializes configured input annotations into the Python request
- deserializes returned annotation chunks into CAS annotations
- deserializes returned feature-structure chunks into CAS feature structures when their type exists
- returns codec errors as DUUI process failures

## Request Shape in Python

`process(...)` receives a `V1RequestEnvelope`.

```python
from duui_py.models.uima import sofa_text_value


async def process(self, doc):
    text = sofa_text_value(doc.sofa) or ""
    parameters = dict(doc.parameters)
    incoming_feature_structures = doc.fs
```

Example request values:

```text
sofa: text/plain; charset=utf-8
parameters:
  lang: en
  verify: true
fs:
  de.tudarmstadt.ukp.dkpro.core.api.ner.type.Location [0, 17]
```

## Response Shape

```python
from duui_py.models import DuuiResult

return DuuiResult(annotations=annotations, feature_structures=feature_structures)
```

Example CAS result:

```text
org.texttechnologylab.annotation.geonames.GeoNamesEntity [0, 17]
  name = "Frankfurt am Main"
  countryCode = "DE"
```
