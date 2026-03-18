from __future__ import annotations

from typing import Any

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


class DomainSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    sofa: SofaSpec
    optional_types: list[str] = Field(default_factory=list)


class ExcludeSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    features: list[str] = Field(default_factory=list)
    ranges: list[str] = Field(default_factory=list)
    types: list[str] = Field(default_factory=list)


class InputTypeSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: str = Field(min_length=1)
    exclude: ExcludeSpec = Field(default_factory=ExcludeSpec)


class InputDesc(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: DomainSpec
    optional_inputs: list[InputTypeSpec] = Field(default_factory=list)


class OutputDesc(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    sofa: SofaSpec
    types: list[str] = Field(default_factory=list)


class AnnotatorDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    input: InputDesc
    output: OutputDesc


class AnnotatorConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    meta: AnnotatorMeta
    description: str = ""
    descriptor: AnnotatorDescriptor
    typesystem_xml_path: str = "TypeSystem.xml"
    parameters_schema: Json = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_descriptor_patterns(self) -> "AnnotatorConfig":
        validation = self.meta.settings.validation
        if validation.strict_mime_validation and validation.strict_descriptor_mime_pattern_validation:
            _validate_mime_pattern(self.descriptor.input.domain.sofa.mimeType)
            _validate_mime_pattern(self.descriptor.output.sofa.mimeType)
        return self


def load_annotator_config(path: str) -> AnnotatorConfig:
    return AnnotatorConfig.model_validate_json(open(path, "rb").read())
