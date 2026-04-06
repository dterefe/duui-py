"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.possib."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class POSSIBDE(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.possib.POSSIBDE"
    value: Optional[str] = None

class POSSIBEN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.possib.POSSIBEN"
    value: Optional[str] = None

class POSSIBIRR(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.possib.POSSIBIRR"
    value: Optional[str] = None

class POSSIBJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.possib.POSSIBJA"
    value: Optional[str] = None

class POSSIBKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.possib.POSSIBKO"
    value: Optional[str] = None

class POSSIBPST(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.possib.POSSIBPST"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.possib.POSSIBDE": POSSIBDE,
    "org.texttechnologylab.type.morphosyn.tag.possib.POSSIBEN": POSSIBEN,
    "org.texttechnologylab.type.morphosyn.tag.possib.POSSIBIRR": POSSIBIRR,
    "org.texttechnologylab.type.morphosyn.tag.possib.POSSIBJA": POSSIBJA,
    "org.texttechnologylab.type.morphosyn.tag.possib.POSSIBKO": POSSIBKO,
    "org.texttechnologylab.type.morphosyn.tag.possib.POSSIBPST": POSSIBPST,
}

__all__ = [
    "POSSIBDE",
    "POSSIBEN",
    "POSSIBIRR",
    "POSSIBJA",
    "POSSIBKO",
    "POSSIBPST",
    "UIMA_TYPE_TO_CLASS",
]
