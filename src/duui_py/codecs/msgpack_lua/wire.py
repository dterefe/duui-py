from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, get_args, get_origin
import xml.etree.ElementTree as ET

from duui_py.models import AnnotatorConfig, AnnotatorDescriptor
from duui_py.models.uima import FeatureStructure
from duui_py.models.uima_typesystem import get_uima_model_class
from duui_py.models.uima_typesystem.texttechnologylab.annotation.types import (
    AnnotatorMetaData,
    DocumentModification,
)

PROTOCOL_ALIASES = {
    "auto": "runtime-msgpack-direct",
    "msgpack-row-batch": "msgpack-row-batch",
    "msgpack-columnar": "msgpack-columnar",
    "msgpack-windowed-columnar": "msgpack-windowed-columnar",
    "compressed-msgpack-columnar": "compressed-msgpack-columnar",
    "runtime-msgpack-columnar": "runtime-msgpack-columnar",
    "runtime-msgpack-windowed": "runtime-msgpack-windowed",
    "runtime-msgpack-packed": "runtime-msgpack-packed",
    "runtime-msgpack-compressed": "runtime-msgpack-compressed",
    "runtime-msgpack-direct": "runtime-msgpack-direct",
}
UNSUPPORTED_PROTOCOLS = {"protobuf-batch", "protobuf-windowed"}


