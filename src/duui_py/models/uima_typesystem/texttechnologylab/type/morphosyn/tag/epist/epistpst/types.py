"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.epist.epistpst."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class EPISTPSTEN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.epist.epistpst.EPISTPSTEN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.epist.epistpst.EPISTPSTEN": EPISTPSTEN,
}

__all__ = [
    "EPISTPSTEN",
    "UIMA_TYPE_TO_CLASS",
]
