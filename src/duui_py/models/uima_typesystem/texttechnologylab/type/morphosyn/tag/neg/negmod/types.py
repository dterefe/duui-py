"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.neg.negmod."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class NEGMODKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.neg.negmod.NEGMODKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.neg.negmod.NEGMODKO": NEGMODKO,
}

__all__ = [
    "NEGMODKO",
    "UIMA_TYPE_TO_CLASS",
]
