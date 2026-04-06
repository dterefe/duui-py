"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp.ppcausal2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PPCAUSAL2JA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.ppcausal2.PPCAUSAL2JA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp.ppcausal2.PPCAUSAL2JA": PPCAUSAL2JA,
}

__all__ = [
    "PPCAUSAL2JA",
    "UIMA_TYPE_TO_CLASS",
]
