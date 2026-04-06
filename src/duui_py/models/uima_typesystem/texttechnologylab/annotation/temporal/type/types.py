"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.temporal.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class After_temporal_type_After(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.temporal.type.After"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class Before(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.temporal.type.Before"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class During(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.temporal.type.During"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.temporal.type.After": After_temporal_type_After,
    "org.texttechnologylab.annotation.temporal.type.Before": Before,
    "org.texttechnologylab.annotation.temporal.type.During": During,
}

__all__ = [
    "After_temporal_type_After",
    "Before",
    "During",
    "UIMA_TYPE_TO_CLASS",
]
