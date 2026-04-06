"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.irr1."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class IRR1EN(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.irr1.IRR1EN"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.irr1.IRR1EN": IRR1EN,
}

__all__ = [
    "IRR1EN",
    "UIMA_TYPE_TO_CLASS",
]
