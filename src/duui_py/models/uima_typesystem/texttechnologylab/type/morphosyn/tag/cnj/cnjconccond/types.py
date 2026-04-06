"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.cnj.cnjconccond."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CNJCONCCONDEN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.cnj.cnjconccond.CNJCONCCONDEN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.cnj.cnjconccond.CNJCONCCONDEN": CNJCONCCONDEN,
}

__all__ = [
    "CNJCONCCONDEN",
    "UIMA_TYPE_TO_CLASS",
]
