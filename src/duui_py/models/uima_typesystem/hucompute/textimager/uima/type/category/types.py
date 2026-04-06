"""Auto-generated UIMA models for namespace: hucompute.textimager.uima.type.category."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CategoryCoveredTagged(Annotation):
    type: str = "org.hucompute.textimager.uima.type.category.CategoryCoveredTagged"
    ref: Optional[UimaValue] = None
    score: Optional[float] = None
    tags: Optional[str] = None
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.hucompute.textimager.uima.type.category.CategoryCoveredTagged": CategoryCoveredTagged,
}

__all__ = [
    "CategoryCoveredTagged",
    "UIMA_TYPE_TO_CLASS",
]
