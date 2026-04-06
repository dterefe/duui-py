"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.search."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ReferenceText(Annotation):
    type: str = "org.texttechnologylab.annotation.search.ReferenceText"
    dateTime: Optional[str] = None
    group: Optional[str] = None
    infos: Optional[str] = None
    methods: Optional[str] = None
    priority: Optional[int] = None
    reference: Optional[UimaValue] = None
    success: Optional[bool] = None
    summary: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.search.ReferenceText": ReferenceText,
}

__all__ = [
    "ReferenceText",
    "UIMA_TYPE_TO_CLASS",
]
