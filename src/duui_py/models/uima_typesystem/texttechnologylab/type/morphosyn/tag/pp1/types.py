"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PP1DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp1.PP1DE"
    value: Optional[str] = None

class PP1EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp1.PP1EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp1.PP1DE": PP1DE,
    "org.texttechnologylab.type.morphosyn.tag.pp1.PP1EN": PP1EN,
}

__all__ = [
    "PP1DE",
    "PP1EN",
    "UIMA_TYPE_TO_CLASS",
]
