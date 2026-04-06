"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.attribution.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Bigger(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.attribution.type.Bigger"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class Louder(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.attribution.type.Louder"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class Quieter(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.attribution.type.Quieter"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class Smaler(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.attribution.type.Smaler"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    begin: Optional[int] = None
    create: Optional[int] = None
    end: Optional[int] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.attribution.type.Bigger": Bigger,
    "org.texttechnologylab.annotation.attribution.type.Louder": Louder,
    "org.texttechnologylab.annotation.attribution.type.Quieter": Quieter,
    "org.texttechnologylab.annotation.attribution.type.Smaler": Smaler,
}

__all__ = [
    "Bigger",
    "Louder",
    "Quieter",
    "Smaler",
    "UIMA_TYPE_TO_CLASS",
]
