"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.biofid."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue


class Collection(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.Collection"
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    uri: Optional[str] = None


class Journal(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.Journal"
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    uri: Optional[str] = None


class Volume(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.Volume"
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    number: Optional[str] = None
    uri: Optional[str] = None
    year: Optional[str] = None


class Issue(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.Issue"
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    number: Optional[str] = None
    uri: Optional[str] = None
    year: Optional[str] = None


class Article(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.Article"
    abstractText: Optional[str] = None
    doi: Optional[str] = None
    id: Optional[str] = None
    kind: Optional[str] = None
    language: Optional[str] = None
    license: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    pages: Optional[str] = None
    pdf: Optional[str] = None
    uri: Optional[str] = None
    vendor: Optional[str] = None
    year: Optional[str] = None


class Page(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.biofid.Page"
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    number: Optional[int] = None
    uri: Optional[str] = None


class Taxon(Annotation):
    type: str = "org.texttechnologylab.annotation.biofid.Taxon"
    identifier: Optional[str] = None
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.biofid.Collection": Collection,
    "org.texttechnologylab.annotation.biofid.Journal": Journal,
    "org.texttechnologylab.annotation.biofid.Volume": Volume,
    "org.texttechnologylab.annotation.biofid.Issue": Issue,
    "org.texttechnologylab.annotation.biofid.Article": Article,
    "org.texttechnologylab.annotation.biofid.Page": Page,
    "org.texttechnologylab.annotation.biofid.Taxon": Taxon,
}

__all__ = [
    "Collection",
    "Journal",
    "Volume",
    "Issue",
    "Article",
    "Page",
    "Taxon",
    "UIMA_TYPE_TO_CLASS",
]
