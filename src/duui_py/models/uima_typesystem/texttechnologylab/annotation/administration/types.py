"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.administration."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class AnnotationStatus(Annotation):
    type: str = "org.texttechnologylab.annotation.administration.AnnotationStatus"
    status: Optional[str] = None
    tool: Optional[str] = None

class FinishAnnotation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.administration.FinishAnnotation"
    collectionId: Optional[str] = None
    comment: Optional[str] = None
    documentBaseUri: Optional[str] = None
    documentId: Optional[str] = None
    documentTitle: Optional[str] = None
    documentUri: Optional[str] = None
    isLastSegment: Optional[bool] = None
    tool: Optional[str] = None
    user: Optional[str] = None

class Recommendation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.administration.Recommendation"
    reference: Optional[UimaValue] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.administration.AnnotationStatus": AnnotationStatus,
    "org.texttechnologylab.annotation.administration.FinishAnnotation": FinishAnnotation,
    "org.texttechnologylab.annotation.administration.Recommendation": Recommendation,
}

__all__ = [
    "AnnotationStatus",
    "FinishAnnotation",
    "Recommendation",
    "UIMA_TYPE_TO_CLASS",
]
