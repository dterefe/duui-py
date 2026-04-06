"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convcoora."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVCOORAKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convcoora.CONVCOORAKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convcoora.CONVCOORAKO": CONVCOORAKO,
}

__all__ = [
    "CONVCOORAKO",
    "UIMA_TYPE_TO_CLASS",
]
