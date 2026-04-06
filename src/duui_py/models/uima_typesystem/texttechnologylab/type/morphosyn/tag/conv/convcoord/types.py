"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convcoord."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVCOORDKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convcoord.CONVCOORDKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convcoord.CONVCOORDKO": CONVCOORDKO,
}

__all__ = [
    "CONVCOORDKO",
    "UIMA_TYPE_TO_CLASS",
]
