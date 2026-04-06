"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convconc."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVCONCJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convconc.CONVCONCJA"
    value: Optional[str] = None

class CONVCONCKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convconc.CONVCONCKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convconc.CONVCONCJA": CONVCONCJA,
    "org.texttechnologylab.type.morphosyn.tag.conv.convconc.CONVCONCKO": CONVCONCKO,
}

__all__ = [
    "CONVCONCJA",
    "CONVCONCKO",
    "UIMA_TYPE_TO_CLASS",
]
