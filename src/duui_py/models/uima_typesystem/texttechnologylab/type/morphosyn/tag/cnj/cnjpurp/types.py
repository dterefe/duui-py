"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjpurp."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJPURPEN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjpurp.CNJPURPEN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjpurp.CNJPURPEN": CNJPURPEN,
}

__all__ = [
    "CNJPURPEN",
    "UIMA_TYPE_TO_CLASS",
]
