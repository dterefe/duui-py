"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.top."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class TOPJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.top.TOPJA"
    value: Optional[str] = None

class TOPKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.top.TOPKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.top.TOPJA": TOPJA,
    "org.texttechnologylab.type.morphosyn.tag.top.TOPKO": TOPKO,
}

__all__ = [
    "TOPJA",
    "TOPKO",
    "UIMA_TYPE_TO_CLASS",
]
