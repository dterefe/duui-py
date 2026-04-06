"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PP2DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp2.PP2DE"
    value: Optional[str] = None

class PP2EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp2.PP2EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp2.PP2DE": PP2DE,
    "org.texttechnologylab.type.morphosyn.tag.pp2.PP2EN": PP2EN,
}

__all__ = [
    "PP2DE",
    "PP2EN",
    "UIMA_TYPE_TO_CLASS",
]
