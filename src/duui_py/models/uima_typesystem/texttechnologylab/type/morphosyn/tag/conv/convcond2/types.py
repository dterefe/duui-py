"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convcond2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVCOND2JA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convcond2.CONVCOND2JA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convcond2.CONVCOND2JA": CONVCOND2JA,
}

__all__ = [
    "CONVCOND2JA",
    "UIMA_TYPE_TO_CLASS",
]
