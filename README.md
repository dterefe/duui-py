# duui-py

Python helpers for building DUUI V1 annotators.

The current examples use one path: a FastAPI app created with `create_app`, an annotator class with Python config objects, generated MsgPack/Lua communication, and Python UIMA model classes from `duui_py.models.uima_typesystem`.

## Install

```bash
pip install -e .
```

Run an example:

```bash
cd examples/gnfinder-msgpack-lua
PYTHONPATH=../../src uvicorn gnfinder_annotator:app --host 0.0.0.0 --port 9714
```

Useful endpoints:

```text
GET  /v1/documentation
GET  /v1/typesystem
GET  /v1/communication_layer
POST /v1/process
```

## Documentation

- [Annotators and Apps](docs/annotators.md)
- [Python Config Objects](docs/config.md)
- [Generated MsgPack/Lua Codec](docs/msgpack-lua.md)
- [UIMA Models and Type Systems](docs/uima-models.md)
- [Logging, Metrics, and Errors](docs/logging-errors-metrics.md)
- [Example Annotators](docs/examples.md)

## Examples

Text examples currently covered by the DUUI Java harness:

- `examples/gnfinder-msgpack-lua`
- `examples/taxonerd-msgpack-lua`
- `examples/argument-msgpack-lua`
- `examples/essay-scorer-msgpack-lua`
- `examples/srl-msgpack-lua`
- `examples/spacy-lua-msgpack`
- `examples/geonames-msgpack-lua`

The non-text `whisper-msgpack-lua` example uses the same app/config/codec path, but processes byte SofA input.

## Development Checks

```bash
python -m compileall -q src examples
python -m pytest -q test_msgpack_lua.py test_simple.py test_whisper_v1_async_process.py
```

The Java integration harness lives in:

```text
../DockerUnifiedUIMAInterface/src/test/java/org/texttechnologylab/duui/rework/DUUIDuuiPyTextExamplesIntegrationTest.java
```
