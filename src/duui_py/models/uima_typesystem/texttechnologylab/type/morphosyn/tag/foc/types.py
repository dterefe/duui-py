"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.foc."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class FOCJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.foc.FOCJA"
    value: Optional[str] = None

class FOCKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.foc.FOCKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.foc.FOCJA": FOCJA,
    "org.texttechnologylab.type.morphosyn.tag.foc.FOCKO": FOCKO,
}

__all__ = [
    "FOCJA",
    "FOCKO",
    "UIMA_TYPE_TO_CLASS",
]
