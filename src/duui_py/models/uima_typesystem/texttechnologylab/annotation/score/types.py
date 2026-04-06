"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.score."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ScoreAnnotation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.score.ScoreAnnotation"
    origin: Optional[str] = None
    reference: Optional[UimaValue] = None
    value: Optional[float] = None

class TextScore(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.score.TextScore"
    documentName: Optional[str] = None
    documentURI: Optional[str] = None
    elements: Optional[list[UimaValue]] = None

class TextScoreEntry(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.score.TextScoreEntry"
    key: Optional[str] = None
    label: Optional[str] = None
    value: Optional[float] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.score.ScoreAnnotation": ScoreAnnotation,
    "org.texttechnologylab.annotation.score.TextScore": TextScore,
    "org.texttechnologylab.annotation.score.TextScoreEntry": TextScoreEntry,
}

__all__ = [
    "ScoreAnnotation",
    "TextScore",
    "TextScoreEntry",
    "UIMA_TYPE_TO_CLASS",
]
