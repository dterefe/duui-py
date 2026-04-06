"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp.ppcond1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PPCOND1JA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.ppcond1.PPCOND1JA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp.ppcond1.PPCOND1JA": PPCOND1JA,
}

__all__ = [
    "PPCOND1JA",
    "UIMA_TYPE_TO_CLASS",
]
