"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convcoor."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVCOORJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convcoor.CONVCOORJA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convcoor.CONVCOORJA": CONVCOORJA,
}

__all__ = [
    "CONVCOORJA",
    "UIMA_TYPE_TO_CLASS",
]
