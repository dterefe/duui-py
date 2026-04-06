"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.hort."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class HORTJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.hort.HORTJA"
    value: Optional[str] = None

class HORTKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.hort.HORTKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.hort.HORTJA": HORTJA,
    "org.texttechnologylab.type.morphosyn.tag.hort.HORTKO": HORTKO,
}

__all__ = [
    "HORTJA",
    "HORTKO",
    "UIMA_TYPE_TO_CLASS",
]
