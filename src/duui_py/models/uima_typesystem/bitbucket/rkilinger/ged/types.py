"""Auto-generated UIMA models for namespace: bitbucket.rkilinger.ged."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Emotion(Annotation):
    type: str = "org.bitbucket.rkilinger.ged.Emotion"
    anger: Optional[float] = None
    contempt: Optional[float] = None
    disgust: Optional[float] = None
    fear: Optional[float] = None
    joy: Optional[float] = None
    mourning: Optional[float] = None
    surprise: Optional[float] = None

UIMA_TYPE_TO_CLASS = {
    "org.bitbucket.rkilinger.ged.Emotion": Emotion,
}

__all__ = [
    "Emotion",
    "UIMA_TYPE_TO_CLASS",
]
