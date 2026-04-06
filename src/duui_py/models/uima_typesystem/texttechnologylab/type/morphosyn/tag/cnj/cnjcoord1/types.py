"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcoord1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCOORD1DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoord1.CNJCOORD1DE"
    value: Optional[str] = None

class CNJCOORD1EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoord1.CNJCOORD1EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoord1.CNJCOORD1DE": CNJCOORD1DE,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoord1.CNJCOORD1EN": CNJCOORD1EN,
}

__all__ = [
    "CNJCOORD1DE",
    "CNJCOORD1EN",
    "UIMA_TYPE_TO_CLASS",
]
