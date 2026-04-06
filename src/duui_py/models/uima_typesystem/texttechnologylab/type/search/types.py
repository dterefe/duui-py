"""Auto-generated UIMA models for namespace: texttechnologylab.type.search."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class TextSearch(Annotation):
    type: str = "org.texttechnologylab.type.search.TextSearch"
    text: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.search.TextSearch": TextSearch,
}

__all__ = [
    "TextSearch",
    "UIMA_TYPE_TO_CLASS",
]
