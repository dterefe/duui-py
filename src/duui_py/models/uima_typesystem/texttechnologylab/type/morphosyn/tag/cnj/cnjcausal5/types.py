"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcausal5."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCAUSAL5DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal5.CNJCAUSAL5DE"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal5.CNJCAUSAL5DE": CNJCAUSAL5DE,
}

__all__ = [
    "CNJCAUSAL5DE",
    "UIMA_TYPE_TO_CLASS",
]
