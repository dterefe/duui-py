"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp5."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PP5DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp5.PP5DE"
    value: Optional[str] = None

class PP5EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp5.PP5EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp5.PP5DE": PP5DE,
    "org.texttechnologylab.type.morphosyn.tag.pp5.PP5EN": PP5EN,
}

__all__ = [
    "PP5DE",
    "PP5EN",
    "UIMA_TYPE_TO_CLASS",
]
