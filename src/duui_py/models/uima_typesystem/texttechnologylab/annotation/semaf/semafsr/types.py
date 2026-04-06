"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.semaf.semafsr."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class SrLink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.semafsr.SrLink"
    comment: Optional[str] = None
    figure: Optional[UimaValue] = None
    ground: Optional[UimaValue] = None
    rel_type: Optional[str] = None
    trigger: Optional[UimaValue] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.semaf.semafsr.SrLink": SrLink,
}

__all__ = [
    "SrLink",
    "UIMA_TYPE_TO_CLASS",
]
