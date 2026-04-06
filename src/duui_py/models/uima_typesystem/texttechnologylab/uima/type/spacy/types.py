"""Auto-generated UIMA models for namespace: texttechnologylab.uima.type.spacy."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class SpacyNounChunk(Annotation):
    type: str = "org.texttechnologylab.uima.type.spacy.SpacyNounChunk"
    pass

class SpacyToken(FeatureStructure):
    type: str = "org.texttechnologylab.uima.type.spacy.SpacyToken"
    beneparLabels: Optional[list[str]] = None
    form: Optional[UimaValue] = None
    hasVector: Optional[bool] = None
    id: Optional[str] = None
    isAlpha: Optional[bool] = None
    isAscii: Optional[bool] = None
    isBracket: Optional[bool] = None
    isCurrency: Optional[bool] = None
    isDigit: Optional[bool] = None
    isLeftPunct: Optional[bool] = None
    isLower: Optional[bool] = None
    isOov: Optional[bool] = None
    isPunct: Optional[bool] = None
    isQuote: Optional[bool] = None
    isRightPunct: Optional[bool] = None
    isSentEnd: Optional[bool] = None
    isSentStart: Optional[bool] = None
    isStop: Optional[bool] = None
    isTitle: Optional[bool] = None
    isUpper: Optional[bool] = None
    lemma: Optional[UimaValue] = None
    likeNum: Optional[bool] = None
    likeUrl: Optional[bool] = None
    morph: Optional[UimaValue] = None
    order: Optional[int] = None
    parent: Optional[UimaValue] = None
    pos: Optional[UimaValue] = None
    stem: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None
    vector: Optional[list[float]] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.uima.type.spacy.SpacyNounChunk": SpacyNounChunk,
    "org.texttechnologylab.uima.type.spacy.SpacyToken": SpacyToken,
}

__all__ = [
    "SpacyNounChunk",
    "SpacyToken",
    "UIMA_TYPE_TO_CLASS",
]
