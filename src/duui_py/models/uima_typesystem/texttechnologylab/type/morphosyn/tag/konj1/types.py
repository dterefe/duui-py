"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.konj1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class KONJ1DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.konj1.KONJ1DE"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.konj1.KONJ1DE": KONJ1DE,
}

__all__ = [
    "KONJ1DE",
    "UIMA_TYPE_TO_CLASS",
]
