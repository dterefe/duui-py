"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcond4."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCOND4DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond4.CNJCOND4DE"
    value: Optional[str] = None

class CNJCOND4EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond4.CNJCOND4EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond4.CNJCOND4DE": CNJCOND4DE,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond4.CNJCOND4EN": CNJCOND4EN,
}

__all__ = [
    "CNJCOND4DE",
    "CNJCOND4EN",
    "UIMA_TYPE_TO_CLASS",
]
