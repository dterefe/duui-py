"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.nmz.nmzirr."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class NMZIRRJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.nmz.nmzirr.NMZIRRJA"
    value: Optional[str] = None

class NMZIRRKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.nmz.nmzirr.NMZIRRKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.nmz.nmzirr.NMZIRRJA": NMZIRRJA,
    "org.texttechnologylab.type.morphosyn.tag.nmz.nmzirr.NMZIRRKO": NMZIRRKO,
}

__all__ = [
    "NMZIRRJA",
    "NMZIRRKO",
    "UIMA_TYPE_TO_CLASS",
]
