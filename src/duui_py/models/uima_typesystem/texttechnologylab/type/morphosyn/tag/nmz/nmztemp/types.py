"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.nmz.nmztemp."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class NMZTEMPJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.nmz.nmztemp.NMZTEMPJA"
    value: Optional[str] = None

class NMZTEMPKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.nmz.nmztemp.NMZTEMPKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.nmz.nmztemp.NMZTEMPJA": NMZTEMPJA,
    "org.texttechnologylab.type.morphosyn.tag.nmz.nmztemp.NMZTEMPKO": NMZTEMPKO,
}

__all__ = [
    "NMZTEMPJA",
    "NMZTEMPKO",
    "UIMA_TYPE_TO_CLASS",
]
