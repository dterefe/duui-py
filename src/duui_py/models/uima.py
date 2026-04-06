from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator
from typing import Optional, Any
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


class SoFa(FeatureStructure):
    type: str = "uima.cas.Sofa"
    mimeType: str
    language: str
    data: str | bytes

    @model_validator(mode="after")
    def validate_mime_and_data(self) -> "SoFa":
        validation = get_settings().validation

        if not self.mimeType:
            raise ValueError("sofa.mimeType must not be empty")
        if not self.language:
            raise ValueError("sofa.language must not be empty")

        base = self.mimeType.split(";", 1)[0].strip().lower()
        if validation.strict_mime_validation and ("/" not in base or base.endswith("/*") or "*" in base):
            raise ValueError("sofa.mimeType must be a concrete mime type (no wildcards)")

        is_text = base.startswith("text/")
        if validation.strict_sofa_data_type_validation:
            if is_text and not isinstance(self.data, str):
                raise TypeError("text SofA requires string data")
            if not is_text and not isinstance(self.data, (bytes, bytearray)):
                raise TypeError("non-text SofA requires bytes data")
        return self
