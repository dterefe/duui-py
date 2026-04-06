"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcausal1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCAUSAL1DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal1.CNJCAUSAL1DE"
    value: Optional[str] = None

class CNJCAUSAL1EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal1.CNJCAUSAL1EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal1.CNJCAUSAL1DE": CNJCAUSAL1DE,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal1.CNJCAUSAL1EN": CNJCAUSAL1EN,
}

__all__ = [
    "CNJCAUSAL1DE",
    "CNJCAUSAL1EN",
    "UIMA_TYPE_TO_CLASS",
]
