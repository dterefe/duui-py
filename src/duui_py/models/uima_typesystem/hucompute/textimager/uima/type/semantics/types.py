"""Auto-generated UIMA models for namespace: hucompute.textimager.uima.type.semantics."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class WordSense_type_semantics_WordSense(FeatureStructure):
    type: str = "org.hucompute.textimager.uima.type.semantics.WordSense"
    confidence: Optional[float] = None
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.hucompute.textimager.uima.type.semantics.WordSense": WordSense_type_semantics_WordSense,
}

__all__ = [
    "WordSense_type_semantics_WordSense",
    "UIMA_TYPE_TO_CLASS",
]
