"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.irr2."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class IRR2EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.irr2.IRR2EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.irr2.IRR2EN": IRR2EN,
}

__all__ = [
    "IRR2EN",
    "UIMA_TYPE_TO_CLASS",
]
