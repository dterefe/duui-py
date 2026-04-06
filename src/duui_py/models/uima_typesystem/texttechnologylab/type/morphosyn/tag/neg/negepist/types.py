"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.neg.negepist."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class NEGEPISTJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.neg.negepist.NEGEPISTJA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.neg.negepist.NEGEPISTJA": NEGEPISTJA,
}

__all__ = [
    "NEGEPISTJA",
    "UIMA_TYPE_TO_CLASS",
]
