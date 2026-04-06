"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convcond."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVCONDKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convcond.CONVCONDKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convcond.CONVCONDKO": CONVCONDKO,
}

__all__ = [
    "CONVCONDKO",
    "UIMA_TYPE_TO_CLASS",
]
