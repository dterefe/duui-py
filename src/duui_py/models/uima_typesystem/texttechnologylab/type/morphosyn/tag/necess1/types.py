"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.necess1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class NECESS1DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.necess1.NECESS1DE"
    value: Optional[str] = None

class NECESS1EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.necess1.NECESS1EN"
    value: Optional[str] = None

class NECESS1JA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.necess1.NECESS1JA"
    value: Optional[str] = None

class NECESS1KO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.necess1.NECESS1KO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.necess1.NECESS1DE": NECESS1DE,
    "org.texttechnologylab.type.morphosyn.tag.necess1.NECESS1EN": NECESS1EN,
    "org.texttechnologylab.type.morphosyn.tag.necess1.NECESS1JA": NECESS1JA,
    "org.texttechnologylab.type.morphosyn.tag.necess1.NECESS1KO": NECESS1KO,
}

__all__ = [
    "NECESS1DE",
    "NECESS1EN",
    "NECESS1JA",
    "NECESS1KO",
    "UIMA_TYPE_TO_CLASS",
]
