"""Auto-generated UIMA models for namespace: texttechnologylab.type.morphosyn.tag.conv.convconccond."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CONVCONCCONDKO(FeatureStructure):
    type: str = "org.texttechnologylab.type.morphosyn.tag.conv.convconccond.CONVCONCCONDKO"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.morphosyn.tag.conv.convconccond.CONVCONCCONDKO": CONVCONCCONDKO,
}

__all__ = [
    "CONVCONCCONDKO",
    "UIMA_TYPE_TO_CLASS",
]
