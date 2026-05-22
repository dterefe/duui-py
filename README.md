# duui-py

Python helpers for building DUUI V1 annotators.

The supported example path is deliberately small:

- define the annotator descriptor directly in Python
- expose the annotator with `create_app`
- use generated `MsgPackLuaCodec` communication Lua
- use `AsyncChunkedRequestAdapter` for example annotators
- yield existing UIMA model objects from `duui_py.models.uima_typesystem`
- stream OpenTelemetry-compatible logs, metrics, spans, summaries, and errors through `GET /v2/events`

## Install

```bash
pip install -e .
```

## Run An Example

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
GET  /v2/events
```

Per-request telemetry is controlled with `X-DUUI-Telemetry`; see
[`docs/events.md`](docs/events.md) for scoped histograms, resource gauges, and
trace context headers.

## Documentation

- [Annotators and Apps](docs/annotators.md)
- [Adapters and Processing](docs/adapters.md)
- [Python Config Objects](docs/config.md)
- [Generated MsgPack/Lua Codec](docs/msgpack-lua.md)
- [Custom Lua Codec](docs/custom-lua.md)
- [UIMA Models and Type Systems](docs/uima-models.md)
- [Events, Logging, Metrics, and Errors](docs/events.md)
- [Example Annotators](docs/examples.md)

## Tested Examples

Text examples covered by the DUUI Java harness:

- `examples/gnfinder-msgpack-lua`
- `examples/taxonerd-msgpack-lua`
- `examples/argument-msgpack-lua`
- `examples/essay-scorer-msgpack-lua`
- `examples/srl-msgpack-lua`
- `examples/spacy-lua-msgpack`
- `examples/geonames-msgpack-lua`

`examples/whisper-msgpack-lua` uses the same app/config/codec path, but consumes byte SofA input.

## Development Checks

```bash
python -m compileall -q src examples
python -m pytest -q
```

Java integration tests live in:

```text
../DockerUnifiedUIMAInterface/src/test/java/org/texttechnologylab/duui/rework
```
