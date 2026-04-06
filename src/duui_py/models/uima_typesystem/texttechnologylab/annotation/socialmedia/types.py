"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.socialmedia."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class MetaData_annotation_socialmedia_MetaData(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.socialmedia.MetaData"
    createDate: Optional[int] = None
    description: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.socialmedia.MetaData": MetaData_annotation_socialmedia_MetaData,
}

__all__ = [
    "MetaData_annotation_socialmedia_MetaData",
    "UIMA_TYPE_TO_CLASS",
]
