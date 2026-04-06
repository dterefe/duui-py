"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.expect."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class EXPECTJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.expect.EXPECTJA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.expect.EXPECTJA": EXPECTJA,
}

__all__ = [
    "EXPECTJA",
    "UIMA_TYPE_TO_CLASS",
]
