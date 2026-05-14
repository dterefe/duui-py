from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Json = dict[str, Any]


_ALLOWED_DOMAINS = ("text", "bytes", "uri", "annotation")


def _dedup_keep_order(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _validate_mime_pattern(value: str) -> None:
    for raw in value.split("|"):
        base = raw.split(";", 1)[0].strip().lower()
        if not base:
            raise ValueError("mimeType must not contain empty alternatives")
        if "/" not in base:
            raise ValueError("mimeType must contain '/'")
        major, minor = base.split("/", 1)
        if not major or not minor:
            raise ValueError("mimeType must be major/minor")
        if "*" in base:
            raise ValueError("wildcards are not allowed in active descriptor mimeType entries")


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


class Domain(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    mimeType: str | None = None
    languages: list[str] = Field(default_factory=list)
    types: dict[str, list[str]] = Field(default_factory=dict)


DomainAlternative = Domain


class DomainSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    languages: list[str] = Field(default_factory=list)
    types: dict[str, list[str]] = Field(default_factory=dict)
    default: Domain | None = None
    aliases: dict[str, Domain] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def collect_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        aliases = dict(normalized.get("aliases") or {})
        for key, value in list(normalized.items()):
            if key in {"languages", "types", "default", "aliases"}:
                continue
            if isinstance(value, dict):
                aliases[key] = value
                normalized.pop(key)
        normalized["aliases"] = aliases
        return normalized

    def iter_alternatives(self) -> list[tuple[str, Domain]]:
        out: list[tuple[str, Domain]] = []
        if self.default is not None:
            out.append(("default", self.default))
        for name in sorted(self.aliases):
            out.append((name, self.aliases[name]))
        return out

    def get_alternative(self, alias: str) -> Domain | None:
        if alias == "default":
            return self.default
        return self.aliases.get(alias)


class ResolvedDomainSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: str
    alias: str
    mimeType: str | None = None
    languages: list[str] = Field(default_factory=list)
    types: dict[str, list[str]] = Field(default_factory=dict)


class IODescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    languages: list[str] = Field(default_factory=list)
    types: dict[str, list[str]] = Field(default_factory=dict)
    text: DomainSpec | None = None
    bytes: DomainSpec | None = None
    uri: DomainSpec | None = None
    annotation: DomainSpec | None = None

    def _domain_spec(self, domain: str) -> DomainSpec | None:
        if domain not in _ALLOWED_DOMAINS:
            return None
        return getattr(self, domain)

    def resolve(self, domain: str, alias: str = "default") -> ResolvedDomainSpec:
        spec = self._domain_spec(domain)
        if spec is None:
            raise ValueError(f"descriptor domain '{domain}' not configured")
        alt = spec.get_alternative(alias)
        if alt is None:
            raise ValueError(f"descriptor domain '{domain}' alias '{alias}' not configured")

        merged_types: dict[str, list[str]] = {}
        for source in (self.types, spec.types, alt.types):
            for key, candidates in source.items():
                merged_types[key] = _dedup_keep_order(list(merged_types.get(key, [])) + list(candidates))

        merged_languages = _dedup_keep_order(list(self.languages) + list(spec.languages) + list(alt.languages))
        return ResolvedDomainSpec(
            domain=domain,
            alias=alias,
            mimeType=alt.mimeType,
            languages=merged_languages,
            types=merged_types,
        )

    def first_available(self) -> ResolvedDomainSpec | None:
        for domain in _ALLOWED_DOMAINS:
            spec = self._domain_spec(domain)
            if spec is None:
                continue
            if spec.default is not None:
                return self.resolve(domain, "default")
            alternatives = spec.iter_alternatives()
            if alternatives:
                return self.resolve(domain, alternatives[0][0])
        return None


class AnnotatorDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    input: IODescriptor
    output: IODescriptor


IODescriptorVNext = IODescriptor


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
        if not (validation.strict_mime_validation and validation.strict_descriptor_mime_pattern_validation):
            return self

        for io_desc in (self.descriptor.input, self.descriptor.output):
            for domain in _ALLOWED_DOMAINS:
                spec = getattr(io_desc, domain)
                if spec is None:
                    continue
                for _, alt in spec.iter_alternatives():
                    if alt.mimeType:
                        _validate_mime_pattern(alt.mimeType)
        return self


def load_annotator_config(path: str) -> AnnotatorConfig:
    return AnnotatorConfig.model_validate_json(open(path, "rb").read())
