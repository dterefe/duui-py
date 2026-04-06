"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convcausal."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVCAUSALKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convcausal.CONVCAUSALKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convcausal.CONVCAUSALKO": CONVCAUSALKO,
}

__all__ = [
    "CONVCAUSALKO",
    "UIMA_TYPE_TO_CLASS",
]
