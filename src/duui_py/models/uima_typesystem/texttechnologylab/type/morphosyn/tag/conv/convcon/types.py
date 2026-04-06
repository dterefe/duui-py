"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convcon."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVCONKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convcon.CONVCONKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convcon.CONVCONKO": CONVCONKO,
}

__all__ = [
    "CONVCONKO",
    "UIMA_TYPE_TO_CLASS",
]
