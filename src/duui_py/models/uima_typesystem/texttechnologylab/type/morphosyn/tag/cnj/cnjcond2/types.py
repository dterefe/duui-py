"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcond2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCOND2DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond2.CNJCOND2DE"
    value: Optional[str] = None

class CNJCOND2EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond2.CNJCOND2EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond2.CNJCOND2DE": CNJCOND2DE,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond2.CNJCOND2EN": CNJCOND2EN,
}

__all__ = [
    "CNJCOND2DE",
    "CNJCOND2EN",
    "UIMA_TYPE_TO_CLASS",
]
