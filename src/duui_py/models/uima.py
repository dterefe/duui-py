from __future__ import annotations

from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator
from typing_extensions import TypedDict

from duui_py.settings import get_settings

FeatureStructureRef = TypedDict("FeatureStructureRef", {"$ref": int})
PackedFloat32Array = TypedDict("PackedFloat32Array", {"$f32": bytes})
PackedFloat64Array = TypedDict("PackedFloat64Array", {"$f64": bytes})
PackedInt32Array = TypedDict("PackedInt32Array", {"$i32": bytes})
PackedInt64Array = TypedDict("PackedInt64Array", {"$i64": bytes})

# Simplified type to avoid recursion issues in Pydantic
# Original recursive type caused infinite recursion
UimaValue = Any
_CORE_FIELD_NAMES = frozenset({"ref", "type", "features", "begin", "end"})
_FEATURE_FIELD_CACHE: dict[type, tuple[tuple[str, str], ...]] = {}
_FEATURE_LOOKUP_CACHE: dict[type, dict[str, tuple[str, str]]] = {}
_TYPE_NAME_CACHE: dict[type, str] = {}


def is_feature_structure_ref(value: Any) -> bool:
    return isinstance(value, dict) and set(value.keys()) == {"$ref"} and isinstance(value.get("$ref"), int)


def normalize_uima_value(value: Any) -> UimaValue:
    # Preserve explicit FS references and normalize numeric id.
    if isinstance(value, dict) and "$ref" in value and len(value) == 1:
        try:
            return {"$ref": int(value["$ref"])}
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"invalid $ref value: {value!r}") from exc

    if isinstance(value, list):
        return [normalize_uima_value(item) for item in value]

    if isinstance(value, dict):
        return {str(k): normalize_uima_value(v) for k, v in value.items()}

    return value


def uima_type_name(model_or_type: Any) -> str:
    if isinstance(model_or_type, str):
        return model_or_type
    model_fields = getattr(model_or_type, "model_fields", None)
    if isinstance(model_fields, dict):
        field = model_fields.get("type")
        default = getattr(field, "default", None)
        if isinstance(default, str):
            return default
    type_value = getattr(model_or_type, "type", None)
    if isinstance(type_value, str):
        return type_value
    raise TypeError(f"cannot resolve UIMA type name from {model_or_type!r}")


