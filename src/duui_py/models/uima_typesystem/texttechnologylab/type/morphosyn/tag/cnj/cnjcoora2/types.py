"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcoora2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCOORA2JA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoora2.CNJCOORA2JA"
    value: Optional[str] = None

class CNJCOORA2KO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoora2.CNJCOORA2KO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoora2.CNJCOORA2JA": CNJCOORA2JA,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoora2.CNJCOORA2KO": CNJCOORA2KO,
}

__all__ = [
    "CNJCOORA2JA",
    "CNJCOORA2KO",
    "UIMA_TYPE_TO_CLASS",
]
