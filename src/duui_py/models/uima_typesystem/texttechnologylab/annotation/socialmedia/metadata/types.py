"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.socialmedia.metadata."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class YouTube(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.socialmedia.metadata.YouTube"
    channelName: Optional[str] = None
    channelURL: Optional[str] = None
    createDate: Optional[int] = None
    description: Optional[str] = None
    dislikes: Optional[int] = None
    downloadDate: Optional[int] = None
    length: Optional[int] = None
    likes: Optional[int] = None
    name: Optional[str] = None
    playlist: Optional[list[UimaValue]] = None
    url: Optional[str] = None
    views: Optional[int] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.socialmedia.metadata.YouTube": YouTube,
}

__all__ = [
    "YouTube",
    "UIMA_TYPE_TO_CLASS",
]
