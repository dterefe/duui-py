"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.nmz.nmzcond."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class NMZCONDJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.nmz.nmzcond.NMZCONDJA"
    value: Optional[str] = None

class NMZCONDKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.nmz.nmzcond.NMZCONDKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.nmz.nmzcond.NMZCONDJA": NMZCONDJA,
    "org.texttechnologylab.type.morphosyn.tag.nmz.nmzcond.NMZCONDKO": NMZCONDKO,
}

__all__ = [
    "NMZCONDJA",
    "NMZCONDKO",
    "UIMA_TYPE_TO_CLASS",
]
