"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjconc."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCONCDE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjconc.CNJCONCDE"
    value: Optional[str] = None

class CNJCONCEN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjconc.CNJCONCEN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjconc.CNJCONCDE": CNJCONCDE,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjconc.CNJCONCEN": CNJCONCEN,
}

__all__ = [
    "CNJCONCDE",
    "CNJCONCEN",
    "UIMA_TYPE_TO_CLASS",
]
