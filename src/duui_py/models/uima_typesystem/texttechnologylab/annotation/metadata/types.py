"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.metadata."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ViewReference(Annotation):
    type: str = "org.texttechnologylab.annotation.metadata.ViewReference"
    SourceBegin: Optional[int] = None
    SourceEnd: Optional[int] = None
    SourceType: Optional[str] = None
    SourceViewName: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.metadata.ViewReference": ViewReference,
}

__all__ = [
    "ViewReference",
    "UIMA_TYPE_TO_CLASS",
]
