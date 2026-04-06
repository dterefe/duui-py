"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjtemp2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJTEMP2EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjtemp2.CNJTEMP2EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjtemp2.CNJTEMP2EN": CNJTEMP2EN,
}

__all__ = [
    "CNJTEMP2EN",
    "UIMA_TYPE_TO_CLASS",
]
