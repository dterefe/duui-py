from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Json = dict[str, Any]


def _validate_mime_pattern(value: str) -> None:
    for raw in value.split("|"):
        base = raw.split(";", 1)[0].strip().lower()
        if not base:
            raise ValueError("sofa.mimeType must not contain empty alternatives")
        if "/" not in base:
            raise ValueError("sofa.mimeType must contain '/'")
        major, minor = base.split("/", 1)
        if not major or not minor:
            raise ValueError("sofa.mimeType must be major/minor or major/*")
        if minor == "*":
            continue
        if "*" in minor:
            raise ValueError("sofa.mimeType wildcard only allowed as major/*")


class ValidationSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    strict_mime_validation: bool = True
    strict_input_mime_check: bool = True
    strict_output_mime_check: bool = True
    strict_sofa_data_type_validation: bool = True
    strict_descriptor_mime_pattern_validation: bool = True


class LimitSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request_max_bytes: int | None = Field(default=None, ge=1)
    response_max_bytes: int | None = Field(default=None, ge=1)


class ErrorSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    fail_on_codec_error: bool = True
    include_validation_details: bool = True


class LoggingSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = True
    stream_timeout_minutes: int = Field(default=5, ge=1, le=60)
    max_queue_size: int = Field(default=1000, ge=10, le=10000)
    metrics_collection_interval_seconds: int = Field(default=5, ge=1, le=300)
    include_system_metrics: bool = True
    include_process_metrics: bool = True
    include_disk_metrics: bool = True
    include_network_metrics: bool = True


class FrameworkSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    validation: ValidationSettings = Field(default_factory=ValidationSettings)
    limits: LimitSettings = Field(default_factory=LimitSettings)
    errors: ErrorSettings = Field(default_factory=ErrorSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)


class AnnotatorMeta(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    implementation_lang: str = "Python"
    meta: Json = Field(default_factory=dict)
    settings: FrameworkSettings = Field(default_factory=FrameworkSettings)


class SofaSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    mimeType: str = Field(min_length=1)
    language: str = Field(min_length=1)


class SofaModeSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    mimeType: str | None = None
    language: str | None = None
    targetView: str | None = None


class InputSofaSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    text: SofaModeSpec | None = None
    uri: SofaModeSpec | None = None
    bytes: SofaModeSpec | None = None
    annotation: list[str] = Field(default_factory=list)
    selections: list[str] = Field(default_factory=list)

    def annotation_types(self) -> list[str]:
        merged = list(self.annotation) + list(self.selections)
        dedup: list[str] = []
        seen: set[str] = set()
        for entry in merged:
            if entry not in seen:
                seen.add(entry)
                dedup.append(entry)
        return dedup

    def default_mime_type(self) -> str:
        for mode in (self.text, self.bytes, self.uri):
            if mode is not None and mode.mimeType:
                return mode.mimeType
        return "text/plain; charset=utf-8"

    def default_language(self) -> str:
        for mode in (self.text, self.bytes, self.uri):
            if mode is not None and mode.language:
                return mode.language
        return "x-unspecified"


class OutputSofaSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    text: SofaModeSpec | None = None
    uri: SofaModeSpec | None = None
    bytes: SofaModeSpec | None = None

    def default_mime_type(self) -> str:
        for mode in (self.text, self.bytes, self.uri):
            if mode is not None and mode.mimeType:
                return mode.mimeType
        return "text/plain; charset=utf-8"

    def default_language(self) -> str:
        for mode in (self.text, self.bytes, self.uri):
            if mode is not None and mode.language:
                return mode.language
        return "x-unspecified"


class InputDesc(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    sofa: InputSofaSpec = Field(default_factory=InputSofaSpec)
    types: list[str] = Field(default_factory=list)

    def default_mime_type(self) -> str:
        return self.sofa.default_mime_type()

    def default_language(self) -> str:
        return self.sofa.default_language()


class OutputDesc(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    sofa: OutputSofaSpec = Field(default_factory=OutputSofaSpec)
    types: list[str] = Field(default_factory=list)

    def default_mime_type(self) -> str:
        return self.sofa.default_mime_type()

    def default_language(self) -> str:
        return self.sofa.default_language()


class AnnotatorDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    input: InputDesc
    output: OutputDesc

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_descriptor_shape(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)

        input_part = normalized.get("input")
        if isinstance(input_part, dict) and "domain" in input_part:
            domain = input_part.get("domain", {})
            domain_sofa = domain.get("sofa", {}) if isinstance(domain, dict) else {}
            optional_types = list(domain.get("optional_types", [])) if isinstance(domain, dict) else []
            optional_inputs = input_part.get("optional_inputs", [])
            optional_input_types = [
                item.get("type")
                for item in optional_inputs
                if isinstance(item, dict) and isinstance(item.get("type"), str)
            ]
            merged_types = [*optional_types, *optional_input_types]
            dedup_types: list[str] = []
            seen: set[str] = set()
            for item in merged_types:
                if item not in seen:
                    seen.add(item)
                    dedup_types.append(item)

            normalized["input"] = {
                "sofa": {
                    "text": {
                        "mimeType": domain_sofa.get("mimeType", "text/plain; charset=utf-8"),
                        "language": domain_sofa.get("language", "x-unspecified"),
                    },
                    "annotation": dedup_types,
                },
                "types": dedup_types,
            }

        output_part = normalized.get("output")
        if isinstance(output_part, dict):
            sofa_part = output_part.get("sofa")
            if isinstance(sofa_part, dict) and (
                "mimeType" in sofa_part or "language" in sofa_part or "targetView" in sofa_part
            ):
                normalized["output"] = {
                    "sofa": {
                        "text": {
                            "mimeType": sofa_part.get("mimeType"),
                            "language": sofa_part.get("language"),
                            "targetView": sofa_part.get("targetView"),
                        }
                    },
                    "types": list(output_part.get("types", [])),
                }

        return normalized


class AnnotatorConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    meta: AnnotatorMeta
    description: str = ""
    descriptor: AnnotatorDescriptor
    typesystem_xml_path: str = "TypeSystem.xml"
    parameters_schema: Json = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_descriptor_patterns(self) -> Self:
        validation = self.meta.settings.validation
        if validation.strict_mime_validation and validation.strict_descriptor_mime_pattern_validation:
            input_mime = self.descriptor.input.default_mime_type()
            output_mime = self.descriptor.output.default_mime_type()
            if input_mime:
                _validate_mime_pattern(input_mime)
            if output_mime:
                _validate_mime_pattern(output_mime)
        return self


def load_annotator_config(path: str) -> AnnotatorConfig:
    return AnnotatorConfig.model_validate_json(open(path, "rb").read())
