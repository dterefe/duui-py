"""Auto-generated UIMA models for namespace: hucompute.textimager.uima.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CategorizedSentiment(FeatureStructure):
    type: str = "org.hucompute.textimager.uima.type.CategorizedSentiment"
    neg: Optional[float] = None
    neu: Optional[float] = None
    pos: Optional[float] = None
    sentiment: Optional[float] = None
    subjectivity: Optional[float] = None

class GerVaderSentiment(FeatureStructure):
    type: str = "org.hucompute.textimager.uima.type.GerVaderSentiment"
    neg: Optional[float] = None
    neu: Optional[float] = None
    pos: Optional[float] = None
    sentiment: Optional[float] = None
    subjectivity: Optional[float] = None

class ImageVector(Annotation):
    type: str = "org.hucompute.textimager.uima.type.ImageVector"
    embedding: Optional[list[float]] = None
    value: Optional[str] = None

class Language_uima_type_Language(Annotation):
    type: str = "org.hucompute.textimager.uima.type.Language"
    language: Optional[str] = None

class OpenIERelation(Annotation):
    type: str = "org.hucompute.textimager.uima.type.OpenIERelation"
    beginArg1: Optional[int] = None
    beginArg2: Optional[int] = None
    beginRel: Optional[int] = None
    confidence: Optional[float] = None
    endArg1: Optional[int] = None
    endArg2: Optional[int] = None
    endRel: Optional[int] = None
    valueArg1: Optional[str] = None
    valueArg2: Optional[str] = None
    valueRel: Optional[str] = None

class Sentiment(Annotation):
    type: str = "org.hucompute.textimager.uima.type.Sentiment"
    sentiment: Optional[float] = None
    subjectivity: Optional[float] = None

class Similarity(Annotation):
    type: str = "org.hucompute.textimager.uima.type.Similarity"
    value: Optional[str] = None

class Summary(Annotation):
    type: str = "org.hucompute.textimager.uima.type.Summary"
    summary: Optional[str] = None

class VaderSentiment(FeatureStructure):
    type: str = "org.hucompute.textimager.uima.type.VaderSentiment"
    neg: Optional[float] = None
    neu: Optional[float] = None
    pos: Optional[float] = None
    sentiment: Optional[float] = None
    subjectivity: Optional[float] = None

class Wikify(Annotation):
    type: str = "org.hucompute.textimager.uima.type.Wikify"
    elements: Optional[list[UimaValue]] = None
    link: Optional[str] = None
    title: Optional[str] = None

class WikipediaInformation(Annotation):
    type: str = "org.hucompute.textimager.uima.type.WikipediaInformation"
    categories: Optional[list[str]] = None
    namespace: Optional[str] = None
    namespaceID: Optional[str] = None
    pageID: Optional[str] = None
    pageURL: Optional[str] = None
    revisionID: Optional[str] = None
    timestamp: Optional[str] = None
    title: Optional[str] = None

class Word2Vec(Annotation):
    type: str = "org.hucompute.textimager.uima.type.Word2Vec"
    embedding: Optional[list[float]] = None
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.hucompute.textimager.uima.type.CategorizedSentiment": CategorizedSentiment,
    "org.hucompute.textimager.uima.type.GerVaderSentiment": GerVaderSentiment,
    "org.hucompute.textimager.uima.type.ImageVector": ImageVector,
    "org.hucompute.textimager.uima.type.Language": Language_uima_type_Language,
    "org.hucompute.textimager.uima.type.OpenIERelation": OpenIERelation,
    "org.hucompute.textimager.uima.type.Sentiment": Sentiment,
    "org.hucompute.textimager.uima.type.Similarity": Similarity,
    "org.hucompute.textimager.uima.type.Summary": Summary,
    "org.hucompute.textimager.uima.type.VaderSentiment": VaderSentiment,
    "org.hucompute.textimager.uima.type.Wikify": Wikify,
    "org.hucompute.textimager.uima.type.WikipediaInformation": WikipediaInformation,
    "org.hucompute.textimager.uima.type.Word2Vec": Word2Vec,
}

__all__ = [
    "CategorizedSentiment",
    "GerVaderSentiment",
    "ImageVector",
    "Language_uima_type_Language",
    "OpenIERelation",
    "Sentiment",
    "Similarity",
    "Summary",
    "VaderSentiment",
    "Wikify",
    "WikipediaInformation",
    "Word2Vec",
    "UIMA_TYPE_TO_CLASS",
]
