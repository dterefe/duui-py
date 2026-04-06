"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.prob."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PROBKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.prob.PROBKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.prob.PROBKO": PROBKO,
}

__all__ = [
    "PROBKO",
    "UIMA_TYPE_TO_CLASS",
]
