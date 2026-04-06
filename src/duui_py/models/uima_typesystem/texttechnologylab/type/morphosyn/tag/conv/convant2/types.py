"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convant2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVANT2KO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convant2.CONVANT2KO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convant2.CONVANT2KO": CONVANT2KO,
}

__all__ = [
    "CONVANT2KO",
    "UIMA_TYPE_TO_CLASS",
]
