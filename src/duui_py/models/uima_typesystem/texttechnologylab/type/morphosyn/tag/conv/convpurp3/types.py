"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convpurp3."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVPURP3KO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convpurp3.CONVPURP3KO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convpurp3.CONVPURP3KO": CONVPURP3KO,
}

__all__ = [
    "CONVPURP3KO",
    "UIMA_TYPE_TO_CLASS",
]
