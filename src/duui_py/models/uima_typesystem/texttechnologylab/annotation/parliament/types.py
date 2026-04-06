"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.parliament."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Speaker(Annotation):
    type: str = "org.texttechnologylab.annotation.parliament.Speaker"
    electoral_county: Optional[str] = None
    electoral_county_deducted: Optional[str] = None
    firstname: Optional[str] = None
    fullname_deducted: Optional[str] = None
    label: Optional[str] = None
    name: Optional[str] = None
    nobility: Optional[str] = None
    party: Optional[str] = None
    party_deducted: Optional[str] = None
    role: Optional[str] = None
    title: Optional[str] = None

class Speech(Annotation):
    type: str = "org.texttechnologylab.annotation.parliament.Speech"
    date: Optional[int] = None
    speaker: Optional[UimaValue] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.parliament.Speaker": Speaker,
    "org.texttechnologylab.annotation.parliament.Speech": Speech,
}

__all__ = [
    "Speaker",
    "Speech",
    "UIMA_TYPE_TO_CLASS",
]
