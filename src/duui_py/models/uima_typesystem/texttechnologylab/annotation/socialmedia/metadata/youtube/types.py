"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.socialmedia.metadata.youtube."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Playlist(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.socialmedia.metadata.youtube.Playlist"
    createDate: Optional[int] = None
    description: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.socialmedia.metadata.youtube.Playlist": Playlist,
}

__all__ = [
    "Playlist",
    "UIMA_TYPE_TO_CLASS",
]
