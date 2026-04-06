"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pst."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PSTKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pst.PSTKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pst.PSTKO": PSTKO,
}

__all__ = [
    "PSTKO",
    "UIMA_TYPE_TO_CLASS",
]
