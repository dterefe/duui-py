"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.token."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Correction(Annotation):
    type: str = "org.texttechnologylab.annotation.token.Correction"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.token.Correction": Correction,
}

__all__ = [
    "Correction",
    "UIMA_TYPE_TO_CLASS",
]
