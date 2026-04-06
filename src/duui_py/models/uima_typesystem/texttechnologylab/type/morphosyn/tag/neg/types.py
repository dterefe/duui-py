"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.neg."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class NEGEPIST(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.neg.NEGEPIST"
    value: Optional[str] = None

class NEGMOD(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.neg.NEGMOD"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.neg.NEGEPIST": NEGEPIST,
    "org.texttechnologylab.type.morphosyn.tag.neg.NEGMOD": NEGMOD,
}

__all__ = [
    "NEGEPIST",
    "NEGMOD",
    "UIMA_TYPE_TO_CLASS",
]
