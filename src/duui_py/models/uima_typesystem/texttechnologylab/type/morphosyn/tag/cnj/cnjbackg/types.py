"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjbackg."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJBACKGKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjbackg.CNJBACKGKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjbackg.CNJBACKGKO": CNJBACKGKO,
}

__all__ = [
    "CNJBACKGKO",
    "UIMA_TYPE_TO_CLASS",
]
