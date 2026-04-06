"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp.ppcoord."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PPCOORDJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.ppcoord.PPCOORDJA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp.ppcoord.PPCOORDJA": PPCOORDJA,
}

__all__ = [
    "PPCOORDJA",
    "UIMA_TYPE_TO_CLASS",
]
