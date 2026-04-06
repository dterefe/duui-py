"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convneg."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVNEGJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convneg.CONVNEGJA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convneg.CONVNEGJA": CONVNEGJA,
}

__all__ = [
    "CONVNEGJA",
    "UIMA_TYPE_TO_CLASS",
]
