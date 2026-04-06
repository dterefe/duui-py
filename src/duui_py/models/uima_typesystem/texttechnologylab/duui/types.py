"""Auto-generated UIMA models for namespace: texttechnologylab.duui."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ReproducibleAnnotation(FeatureStructure):
    type: str = "org.texttechnologylab.duui.ReproducibleAnnotation"
    compression: Optional[str] = None
    description: Optional[str] = None
    pipelineName: Optional[str] = None
    timestamp: Optional[int] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.duui.ReproducibleAnnotation": ReproducibleAnnotation,
}

__all__ = [
    "ReproducibleAnnotation",
    "UIMA_TYPE_TO_CLASS",
]
