"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cond3."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class COND3DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cond3.COND3DE"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cond3.COND3DE": COND3DE,
}

__all__ = [
    "COND3DE",
    "UIMA_TYPE_TO_CLASS",
]
