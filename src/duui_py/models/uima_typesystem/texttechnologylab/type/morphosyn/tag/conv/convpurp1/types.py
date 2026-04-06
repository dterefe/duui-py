"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convpurp1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVPURP1KO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convpurp1.CONVPURP1KO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convpurp1.CONVPURP1KO": CONVPURP1KO,
}

__all__ = [
    "CONVPURP1KO",
    "UIMA_TYPE_TO_CLASS",
]
