"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.inf."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class INFDE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.inf.INFDE"
    value: Optional[str] = None

class INFEN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.inf.INFEN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.inf.INFDE": INFDE,
    "org.texttechnologylab.type.morphosyn.tag.inf.INFEN": INFEN,
}

__all__ = [
    "INFDE",
    "INFEN",
    "UIMA_TYPE_TO_CLASS",
]
