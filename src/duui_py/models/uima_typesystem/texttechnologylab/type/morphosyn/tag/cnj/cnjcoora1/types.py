"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcoora1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCOORA1DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoora1.CNJCOORA1DE"
    value: Optional[str] = None

class CNJCOORA1EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoora1.CNJCOORA1EN"
    value: Optional[str] = None

class CNJCOORA1JA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoora1.CNJCOORA1JA"
    value: Optional[str] = None

class CNJCOORA1KO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoora1.CNJCOORA1KO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoora1.CNJCOORA1DE": CNJCOORA1DE,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoora1.CNJCOORA1EN": CNJCOORA1EN,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoora1.CNJCOORA1JA": CNJCOORA1JA,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcoora1.CNJCOORA1KO": CNJCOORA1KO,
}

__all__ = [
    "CNJCOORA1DE",
    "CNJCOORA1EN",
    "CNJCOORA1JA",
    "CNJCOORA1KO",
    "UIMA_TYPE_TO_CLASS",
]