class FeatureStructure(BaseModel):
    model_config = ConfigDict(validate_assignment=False, populate_by_name=True)

    ref: Optional[int] = None
    type: str
    begin: Optional[int] = None
    end: Optional[int] = Field(default=None, alias="end")
    features: dict[str, UimaValue] = Field(default_factory=dict)

    @classmethod
    def _core_field_names(cls) -> set[str]:
        return set(_CORE_FIELD_NAMES)

    def __getattr__(self, name: str) -> Any:
        feature = _feature_lookup(self.__class__).get(name)
        if feature is not None:
            field_name, feature_name = feature
            model_fields = self.__class__.model_fields
            if field_name in model_fields:
                data = object.__getattribute__(self, "__dict__")
                if field_name in data:
                    return data[field_name]
                features = data.get("features")
                if isinstance(features, dict):
                    if feature_name in features:
                        return features[feature_name]
                    if name in features:
                        return features[name]
                return None
        return super().__getattr__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name in _CORE_FIELD_NAMES:
            return
        feature = _feature_lookup(self.__class__).get(name)
        if feature is None:
            return
        _, feature_name = feature
        current = getattr(self, "features", None)
        features = dict(current) if isinstance(current, dict) else {}
        if value is None:
            features.pop(feature_name, None)
        else:
            features[feature_name] = _normalize_if_needed(value)
        object.__setattr__(self, "features", features)

    def __init__(self, **values: Any) -> None:
        if _fast_constructor_enabled(self.__class__):
            _init_model_state(self, _fast_model_data(self.__class__, values))
            return
        self.__pydantic_validator__.validate_python(values, self_instance=self)

    @classmethod
    @model_validator(mode="before")
    def _inflate_typed_fields_from_features(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        features = data.get("features")
        if not isinstance(features, dict):
            return data

        inflated = dict(data)
        for field_name, field_info in cls.model_fields.items():
            if field_name in cls._core_field_names():
                continue
            aliases = [field_name]
            if isinstance(field_info.alias, str) and field_info.alias != field_name:
                aliases.append(field_info.alias)

            if any(alias in inflated for alias in aliases):
                continue

            for alias in aliases:
                if alias in features:
                    inflated[field_name] = normalize_uima_value(features[alias])
                    break

        return inflated

    def feature_map(self) -> dict[str, UimaValue]:
        if isinstance(self.features, dict):
            return self.features
        return {}

    @model_validator(mode="after")
    def _sync_features_field(self) -> "FeatureStructure":
        existing_features = {
            str(k): _normalize_if_needed(v)
            for k, v in self.features.items()
        } if isinstance(self.features, dict) else {}
        for field_name, field_info in self.__class__.model_fields.items():
            if field_name in self._core_field_names():
                continue

            current_value = getattr(self, field_name, None)
            alias = field_info.alias if isinstance(field_info.alias, str) else field_name
            if current_value is not None:
                existing_features[alias] = _normalize_if_needed(current_value)
                continue

            aliases = [field_name]
            if alias != field_name:
                aliases.append(alias)
            for alias in aliases:
                if alias in existing_features:
                    object.__setattr__(self, field_name, existing_features[alias])
                    break

        object.__setattr__(self, "features", existing_features)
        return self

    @model_serializer(mode="wrap")
    def _serialize_with_generic_features(self, handler):
        out = handler(self)
        if not isinstance(out, dict):
            return out

        out["features"] = self.feature_map()

        for field_name, field_info in self.__class__.model_fields.items():
            if field_name in self._core_field_names():
                continue
            out.pop(field_name, None)
            if isinstance(field_info.alias, str):
                out.pop(field_info.alias, None)

        return out


class Annotation(FeatureStructure):
    begin: int
    end: int = Field(alias="end")


class SoFaBase(FeatureStructure):
    type: str = "uima.cas.Sofa"
    mimeType: str
    language: str

    @model_validator(mode="after")
    def validate_mime(self) -> "SoFaBase":
        validation = get_settings().validation

        if not self.mimeType:
            raise ValueError("sofa.mimeType must not be empty")
        if not self.language:
            raise ValueError("sofa.language must not be empty")

        base = self.mimeType.split(";", 1)[0].strip().lower()
        if validation.strict_mime_validation and ("/" not in base or base.endswith("/*") or "*" in base):
            raise ValueError("sofa.mimeType must be a concrete mime type (no wildcards)")
        return self


class SoFaText(SoFaBase):
    kind: Literal["text"] = "text"
    text: str

    @model_validator(mode="after")
    def validate_text(self) -> "SoFaText":
        validation = get_settings().validation
        if validation.strict_sofa_data_type_validation and not isinstance(self.text, str):
            raise TypeError("SoFaText.text must be string")
        return self


class SoFaBytes(SoFaBase):
    kind: Literal["bytes"] = "bytes"
    bytes: bytes

    @model_validator(mode="after")
    def validate_bytes(self) -> "SoFaBytes":
        validation = get_settings().validation
        if validation.strict_sofa_data_type_validation and not isinstance(self.bytes, (bytes, bytearray)):
            raise TypeError("SoFaBytes.bytes must be bytes")
        return self


class SoFaURI(SoFaBase):
    kind: Literal["uri"] = "uri"
    uri: str


class SoFaAnnotationSpans(SoFaBase):
    kind: Literal["annotation_spans"] = "annotation_spans"
    annotationType: str
    spans: list[str] = Field(default_factory=list)


SoFa = Annotated[SoFaText | SoFaBytes | SoFaURI | SoFaAnnotationSpans, Field(discriminator="kind")]


def _feature_fields(model_cls: type[FeatureStructure]) -> tuple[tuple[str, str], ...]:
    cached = _FEATURE_FIELD_CACHE.get(model_cls)
    if cached is not None:
        return cached
    explicit = getattr(model_cls, "__duui_feature_fields__", None)
    if isinstance(explicit, tuple):
        cached = tuple((str(field), str(feature)) for field, feature in explicit)
        _FEATURE_FIELD_CACHE[model_cls] = cached
        return cached
    core_names = model_cls._core_field_names()
    fields: list[tuple[str, str]] = []
    for field_name, field_info in model_cls.model_fields.items():
        if field_name in core_names:
            continue
        feature_name = field_info.alias if isinstance(field_info.alias, str) else field_name
        fields.append((field_name, feature_name))
    cached = tuple(fields)
    _FEATURE_FIELD_CACHE[model_cls] = cached
    return cached


def _feature_lookup(model_cls: type[FeatureStructure]) -> dict[str, tuple[str, str]]:
    cached = _FEATURE_LOOKUP_CACHE.get(model_cls)
    if cached is not None:
        return cached
    out: dict[str, tuple[str, str]] = {}
    for field_name, feature_name in _feature_fields(model_cls):
        pair = (field_name, feature_name)
        out[field_name] = pair
        out[feature_name] = pair
    _FEATURE_LOOKUP_CACHE[model_cls] = out
    return out


def _fast_constructor_enabled(model_cls: type[FeatureStructure]) -> bool:
    return not model_cls.__name__.startswith("SoFa")


def _init_model_state(target: FeatureStructure, data: dict[str, Any]) -> None:
    object.__setattr__(target, "__dict__", data)
    object.__setattr__(target, "__pydantic_fields_set__", set(data))
    object.__setattr__(target, "__pydantic_extra__", None)
    object.__setattr__(target, "__pydantic_private__", None)


def _fast_model_data(model_cls: type[FeatureStructure], values: dict[str, Any]) -> dict[str, Any]:
    features = values.pop("features", None)
    type_name = values.pop("type", None) or _type_name(model_cls)
    data: dict[str, Any] = {
        "ref": values.pop("ref", None),
        "type": type_name,
        "begin": values.pop("begin", None),
        "end": values.pop("end", None),
    }

    feature_values: dict[str, Any] = {}
    features_from_map = False
    if isinstance(features, dict):
        features_from_map = bool(features)
        feature_values.update(
            {
                str(key): _normalize_if_needed(value)
                for key, value in features.items()
                if value is not None
            }
        )

    lookup = _feature_lookup(model_cls)
    model_field_names = model_cls.model_fields
    for raw_name, raw_value in values.items():
        if raw_value is None:
            continue
        field_name, feature_name = lookup.get(raw_name, (raw_name, raw_name))
        value = _normalize_if_needed(raw_value)
        if field_name in model_field_names:
            data[field_name] = value
        if field_name not in _CORE_FIELD_NAMES:
            feature_values[feature_name] = value

    if features_from_map:
        for field_name, feature_name in _feature_fields(model_cls):
            if field_name not in data and feature_name in feature_values:
                data[field_name] = feature_values[feature_name]

    data["features"] = feature_values
    return data


def _type_name(model_cls: type[FeatureStructure]) -> str:
    cached = _TYPE_NAME_CACHE.get(model_cls)
    if cached is not None:
        return cached
    explicit = getattr(model_cls, "__duui_type_name__", None)
    if isinstance(explicit, str) and explicit:
        _TYPE_NAME_CACHE[model_cls] = explicit
        return explicit
    type_field = model_cls.model_fields.get("type")
    if type_field is not None and isinstance(type_field.default, str):
        _TYPE_NAME_CACHE[model_cls] = type_field.default
        return type_field.default
    fallback = model_cls.__name__
    _TYPE_NAME_CACHE[model_cls] = fallback
    return fallback


def _normalize_if_needed(value: Any) -> UimaValue:
    if value is None or isinstance(value, (str, int, float, bool, bytes)):
        return value
    return normalize_uima_value(value)


def sofa_default_for_mime(*, mime_type: str, language: str) -> SoFa:
    base = mime_type.split(";", 1)[0].strip().lower()
    if base.startswith("text/"):
        return SoFaText(mimeType=mime_type, language=language, text="")
    if base == "application/uri":
        return SoFaURI(mimeType=mime_type, language=language, uri="")
    if base.startswith("application/x-uima-annotation-spans"):
        return SoFaAnnotationSpans(mimeType=mime_type, language=language, annotationType="", spans=[])
    return SoFaBytes(mimeType=mime_type, language=language, bytes=b"")


def sofa_from_wire(*, mime_type: str, language: str, data: Any, annotation_type: str | None = None, spans: list[str] | None = None) -> SoFa:
    base = mime_type.split(";", 1)[0].strip().lower()
    if base.startswith("text/"):
        if not isinstance(data, str):
            raise TypeError("text SofA requires string data")
        return SoFaText(mimeType=mime_type, language=language, text=data)
    if base == "application/uri":
        if not isinstance(data, str):
            raise TypeError("uri SofA requires string uri")
        return SoFaURI(mimeType=mime_type, language=language, uri=data)
    if base.startswith("application/x-uima-annotation-spans"):
        return SoFaAnnotationSpans(
            mimeType=mime_type,
            language=language,
            annotationType=annotation_type or "",
            spans=spans or ([] if not isinstance(data, list) else [str(x) for x in data]),
        )
    if isinstance(data, str):
        try:
            data = data.encode("latin-1")
        except UnicodeEncodeError:
            # Lua msgpack transport currently serializes bytes as string payload.
            # If unpacked text contains non-latin1 code points, utf-8 round-trip
            # preserves the original byte stream for valid utf-8 sequences.
            data = data.encode("utf-8")
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("bytes SofA requires bytes data")
    return SoFaBytes(mimeType=mime_type, language=language, bytes=bytes(data))


def sofa_to_wire_data(sofa: SoFa) -> Any:
    if isinstance(sofa, SoFaText):
        return sofa.text
    if isinstance(sofa, SoFaBytes):
        return sofa.bytes.decode("latin-1")
    if isinstance(sofa, SoFaURI):
        return sofa.uri
    return list(sofa.spans)


def sofa_annotation_type(sofa: SoFa) -> str | None:
    if isinstance(sofa, SoFaAnnotationSpans):
        return sofa.annotationType
    return None


def sofa_kind(sofa: SoFa) -> str:
    if isinstance(sofa, SoFaText):
        return "text"
    if isinstance(sofa, SoFaBytes):
        return "bytes"
    if isinstance(sofa, SoFaURI):
        return "uri"
    return "annotation_spans"


def sofa_text_value(sofa: SoFa) -> str | None:
    if isinstance(sofa, SoFaText):
        return sofa.text
    return None


def sofa_bytes_value(sofa: SoFa) -> bytes | None:
    if isinstance(sofa, SoFaBytes):
        return sofa.bytes
    return None
