"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.imposs."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class IMPOSSKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.imposs.IMPOSSKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.imposs.IMPOSSKO": IMPOSSKO,
}

__all__ = [
    "IMPOSSKO",
    "UIMA_TYPE_TO_CLASS",
]
