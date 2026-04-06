"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convpurp2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVPURP2KO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convpurp2.CONVPURP2KO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convpurp2.CONVPURP2KO": CONVPURP2KO,
}

__all__ = [
    "CONVPURP2KO",
    "UIMA_TYPE_TO_CLASS",
]
