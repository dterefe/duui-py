"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.negation."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CompleteNegation(Annotation):
    type: str = "org.texttechnologylab.annotation.negation.CompleteNegation"
    cue: Optional[UimaValue] = None
    event: Optional[list[UimaValue]] = None
    focus: Optional[list[UimaValue]] = None
    negType: Optional[str] = None
    scope: Optional[list[UimaValue]] = None
    xscope: Optional[list[UimaValue]] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.negation.CompleteNegation": CompleteNegation,
}

__all__ = [
    "CompleteNegation",
    "UIMA_TYPE_TO_CLASS",
]
