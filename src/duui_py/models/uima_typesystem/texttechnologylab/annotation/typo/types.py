"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.typo."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Historical(Annotation):
    type: str = "org.texttechnologylab.annotation.typo.Historical"
    pass

class OCR(Annotation):
    type: str = "org.texttechnologylab.annotation.typo.OCR"
    pass

class Orthography(Annotation):
    type: str = "org.texttechnologylab.annotation.typo.Orthography"
    pass

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.typo.Historical": Historical,
    "org.texttechnologylab.annotation.typo.OCR": OCR,
    "org.texttechnologylab.annotation.typo.Orthography": Orthography,
}

__all__ = [
    "Historical",
    "OCR",
    "Orthography",
    "UIMA_TYPE_TO_CLASS",
]
