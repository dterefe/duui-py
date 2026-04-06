"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convant1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVANT1KO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convant1.CONVANT1KO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convant1.CONVANT1KO": CONVANT1KO,
}

__all__ = [
    "CONVANT1KO",
    "UIMA_TYPE_TO_CLASS",
]
