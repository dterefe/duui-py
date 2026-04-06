"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjsim2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJSIM2DE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjsim2.CNJSIM2DE"
    value: Optional[str] = None

class CNJSIM2EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjsim2.CNJSIM2EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjsim2.CNJSIM2DE": CNJSIM2DE,
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjsim2.CNJSIM2EN": CNJSIM2EN,
}

__all__ = [
    "CNJSIM2DE",
    "CNJSIM2EN",
    "UIMA_TYPE_TO_CLASS",
]
