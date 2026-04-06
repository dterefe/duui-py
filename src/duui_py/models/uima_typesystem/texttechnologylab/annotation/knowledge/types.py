"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.knowledge."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class KnowledgeEntry(Annotation):
    type: str = "org.texttechnologylab.annotation.knowledge.KnowledgeEntry"
    source: Optional[str] = None
    uri: Optional[str] = None

class WikidataEntry(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.knowledge.WikidataEntry"
    P279: Optional[list[str]] = None
    P31: Optional[list[str]] = None
    source: Optional[str] = None
    uri: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.knowledge.KnowledgeEntry": KnowledgeEntry,
    "org.texttechnologylab.annotation.knowledge.WikidataEntry": WikidataEntry,
}

__all__ = [
    "KnowledgeEntry",
    "WikidataEntry",
    "UIMA_TYPE_TO_CLASS",
]
