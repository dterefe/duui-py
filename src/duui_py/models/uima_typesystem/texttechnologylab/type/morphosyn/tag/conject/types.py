"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conject."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONJECTKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conject.CONJECTKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conject.CONJECTKO": CONJECTKO,
}

__all__ = [
    "CONJECTKO",
    "UIMA_TYPE_TO_CLASS",
]
