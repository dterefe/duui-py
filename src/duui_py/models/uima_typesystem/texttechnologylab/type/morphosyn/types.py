"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class MorphosynTag(Annotation):
    type: str = "org.texttechnologylab.type.morphosyn.MorphosynTag"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.MorphosynTag": MorphosynTag,
}

__all__ = [
    "MorphosynTag",
    "UIMA_TYPE_TO_CLASS",
]
