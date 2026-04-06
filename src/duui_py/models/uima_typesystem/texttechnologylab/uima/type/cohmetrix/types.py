"""Auto-generated UIMA models for namespace: texttechnologylab.uima.type.cohmetrix."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Index(Annotation):
    type: str = "org.texttechnologylab.uima.type.cohmetrix.Index"
    description: Optional[str] = None
    error: Optional[str] = None
    index: Optional[int] = None
    labelTTLab: Optional[str] = None
    labelV2: Optional[str] = None
    labelV3: Optional[str] = None
    typeName: Optional[str] = None
    value: Optional[float] = None
    version: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.uima.type.cohmetrix.Index": Index,
}

__all__ = [
    "Index",
    "UIMA_TYPE_TO_CLASS",
]
