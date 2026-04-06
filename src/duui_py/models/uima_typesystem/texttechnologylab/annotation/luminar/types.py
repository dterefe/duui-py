"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.luminar."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class AIDetection(Annotation):
    type: str = "org.texttechnologylab.annotation.luminar.AIDetection"
    detectionScore: Optional[float] = None
    level: Optional[str] = None
    model: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.luminar.AIDetection": AIDetection,
}

__all__ = [
    "AIDetection",
    "UIMA_TYPE_TO_CLASS",
]
