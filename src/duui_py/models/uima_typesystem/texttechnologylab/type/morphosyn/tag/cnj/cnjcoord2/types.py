"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcoord2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCOORD2DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoord2.CNJCOORD2DE"
    value: Optional[str] = None

class CNJCOORD2EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoord2.CNJCOORD2EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoord2.CNJCOORD2DE": CNJCOORD2DE,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoord2.CNJCOORD2EN": CNJCOORD2EN,
}

__all__ = [
    "CNJCOORD2DE",
    "CNJCOORD2EN",
    "UIMA_TYPE_TO_CLASS",
]
