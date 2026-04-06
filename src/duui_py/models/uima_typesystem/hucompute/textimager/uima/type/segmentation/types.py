"""Auto-generated UIMA models for namespace: hucompute.textimager.uima.type.segmentation."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Div_type_segmentation_Div(Annotation):
    type: str = "org.hucompute.textimager.uima.type.segmentation.Div"
    id: Optional[str] = None
    section: Optional[str] = None
    timestamp: Optional[str] = None
    typ: Optional[str] = None
    user: Optional[str] = None

class Head(Annotation):
    type: str = "org.hucompute.textimager.uima.type.segmentation.Head"
    children: Optional[str] = None
    id: Optional[str] = None
    parent: Optional[str] = None
    rootEntries: Optional[str] = None
    typ: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.hucompute.textimager.uima.type.segmentation.Div": Div_type_segmentation_Div,
    "org.hucompute.textimager.uima.type.segmentation.Head": Head,
}

__all__ = [
    "Div_type_segmentation_Div",
    "Head",
    "UIMA_TYPE_TO_CLASS",
]
