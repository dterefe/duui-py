"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.pp.pppurp."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class PPPURPJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.pp.pppurp.PPPURPJA"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.pp.pppurp.PPPURPJA": PPPURPJA,
}

__all__ = [
    "PPPURPJA",
    "UIMA_TYPE_TO_CLASS",
]
