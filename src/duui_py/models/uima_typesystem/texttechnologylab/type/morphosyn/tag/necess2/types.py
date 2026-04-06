"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.necess2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class NECESS2DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.necess2.NECESS2DE"
    value: Optional[str] = None

class NECESS2EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.necess2.NECESS2EN"
    value: Optional[str] = None

class NECESS2JA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.necess2.NECESS2JA"
    value: Optional[str] = None

class NECESS2KO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.necess2.NECESS2KO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.necess2.NECESS2DE": NECESS2DE,
    "org.texttechnologylab.type.morphosyn.tag.necess2.NECESS2EN": NECESS2EN,
    "org.texttechnologylab.type.morphosyn.tag.necess2.NECESS2JA": NECESS2JA,
    "org.texttechnologylab.type.morphosyn.tag.necess2.NECESS2KO": NECESS2KO,
}

__all__ = [
    "NECESS2DE",
    "NECESS2EN",
    "NECESS2JA",
    "NECESS2KO",
    "UIMA_TYPE_TO_CLASS",
]
