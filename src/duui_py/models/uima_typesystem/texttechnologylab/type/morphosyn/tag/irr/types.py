"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.irr."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class IRRDE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.irr.IRRDE"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.irr.IRRDE": IRRDE,
}

__all__ = [
    "IRRDE",
    "UIMA_TYPE_TO_CLASS",
]
