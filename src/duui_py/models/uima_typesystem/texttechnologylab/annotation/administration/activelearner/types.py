"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.administration.activelearner."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Accept(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.administration.activelearner.Accept"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    comment: Optional[str] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    reference: Optional[UimaValue] = None
    user: Optional[str] = None

class Decision(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.administration.activelearner.Decision"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    comment: Optional[str] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    reference: Optional[UimaValue] = None
    user: Optional[str] = None

class Recommendation_administration_activelearner_Recommendation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.administration.activelearner.Recommendation"
    hash: Optional[str] = None
    key: Optional[str] = None
    reference: Optional[UimaValue] = None
    score: Optional[float] = None
    value: Optional[str] = None

class Reject(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.administration.activelearner.Reject"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    comment: Optional[str] = None
    create: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    reference: Optional[UimaValue] = None
    user: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.administration.activelearner.Accept": Accept,
    "org.texttechnologylab.annotation.administration.activelearner.Decision": Decision,
    "org.texttechnologylab.annotation.administration.activelearner.Recommendation": Recommendation_administration_activelearner_Recommendation,
    "org.texttechnologylab.annotation.administration.activelearner.Reject": Reject,
}

__all__ = [
    "Accept",
    "Decision",
    "Recommendation_administration_activelearner_Recommendation",
    "Reject",
    "UIMA_TYPE_TO_CLASS",
]
