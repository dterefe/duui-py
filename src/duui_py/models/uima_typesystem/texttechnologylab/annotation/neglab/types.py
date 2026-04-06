"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.neglab."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ConditionSentence(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.neglab.ConditionSentence"
    condition: Optional[str] = None
    id: Optional[str] = None
    order: Optional[int] = None
    sequenceScore: Optional[float] = None
    sequenceScoreSum: Optional[float] = None
    target: Optional[str] = None
    value: Optional[float] = None

class TokenSuprisal(Annotation):
    type: str = "org.texttechnologylab.annotation.neglab.TokenSuprisal"
    value: Optional[float] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.neglab.ConditionSentence": ConditionSentence,
    "org.texttechnologylab.annotation.neglab.TokenSuprisal": TokenSuprisal,
}

__all__ = [
    "ConditionSentence",
    "TokenSuprisal",
    "UIMA_TYPE_TO_CLASS",
]
