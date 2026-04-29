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


class FeatureStructure(BaseModel):
    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    ref: Optional[int] = None
    type: str
    begin: Optional[int] = None
    end: Optional[int] = Field(default=None, alias="end")
    features: dict[str, UimaValue] = Field(default_factory=dict)

    @classmethod
    def _core_field_names(cls) -> set[str]:
        return {"ref", "type", "features", "begin", "end"}

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
        merged = {str(k): normalize_uima_value(v) for k, v in self.features.items()}

        for field_name, field_info in self.__class__.model_fields.items():
            if field_name in self._core_field_names():
                continue

            value = getattr(self, field_name, None)
            if value is None:
                continue

            feature_name = field_info.alias if isinstance(field_info.alias, str) else field_name
            merged[feature_name] = normalize_uima_value(value)

        return merged

    @model_validator(mode="after")
    def _sync_features_field(self) -> "FeatureStructure":
        existing_features = (
            {str(k): normalize_uima_value(v) for k, v in self.features.items()}
            if isinstance(self.features, dict)
            else {}
        )
        for field_name, field_info in self.__class__.model_fields.items():
            if field_name in self._core_field_names():
                continue

            current_value = getattr(self, field_name, None)
            if current_value is not None:
                continue

            aliases = [field_name]
            if isinstance(field_info.alias, str) and field_info.alias != field_name:
                aliases.append(field_info.alias)
            for alias in aliases:
                if alias in existing_features:
                    object.__setattr__(self, field_name, normalize_uima_value(existing_features[alias]))
                    break

        object.__setattr__(self, "features", self.feature_map())
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
