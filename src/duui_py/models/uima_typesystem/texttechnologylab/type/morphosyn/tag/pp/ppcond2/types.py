"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp.ppcond2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PPCOND2JA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.ppcond2.PPCOND2JA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp.ppcond2.PPCOND2JA": PPCOND2JA,
}

__all__ = [
    "PPCOND2JA",
    "UIMA_TYPE_TO_CLASS",
]
