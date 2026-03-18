# duui-py

Python framework for building DUUI annotators with:

- FastAPI server scaffold
- Generic codec interface (default: DUUI-BIN v1 MessagePack codec)
- Config-driven `/v1/details/input_output`, `/v1/typesystem`, `/v1/documentation`
- Strong validation (mime types, SofA payload, config schema)

## Install

Editable install:

```bash
pip install -e .
```

Runtime dependencies are declared in `pyproject.toml`.

## Quick Start

1) Create a config file (start from `annotator_config.example.json`).

2) Implement an annotator class:

```python
from __future__ import annotations

from duui_py.annotator import DuuiAnnotator
from duui_py.codecs.msgpack_v1 import DuuiBinV1MsgpackCodec
from duui_py.models import DuuiDocument, DuuiResult


class MyAnnotator(DuuiAnnotator[DuuiDocument, DuuiResult]):
    config_path = "annotator_config.example.json"

    def codec(self) -> DuuiBinV1MsgpackCodec:
        return DuuiBinV1MsgpackCodec()

    async def process(self, doc: DuuiDocument) -> DuuiResult:
        raise NotImplementedError
```

3) Expose the FastAPI app:

```python
from duui_py.app import create_app

app = create_app(MyAnnotator)
```

4) Run locally:

```bash
uvicorn my_module:app --host 0.0.0.0 --port 9714
```

## Config (`AnnotatorConfig`)

Config can be:

- Declared directly in the class (`config = AnnotatorConfig(...)`), or
- Loaded from JSON via `config_path` (recommended).

The loader is strict:

- Unknown keys are rejected (`extra="forbid"`).
- `descriptor.input.domain.sofa.mimeType` and `descriptor.output.sofa.mimeType` must be non-empty patterns.
- Wildcards are supported only as `major/*` (for example `audio/*`).
- Alternatives can be separated with `|` (for example `audio/*|video/*`).
- Framework behavior is configured via `meta.settings`.
- Framework settings are process-global and initialized on the first `create_app(...)` call.

Minimal JSON shape:

```json
{
    "meta": {
        "implementation_lang": "Python",
        "meta": {},
        "settings": {
            "validation": {
                "strict_mime_validation": true,
                "strict_input_mime_check": true,
                "strict_output_mime_check": true,
                "strict_sofa_data_type_validation": true,
                "strict_descriptor_mime_pattern_validation": true
            },
            "limits": {
                "request_max_bytes": null,
                "response_max_bytes": null
            },
            "errors": {
                "fail_on_codec_error": true,
                "include_validation_details": true
            }
        }
    },
    "descriptor": {
        "name": "my-annotator",
        "version": "0.0.0",
        "input": {
            "domain": {
                "sofa": { "mimeType": "text/plain; charset=utf-8", "language": "x-unspecified" },
                "optional_types": []
            },
            "optional_inputs": []
        },
        "output": {
            "sofa": { "mimeType": "text/plain; charset=utf-8", "language": "x-unspecified" },
            "types": []
        }
    },
    "typesystem_xml_path": "TypeSystem.xml",
    "parameters_schema": {}
}
```

## Endpoints

`create_app(...)` exposes:

- `GET /v1/typesystem` → serves the file from `typesystem_xml_path` with media type `application/xml`
- `GET /v1/details/input_output` → emits the descriptor in DUUI format
- `GET /v1/documentation` → emits metadata + `parameters_schema`
- `GET /v1/communication_layer`
    - Always `application/json`
    - Always `{"kind":"...","format":"...","version":1,"spec":...}`
- `POST /v1/process` → the processing endpoint

## MessagePack Codec (DUUI-BIN v1)

### Request (what your annotator receives)

When using the default `DuuiBinV1MsgpackCodec`, DUUI sends `application/x-msgpack` and the server decodes into a `DuuiDocument`:

- `doc.sofa.mimeType` is a concrete mime type (no wildcards)
- `doc.sofa.language` is non-empty
- SofA typing is enforced:
    - `mimeType` base starts with `text/` → `doc.sofa.data` is `string`
    - otherwise → `doc.sofa.data` is `bytes`

`create_app` validates `doc.sofa.mimeType` against `descriptor.input.domain.sofa.mimeType` using wildcard matching (`audio/*`, `video/*`, …).

### Response (what your annotator returns)

Return a `DuuiResult`:

- `result.sofa` is optional (set it if you produce a new SofA for the target view)
- `result.annotations` is the simple path (flat annotation list)
- `result.feature_structures` is the general path (FS graph)

`create_app` validates `result.sofa.mimeType` against `descriptor.output.sofa.mimeType` (if `result.sofa` is present).

## Annotations, Feature Structures, and Updates

### Simple path: `result.annotations`

Use this if you only return stand-alone annotations:

```python
from duui_py.models import SofaPayload
from duui_py.models.uima import Sentence

return DuuiResult(
    sofa=SofaPayload(
        mimeType="text/plain; charset=utf-8",
        language=doc.sofa.language,
        data="output text",
    ),
    annotations=[
        Sentence(begin=0, end=12, features={})
    ],
)
```

### General path: `result.feature_structures`

Use this if you need references between feature structures (for example Token → POS):

- Create `FeatureStructureNode` objects with stable string `key`s.
- Reference other nodes via `FeatureStructureKeyRef(key=...)`.
- The framework assigns numeric message ids and produces the wire-level `{"$ref": <int>}` references.

### Updates: `ref`

For updates, a feature structure can include `ref` (low-level CAS FS ref). Rules:

- Input FS records may contain `ref` (existing objects)
- New objects produced by an annotator must omit `ref`
- If an output FS includes a `ref`, DUUI treats it as “update existing”, not “create new”

## Lua / Custom Communication Layer

For custom/legacy communication layers, use `LuaCustomCodec`:

- You must supply:
    - `communication_lua` (returned as `/v1/communication_layer` `spec`)
    - `request_media_type`
    - `response_media_type`
    - `decode_request: bytes -> RequestModel`
    - `encode_response: ResponseModel -> bytes`
- The framework does not enforce request/response schema or transport format for this codec.

Use `DuuiAnnotator[RequestModel, ResponseModel]` for non-msgpack payload types:

```python
from duui_py.annotator import DuuiAnnotator
from duui_py.codecs import LuaCustomCodec


class MyCustomAnnotator(DuuiAnnotator[dict[str, str], dict[str, str]]):
    def codec(self) -> LuaCustomCodec[dict[str, str], dict[str, str]]:
        return LuaCustomCodec(
            communication_lua="-- your lua serde script",
            request_media_type="application/json",
            response_media_type="application/json",
            decode_request=lambda body: {"text": body.decode("utf-8")},
            encode_response=lambda result: (result["text"] + "\n").encode("utf-8"),
        )

    async def process(self, doc: dict[str, str]) -> dict[str, str]:
        return doc
```

## Development Notes

- The package name is `duui_py` (import path); the distribution name is `duui-py` (pip name).
- Run a local syntax check:

```bash
python -m compileall src -q
```
