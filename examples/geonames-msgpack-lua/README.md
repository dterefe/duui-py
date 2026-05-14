# GeoNames MsgPack Lua Example

This migrates the `duui-geonames-fst` DUUI component shape to `duui-py`.

The example consumes DKPro `Location` annotations and declares
`org.texttechnologylab.annotation.geonames.GeoNamesEntity` output. It uses the
framework `MsgPackLuaCodec`, so the Lua communication layer is generated from
the Python annotator descriptor.

This does not recreate GeoNames records in Python. It expects a running
`duui-geonames-fst`-compatible backend via `backend_url` or `GEONAMES_FST_URL`,
forwards `Location` mentions to that backend, and maps the backend response into
the existing `GeoNamesEntity` UIMA model. Runtime parameters mirror the original
component:

- `annotation_type`
- `mode`
- `result_selection`
- `max_dist`
- `state_limit`
- `filter`
- `backend_url`

```bash
cd examples/geonames-msgpack-lua
uvicorn geonames_annotator:app --host 0.0.0.0 --port 9714
```
