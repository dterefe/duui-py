"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjsim."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJSIMDE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjsim.CNJSIMDE"
    value: Optional[str] = None

class CNJSIMEN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjsim.CNJSIMEN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjsim.CNJSIMDE": CNJSIMDE,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjsim.CNJSIMEN": CNJSIMEN,
}

__all__ = [
    "CNJSIMDE",
    "CNJSIMEN",
    "UIMA_TYPE_TO_CLASS",
]
