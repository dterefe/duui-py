"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.sentence."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Anomaly_annotation_sentence_Anomaly(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.sentence.Anomaly"
    category: Optional[str] = None
    description: Optional[str] = None
    suggestions: Optional[list[UimaValue]] = None
    value: Optional[str] = None

class Discourse(Annotation):
    type: str = "org.texttechnologylab.annotation.sentence.Discourse"
    value: Optional[str] = None

class Endmarker(Annotation):
    type: str = "org.texttechnologylab.annotation.sentence.Endmarker"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.sentence.Anomaly": Anomaly_annotation_sentence_Anomaly,
    "org.texttechnologylab.annotation.sentence.Discourse": Discourse,
    "org.texttechnologylab.annotation.sentence.Endmarker": Endmarker,
}

__all__ = [
    "Anomaly_annotation_sentence_Anomaly",
    "Discourse",
    "Endmarker",
    "UIMA_TYPE_TO_CLASS",
]
