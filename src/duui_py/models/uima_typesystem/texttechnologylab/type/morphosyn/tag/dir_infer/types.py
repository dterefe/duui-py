"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.dir_infer."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class DIR_INFERJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.dir_infer.DIR_INFERJA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.dir_infer.DIR_INFERJA": DIR_INFERJA,
}

__all__ = [
    "DIR_INFERJA",
    "UIMA_TYPE_TO_CLASS",
]
