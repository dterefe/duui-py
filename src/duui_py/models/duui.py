from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from duui_py.models.uima import Annotation, FeatureStructure, SoFa
from duui_py.models.uima_typesystem.texttechnologylab.annotation.types import (
    AnnotatorMetaData,
    DocumentModification,
)


class V1RequestEnvelope(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)
    view: str = ""
    sofa: SoFa
    fs: list[FeatureStructure] = Field(default_factory=list)


class DuuiResult(BaseModel):
    sofa: Optional[SoFa] = None
    annotations: list[Annotation] = Field(default_factory=list)
    feature_structures: list[FeatureStructure] = Field(default_factory=list)
    meta: Optional[AnnotatorMetaData] = None
    modification_meta: Optional[DocumentModification] = None
    errors: list[str] = Field(default_factory=list)


class DuuiError(BaseModel):
    message: str
