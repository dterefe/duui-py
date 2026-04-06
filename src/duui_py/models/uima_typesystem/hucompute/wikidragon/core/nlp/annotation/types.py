"""Auto-generated UIMA models for namespace: hucompute.wikidragon.core.nlp.annotation."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class HtmlTag(Annotation):
    type: str = "org.hucompute.wikidragon.core.nlp.annotation.HtmlTag"
    attr: Optional[str] = None
    depth: Optional[int] = None
    order: Optional[int] = None
    tag: Optional[str] = None

class WikiTextSpan(Annotation):
    type: str = "org.hucompute.wikidragon.core.nlp.annotation.WikiTextSpan"
    uid: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.hucompute.wikidragon.core.nlp.annotation.HtmlTag": HtmlTag,
    "org.hucompute.wikidragon.core.nlp.annotation.WikiTextSpan": WikiTextSpan,
}

__all__ = [
    "HtmlTag",
    "WikiTextSpan",
    "UIMA_TYPE_TO_CLASS",
]
