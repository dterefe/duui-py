"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.retr."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class RETRKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.retr.RETRKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.retr.RETRKO": RETRKO,
}

__all__ = [
    "RETRKO",
    "UIMA_TYPE_TO_CLASS",
]
