"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.ger."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class GEREN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.ger.GEREN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.ger.GEREN": GEREN,
}

__all__ = [
    "GEREN",
    "UIMA_TYPE_TO_CLASS",
]
