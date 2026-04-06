"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.nmz."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class NMZCOND(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.nmz.NMZCOND"
    value: Optional[str] = None

class NMZIRR(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.nmz.NMZIRR"
    value: Optional[str] = None

class NMZREAL(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.nmz.NMZREAL"
    value: Optional[str] = None

class NMZTEMP(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.nmz.NMZTEMP"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.nmz.NMZCOND": NMZCOND,
    "org.texttechnologylab.type.morphosyn.tag.nmz.NMZIRR": NMZIRR,
    "org.texttechnologylab.type.morphosyn.tag.nmz.NMZREAL": NMZREAL,
    "org.texttechnologylab.type.morphosyn.tag.nmz.NMZTEMP": NMZTEMP,
}

__all__ = [
    "NMZCOND",
    "NMZIRR",
    "NMZREAL",
    "NMZTEMP",
    "UIMA_TYPE_TO_CLASS",
]
