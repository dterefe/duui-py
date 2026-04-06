"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjcausal."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCAUSALJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal.CNJCAUSALJA"
    value: Optional[str] = None

class CNJCAUSALKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal.CNJCAUSALKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal.CNJCAUSALJA": CNJCAUSALJA,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjcausal.CNJCAUSALKO": CNJCAUSALKO,
}

__all__ = [
    "CNJCAUSALJA",
    "CNJCAUSALKO",
    "UIMA_TYPE_TO_CLASS",
]
