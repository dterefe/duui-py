"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcausal3."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCAUSAL3DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal3.CNJCAUSAL3DE"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal3.CNJCAUSAL3DE": CNJCAUSAL3DE,
}

__all__ = [
    "CNJCAUSAL3DE",
    "UIMA_TYPE_TO_CLASS",
]
