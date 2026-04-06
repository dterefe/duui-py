"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convant."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVANTJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convant.CONVANTJA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convant.CONVANTJA": CONVANTJA,
}

__all__ = [
    "CONVANTJA",
    "UIMA_TYPE_TO_CLASS",
]
