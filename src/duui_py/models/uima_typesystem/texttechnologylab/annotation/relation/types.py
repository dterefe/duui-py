"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.relation."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class AnnotationRelation(Annotation):
    type: str = "org.texttechnologylab.annotation.relation.AnnotationRelation"
    directed: Optional[bool] = None
    u: Optional[UimaValue] = None
    v: Optional[UimaValue] = None

class DamerauLevenshteinDistance(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.relation.DamerauLevenshteinDistance"
    algorithm: Optional[str] = None
    directed: Optional[bool] = None
    distance: Optional[int] = None
    u: Optional[UimaValue] = None
    v: Optional[UimaValue] = None

class EditDistance(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.relation.EditDistance"
    algorithm: Optional[str] = None
    directed: Optional[bool] = None
    distance: Optional[int] = None
    u: Optional[UimaValue] = None
    v: Optional[UimaValue] = None

class HammingDistance(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.relation.HammingDistance"
    algorithm: Optional[str] = None
    directed: Optional[bool] = None
    distance: Optional[int] = None
    u: Optional[UimaValue] = None
    v: Optional[UimaValue] = None

class JaroDistance(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.relation.JaroDistance"
    algorithm: Optional[str] = None
    directed: Optional[bool] = None
    distance: Optional[int] = None
    u: Optional[UimaValue] = None
    v: Optional[UimaValue] = None

class LevenshteinDistance(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.relation.LevenshteinDistance"
    algorithm: Optional[str] = None
    directed: Optional[bool] = None
    distance: Optional[int] = None
    u: Optional[UimaValue] = None
    v: Optional[UimaValue] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.relation.AnnotationRelation": AnnotationRelation,
    "org.texttechnologylab.annotation.relation.DamerauLevenshteinDistance": DamerauLevenshteinDistance,
    "org.texttechnologylab.annotation.relation.EditDistance": EditDistance,
    "org.texttechnologylab.annotation.relation.HammingDistance": HammingDistance,
    "org.texttechnologylab.annotation.relation.JaroDistance": JaroDistance,
    "org.texttechnologylab.annotation.relation.LevenshteinDistance": LevenshteinDistance,
}

__all__ = [
    "AnnotationRelation",
    "DamerauLevenshteinDistance",
    "EditDistance",
    "HammingDistance",
    "JaroDistance",
    "LevenshteinDistance",
    "UIMA_TYPE_TO_CLASS",
]
