"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convcond1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVCOND1JA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convcond1.CONVCOND1JA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convcond1.CONVCOND1JA": CONVCOND1JA,
}

__all__ = [
    "CONVCOND1JA",
    "UIMA_TYPE_TO_CLASS",
]
