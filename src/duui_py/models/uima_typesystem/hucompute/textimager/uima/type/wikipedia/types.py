"""Auto-generated UIMA models for namespace: hucompute.textimager.uima.type.wikipedia."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class WikipediaLink_type_wikipedia_WikipediaLink(FeatureStructure):
    type: str = "org.hucompute.textimager.uima.type.wikipedia.WikipediaLink"
    Anchor: Optional[str] = None
    LinkType: Optional[str] = None
    Target: Optional[str] = None
    WikiData: Optional[str] = None
    WikiDataHyponyms: Optional[list[str]] = None
    isInstance: Optional[bool] = None

UIMA_TYPE_TO_CLASS = {
    "org.hucompute.textimager.uima.type.wikipedia.WikipediaLink": WikipediaLink_type_wikipedia_WikipediaLink,
}

__all__ = [
    "WikipediaLink_type_wikipedia_WikipediaLink",
    "UIMA_TYPE_TO_CLASS",
]
