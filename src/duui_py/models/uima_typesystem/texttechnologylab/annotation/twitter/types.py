"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.twitter."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Tweet(Annotation):
    type: str = "org.texttechnologylab.annotation.twitter.Tweet"
    create: Optional[int] = None
    geo: Optional[str] = None
    hashTags: Optional[list[str]] = None
    language: Optional[str] = None
    originalText: Optional[str] = None
    quoted: Optional[int] = None
    repliedTo: Optional[int] = None
    retweet: Optional[int] = None
    twitterID: Optional[int] = None
    urls: Optional[list[str]] = None
    userId: Optional[int] = None
    userName: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.twitter.Tweet": Tweet,
}

__all__ = [
    "Tweet",
    "UIMA_TYPE_TO_CLASS",
]
