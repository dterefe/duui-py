"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp.ppcoora."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PPCOORAJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.ppcoora.PPCOORAJA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp.ppcoora.PPCOORAJA": PPCOORAJA,
}

__all__ = [
    "PPCOORAJA",
    "UIMA_TYPE_TO_CLASS",
]
