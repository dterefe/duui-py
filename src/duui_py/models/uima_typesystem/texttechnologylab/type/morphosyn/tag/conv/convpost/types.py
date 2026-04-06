"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convpost."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVPOSTKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convpost.CONVPOSTKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convpost.CONVPOSTKO": CONVPOSTKO,
}

__all__ = [
    "CONVPOSTKO",
    "UIMA_TYPE_TO_CLASS",
]
