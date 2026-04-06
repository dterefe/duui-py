"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.decl."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class DECLKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.decl.DECLKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.decl.DECLKO": DECLKO,
}

__all__ = [
    "DECLKO",
    "UIMA_TYPE_TO_CLASS",
]
