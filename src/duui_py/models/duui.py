from __future__ import annotations

from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any

from duui_py.models.uima import Annotation, UimaValue
from duui_py.settings import get_settings


class SofaPayload(BaseModel):
    mimeType: str
    language: str
    data: str | bytes

    @model_validator(mode="after")
    def validate_mime_and_data(self) -> "SofaPayload":
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


class FsRec(BaseModel):
    id: int
    ref: Optional[int] = None
    type: str
    begin: Optional[int] = None
    end: Optional[int] = Field(default=None, alias="end")
    features: dict[str, UimaValue] = Field(default_factory=dict)


class AnnotationMeta(BaseModel):
    name: str
    version: str
    modelName: Optional[str] = None
    modelVersion: Optional[str] = None


class DocumentModification(BaseModel):
    user: str
    timestamp: int
    comment: str


class DuuiDocument(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)
    view: str = ""
    sofa: SofaPayload
    fs: list[FsRec] = Field(default_factory=list)

    @property
    def text(self) -> Optional[str]:
        return self.sofa.data if isinstance(self.sofa.data, str) else None

    @property
    def bytes(self) -> Optional[bytes]:
        return self.sofa.data if isinstance(self.sofa.data, (bytes, bytearray)) else None


class FeatureStructureKeyRef(BaseModel):
    key: str


# Simplified to avoid recursion issues in Pydantic
# Original: UimaValue | FeatureStructureKeyRef | list["UimaValueOrKeyRef"]
UimaValueOrKeyRef = Any


class FeatureStructureNode(BaseModel):
    key: str
    ref: Optional[int] = None
    type: str
    begin: Optional[int] = None
    end: Optional[int] = Field(default=None, alias="end")
    features: dict[str, UimaValueOrKeyRef] = Field(default_factory=dict)


class DuuiResult(BaseModel):
    sofa: Optional[SofaPayload] = None
    annotations: list[Annotation] = Field(default_factory=list)
    feature_structures: list[FeatureStructureNode] = Field(default_factory=list)
    meta: Optional[AnnotationMeta] = None
    modification_meta: Optional[DocumentModification] = None
    errors: list[str] = Field(default_factory=list)
