"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjpurp1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJPURP1DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjpurp1.CNJPURP1DE"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjpurp1.CNJPURP1DE": CNJPURP1DE,
}

__all__ = [
    "CNJPURP1DE",
    "UIMA_TYPE_TO_CLASS",
]
