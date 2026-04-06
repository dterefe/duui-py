"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp3."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PP3DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp3.PP3DE"
    value: Optional[str] = None

class PP3EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp3.PP3EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp3.PP3DE": PP3DE,
    "org.texttechnologylab.type.morphosyn.tag.pp3.PP3EN": PP3EN,
}

__all__ = [
    "PP3DE",
    "PP3EN",
    "UIMA_TYPE_TO_CLASS",
]
