"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjtemp3."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJTEMP3EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjtemp3.CNJTEMP3EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjtemp3.CNJTEMP3EN": CNJTEMP3EN,
}

__all__ = [
    "CNJTEMP3EN",
    "UIMA_TYPE_TO_CLASS",
]
