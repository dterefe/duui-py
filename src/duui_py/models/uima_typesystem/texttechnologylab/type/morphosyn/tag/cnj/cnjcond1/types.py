"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcond1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCOND1DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond1.CNJCOND1DE"
    value: Optional[str] = None

class CNJCOND1EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond1.CNJCOND1EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond1.CNJCOND1DE": CNJCOND1DE,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond1.CNJCOND1EN": CNJCOND1EN,
}

__all__ = [
    "CNJCOND1DE",
    "CNJCOND1EN",
    "UIMA_TYPE_TO_CLASS",
]
