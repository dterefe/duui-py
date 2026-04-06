"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convbackg."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVBACKGKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convbackg.CONVBACKGKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convbackg.CONVBACKGKO": CONVBACKGKO,
}

__all__ = [
    "CONVBACKGKO",
    "UIMA_TYPE_TO_CLASS",
]
