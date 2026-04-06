"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.possib.possibpst."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class POSSIBPSTEN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.possib.possibpst.POSSIBPSTEN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.possib.possibpst.POSSIBPSTEN": POSSIBPSTEN,
}

__all__ = [
    "POSSIBPSTEN",
    "UIMA_TYPE_TO_CLASS",
]
