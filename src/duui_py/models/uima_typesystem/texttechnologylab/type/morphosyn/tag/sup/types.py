"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.sup."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class SUPDE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.sup.SUPDE"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.sup.SUPDE": SUPDE,
}

__all__ = [
    "SUPDE",
    "UIMA_TYPE_TO_CLASS",
]
