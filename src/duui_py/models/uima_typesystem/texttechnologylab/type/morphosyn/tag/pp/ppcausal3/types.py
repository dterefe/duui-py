"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp.ppcausal3."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PPCAUSAL3JA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.ppcausal3.PPCAUSAL3JA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp.ppcausal3.PPCAUSAL3JA": PPCAUSAL3JA,
}

__all__ = [
    "PPCAUSAL3JA",
    "UIMA_TYPE_TO_CLASS",
]
