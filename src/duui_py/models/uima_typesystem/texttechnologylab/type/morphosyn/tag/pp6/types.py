"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp6."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PP6EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp6.PP6EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp6.PP6EN": PP6EN,
}

__all__ = [
    "PP6EN",
    "UIMA_TYPE_TO_CLASS",
]
