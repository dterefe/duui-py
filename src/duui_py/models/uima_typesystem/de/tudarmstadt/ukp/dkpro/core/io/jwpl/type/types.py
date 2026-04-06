"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.io.jwpl.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class WikipediaLink(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.io.jwpl.type.WikipediaLink"
    Anchor: Optional[str] = None
    LinkType: Optional[str] = None
    Target: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.io.jwpl.type.WikipediaLink": WikipediaLink,
}

__all__ = [
    "WikipediaLink",
    "UIMA_TYPE_TO_CLASS",
]
