"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.nmz.nmzreal."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class NMZREALJA(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.nmz.nmzreal.NMZREALJA"
    value: Optional[str] = None

class NMZREALKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.nmz.nmzreal.NMZREALKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.nmz.nmzreal.NMZREALJA": NMZREALJA,
    "org.texttechnologylab.type.morphosyn.tag.nmz.nmzreal.NMZREALKO": NMZREALKO,
}

__all__ = [
    "NMZREALJA",
    "NMZREALKO",
    "UIMA_TYPE_TO_CLASS",
]
