"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcond3."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCOND3EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond3.CNJCOND3EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcond3.CNJCOND3EN": CNJCOND3EN,
}

__all__ = [
    "CNJCOND3EN",
    "UIMA_TYPE_TO_CLASS",
]
