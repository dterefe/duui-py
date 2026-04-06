"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcoorc."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCOORCDE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoorc.CNJCOORCDE"
    value: Optional[str] = None

class CNJCOORCEN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoorc.CNJCOORCEN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoorc.CNJCOORCDE": CNJCOORCDE,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoorc.CNJCOORCEN": CNJCOORCEN,
}

__all__ = [
    "CNJCOORCDE",
    "CNJCOORCEN",
    "UIMA_TYPE_TO_CLASS",
]
