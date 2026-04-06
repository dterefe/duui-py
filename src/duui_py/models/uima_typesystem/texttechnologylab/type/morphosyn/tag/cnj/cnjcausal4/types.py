"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcausal4."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCAUSAL4DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal4.CNJCAUSAL4DE"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal4.CNJCAUSAL4DE": CNJCAUSAL4DE,
}

__all__ = [
    "CNJCAUSAL4DE",
    "UIMA_TYPE_TO_CLASS",
]
