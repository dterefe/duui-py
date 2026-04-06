"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.spec."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class SPECJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.spec.SPECJA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.spec.SPECJA": SPECJA,
}

__all__ = [
    "SPECJA",
    "UIMA_TYPE_TO_CLASS",
]
