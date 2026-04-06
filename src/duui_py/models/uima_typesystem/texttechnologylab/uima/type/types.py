"""Auto-generated UIMA models for namespace: texttechnologylab.uima.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class CategorizedSentiment_uima_type_CategorizedSentiment(FeatureStructure):
    type: str = "org.texttechnologylab.uima.type.CategorizedSentiment"
    ModelReference: Optional[UimaValue] = None
    neg: Optional[float] = None
    neu: Optional[float] = None
    pos: Optional[float] = None
    sentiment: Optional[float] = None
    subjectivity: Optional[float] = None

class Classification(FeatureStructure):
    type: str = "org.texttechnologylab.uima.type.Classification"
    ModelReference: Optional[UimaValue] = None

class Embedding(FeatureStructure):
    type: str = "org.texttechnologylab.uima.type.Embedding"
    ModelReference: Optional[UimaValue] = None
    embedding: Optional[list[float]] = None

class Sentiment_uima_type_Sentiment(FeatureStructure):
    type: str = "org.texttechnologylab.uima.type.Sentiment"
    ModelReference: Optional[UimaValue] = None
    sentiment: Optional[float] = None
    subjectivity: Optional[float] = None

class StarSentiment(FeatureStructure):
    type: str = "org.texttechnologylab.uima.type.StarSentiment"
    FiveStars: Optional[float] = None
    FourStars: Optional[float] = None
    ModelReference: Optional[UimaValue] = None
    OneStar: Optional[float] = None
    ThreeStars: Optional[float] = None
    TwoStars: Optional[float] = None
    sentiment: Optional[float] = None
    subjectivity: Optional[float] = None

class Topic_uima_type_Topic(FeatureStructure):
    type: str = "org.texttechnologylab.uima.type.Topic"
    ModelReference: Optional[UimaValue] = None
    score: Optional[float] = None
    topic: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.uima.type.CategorizedSentiment": CategorizedSentiment_uima_type_CategorizedSentiment,
    "org.texttechnologylab.uima.type.Classification": Classification,
    "org.texttechnologylab.uima.type.Embedding": Embedding,
    "org.texttechnologylab.uima.type.Sentiment": Sentiment_uima_type_Sentiment,
    "org.texttechnologylab.uima.type.StarSentiment": StarSentiment,
    "org.texttechnologylab.uima.type.Topic": Topic_uima_type_Topic,
}

__all__ = [
    "CategorizedSentiment_uima_type_CategorizedSentiment",
    "Classification",
    "Embedding",
    "Sentiment_uima_type_Sentiment",
    "StarSentiment",
    "Topic_uima_type_Topic",
    "UIMA_TYPE_TO_CLASS",
]
