"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp4."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PP4DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp4.PP4DE"
    value: Optional[str] = None

class PP4EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp4.PP4EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp4.PP4DE": PP4DE,
    "org.texttechnologylab.type.morphosyn.tag.pp4.PP4EN": PP4EN,
}

__all__ = [
    "PP4DE",
    "PP4EN",
    "UIMA_TYPE_TO_CLASS",
]
