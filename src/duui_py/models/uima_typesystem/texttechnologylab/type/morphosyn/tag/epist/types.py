"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.epist."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class EPISTEN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.epist.EPISTEN"
    value: Optional[str] = None

class EPISTJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.epist.EPISTJA"
    value: Optional[str] = None

class EPISTPST(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.epist.EPISTPST"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.epist.EPISTEN": EPISTEN,
    "org.texttechnologylab.type.morphosyn.tag.epist.EPISTJA": EPISTJA,
    "org.texttechnologylab.type.morphosyn.tag.epist.EPISTPST": EPISTPST,
}

__all__ = [
    "EPISTEN",
    "EPISTJA",
    "EPISTPST",
    "UIMA_TYPE_TO_CLASS",
]