@dataclass
class WirePlan:
    protocol: str
    compression: str
    max_rows: int
    max_bytes: int
    flush_ms: int
    type_ids: dict[str, int]
    features: dict[str, list[str]]
    ranges: dict[str, dict[str, str]]
    schema_hash: str

    @classmethod
    def from_config(cls, config: AnnotatorConfig) -> "WirePlan":
        protocol = config.wire.protocol
        if protocol in UNSUPPORTED_PROTOCOLS:
            raise NotImplementedError(
                f"{protocol} is reserved in the protocol matrix but requires a protobuf Java/Lua helper"
            )
        resolved_protocol = PROTOCOL_ALIASES.get(protocol, protocol)
        compression = config.wire.compression
        if resolved_protocol in {"compressed-msgpack-columnar", "runtime-msgpack-compressed"} and compression == "none":
            compression = "zlib"
        if compression not in {"none", "zlib", "zstd"}:
            raise NotImplementedError(
                f"compression={compression} requires an external Java/Lua helper; zlib is the generic built-in option"
            )

        type_ids = _type_ids(config.descriptor)
        features = {
            type_name: _feature_names(type_name, config.wire.features.get(type_name, []))
            for type_name in type_ids
        }
        xml_ranges = _type_system_ranges(config.typesystem_xml_path)
        ranges = {
            type_name: _feature_ranges(type_name, features.get(type_name, []), xml_ranges)
            for type_name in type_ids
        }
        manifest_seed = {
            "version": 2,
            "protocol": resolved_protocol,
            "compression": compression,
            "types": type_ids,
            "features": features,
            "ranges": ranges,
        }
        schema_hash = hashlib.sha256(
            json.dumps(manifest_seed, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:24]
        return cls(
            protocol=resolved_protocol,
            compression=compression,
            max_rows=config.wire.window.maxRows,
            max_bytes=config.wire.window.maxBytes,
            flush_ms=config.wire.window.flushMs,
            type_ids=type_ids,
            features=features,
            ranges=ranges,
            schema_hash=schema_hash,
        )

    @property
    def runtime(self) -> bool:
        return self.protocol.startswith("runtime-")

    @property
    def columnar(self) -> bool:
        return self.protocol in {
            "msgpack-columnar",
            "msgpack-windowed-columnar",
            "compressed-msgpack-columnar",
            "runtime-msgpack-columnar",
            "runtime-msgpack-windowed",
            "runtime-msgpack-packed",
            "runtime-msgpack-compressed",
            "runtime-msgpack-direct",
        }

    @property
    def windowed(self) -> bool:
        return self.protocol in {
            "msgpack-windowed-columnar",
            "runtime-msgpack-windowed",
            "runtime-msgpack-packed",
            "runtime-msgpack-compressed",
            "runtime-msgpack-direct",
        }

    @property
    def compressed(self) -> bool:
        return self.protocol in {"compressed-msgpack-columnar", "runtime-msgpack-compressed"}

    def type_id(self, type_name: str) -> int:
        if type_name not in self.type_ids:
            self.type_ids[type_name] = len(self.type_ids) + 1
            self.features[type_name] = _feature_names(type_name, [])
            self.ranges[type_name] = _feature_ranges(type_name, self.features[type_name], {})
        return self.type_ids[type_name]

    def feature_names(self, item: FeatureStructure) -> list[str]:
        planned = list(self.features.get(item.type, []))
        seen = set(planned)
        for key in item.feature_map().keys():
            if key not in seen:
                planned.append(key)
                seen.add(key)
        return planned

    def manifest(self) -> dict[str, Any]:
        ordered_types = [None] * len(self.type_ids)
        for type_name, type_id in self.type_ids.items():
            ordered_types[type_id - 1] = type_name
        return {
            "version": 2,
            "schemaHash": self.schema_hash,
            "protocol": self.protocol,
            "compression": self.compression,
            "window": {
                "maxRows": self.max_rows,
                "maxBytes": self.max_bytes,
                "flushMs": self.flush_ms,
            },
            "types": ordered_types,
            "features": [
                self.features.get(type_name or "", [])
                for type_name in ordered_types
            ],
            "ranges": [
                [
                    self.ranges.get(type_name or "", {}).get(feature_name, "any")
                    for feature_name in self.features.get(type_name or "", [])
                ]
                for type_name in ordered_types
            ],
        }


def _type_ids(descriptor: AnnotatorDescriptor) -> dict[str, int]:
    seen: dict[str, int] = {}

    def add(type_name: Any) -> None:
        if isinstance(type_name, str) and type_name and type_name not in seen:
            seen[type_name] = len(seen) + 1

    for io_desc in (descriptor.input, descriptor.output):
        for type_list in io_desc.types.values():
            for type_name in type_list:
                add(type_name)
        for domain in ("text", "bytes", "uri", "annotation"):
            spec = getattr(io_desc, domain, None)
            if spec is None:
                continue
            for _, alternative in spec.iter_alternatives():
                for type_list in alternative.types.values():
                    for type_name in type_list:
                        add(type_name)

    add(AnnotatorMetaData.model_fields["type"].default)
    add(DocumentModification.model_fields["type"].default)
    return seen


def _feature_names(type_name: str, projected: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []

    def add(value: Any) -> None:
        if isinstance(value, str) and value and value not in seen:
            seen.add(value)
            out.append(value)

    for value in projected:
        add(value)

    model_cls = get_uima_model_class(type_name)
    if model_cls is not None:
        for field_name, field_info in model_cls.model_fields.items():
            if field_name in {"ref", "type", "features", "begin", "end"}:
                continue
            alias = field_info.alias if isinstance(field_info.alias, str) else field_name
            add(alias)
    return out


def _feature_ranges(type_name: str, features: list[str], xml_ranges: dict[str, dict[str, str]]) -> dict[str, str]:
    model_cls = get_uima_model_class(type_name)
    by_alias: dict[str, str] = {}
    if model_cls is not None:
        for field_name, field_info in model_cls.model_fields.items():
            if field_name in {"ref", "type", "features", "begin", "end"}:
                continue
            alias = field_info.alias if isinstance(field_info.alias, str) else field_name
            by_alias[alias] = _range_from_annotation(field_info.annotation)

    by_xml = xml_ranges.get(type_name, {})
    return {feature: by_xml.get(feature, by_alias.get(feature, "any")) for feature in features}


def _type_system_ranges(path_value: str) -> dict[str, dict[str, str]]:
    path = _resolve_type_system_path(path_value)
    if not path.is_file():
        return {}
    try:
        root = ET.parse(path).getroot()
    except Exception:
        return {}
    declared: dict[str, dict[str, str]] = {}
    parents: dict[str, str] = {}
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}", 1)[0] + "}"
    for type_desc in root.findall(f".//{ns}typeDescription"):
        name = type_desc.findtext(f"{ns}name")
        if not name:
            continue
        supertype_name = type_desc.findtext(f"{ns}supertypeName")
        if supertype_name:
            parents[name] = supertype_name
        ranges: dict[str, str] = {}
        for feature_desc in type_desc.findall(f"./{ns}features/{ns}featureDescription"):
            feature_name = feature_desc.findtext(f"{ns}name")
            range_name = feature_desc.findtext(f"{ns}rangeTypeName")
            if feature_name and range_name:
                ranges[feature_name] = _range_from_uima_name(range_name)
        declared[name] = ranges

    resolved: dict[str, dict[str, str]] = {}

    def resolve(type_name: str, stack: set[str]) -> dict[str, str]:
        if type_name in resolved:
            return resolved[type_name]
        if type_name in stack:
            return dict(declared.get(type_name, {}))
        stack.add(type_name)
        ranges: dict[str, str] = {}
        parent = parents.get(type_name)
        if parent:
            ranges.update(resolve(parent, stack))
        ranges.update(declared.get(type_name, {}))
        stack.remove(type_name)
        resolved[type_name] = ranges
        return ranges

    for type_name in declared:
        resolve(type_name, set())
    return resolved


def _resolve_type_system_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute() or path.is_file():
        return path
    for entry in sys.path:
        if not entry:
            continue
        candidate = Path(entry) / path
        if candidate.is_file():
            return candidate
    return path


def _range_from_uima_name(range_name: str) -> str:
    return {
        "uima.cas.String": "string",
        "uima.cas.Boolean": "boolean",
        "uima.cas.Byte": "byte",
        "uima.cas.Short": "short",
        "uima.cas.Integer": "integer",
        "uima.cas.Long": "long",
        "uima.cas.Float": "float",
        "uima.cas.Double": "double",
    }.get(range_name, "any")


def _range_from_annotation(annotation: Any) -> str:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is list:
        return "array"
    if args:
        non_none = [arg for arg in args if arg is not type(None)]
        if len(non_none) == 1:
            return _range_from_annotation(non_none[0])
    if annotation is str:
        return "string"
    if annotation is bool:
        return "boolean"
    if annotation is int:
        return "long"
    if annotation is float:
        return "double"
    return "any"
