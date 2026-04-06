"""Auto-generated UIMA models for namespace: hucompute.textimager.uima.type.wikidata."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class WikiDataHyponym(Annotation):
    type: str = "org.hucompute.textimager.uima.type.wikidata.WikiDataHyponym"
    depth: Optional[int] = None
    id: Optional[str] = None
    typ: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.hucompute.textimager.uima.type.wikidata.WikiDataHyponym": WikiDataHyponym,
}

__all__ = [
    "WikiDataHyponym",
    "UIMA_TYPE_TO_CLASS",
]
