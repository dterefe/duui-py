"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.possib.possibirr."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class POSSIBIRRDE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.possib.possibirr.POSSIBIRRDE"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.possib.possibirr.POSSIBIRRDE": POSSIBIRRDE,
}

__all__ = [
    "POSSIBIRRDE",
    "UIMA_TYPE_TO_CLASS",
]
