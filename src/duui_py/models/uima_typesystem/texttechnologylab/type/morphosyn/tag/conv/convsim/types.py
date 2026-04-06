"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convsim."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVSIMJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convsim.CONVSIMJA"
    value: Optional[str] = None

class CONVSIMKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convsim.CONVSIMKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convsim.CONVSIMJA": CONVSIMJA,
    "org.texttechnologylab.type.morphosyn.tag.conv.convsim.CONVSIMKO": CONVSIMKO,
}

__all__ = [
    "CONVSIMJA",
    "CONVSIMKO",
    "UIMA_TYPE_TO_CLASS",
]
