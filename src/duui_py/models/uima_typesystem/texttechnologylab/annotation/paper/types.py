"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.paper."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Abstract(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.paper.Abstract"
    pass

class Author(Annotation):
    type: str = "org.texttechnologylab.annotation.paper.Author"
    email: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    location: Optional[str] = None
    value: Optional[str] = None

class Caption_annotation_paper_Caption(Annotation):
    type: str = "org.texttechnologylab.annotation.paper.Caption"
    pass

class Figure(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.paper.Figure"
    caption: Optional[UimaValue] = None

class FloatingElements(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.paper.FloatingElements"
    caption: Optional[UimaValue] = None

class Footline(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.paper.Footline"
    pass

class Footnote(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.paper.Footnote"
    reference: Optional[UimaValue] = None

class Graphic(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.paper.Graphic"
    caption: Optional[UimaValue] = None

class Headline(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.paper.Headline"
    pass

class Keyword(Annotation):
    type: str = "org.texttechnologylab.annotation.paper.Keyword"
    value: Optional[str] = None

class NonTextContent(Annotation):
    type: str = "org.texttechnologylab.annotation.paper.NonTextContent"
    pass

class Reference(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.paper.Reference"
    reference: Optional[UimaValue] = None

class Section(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.paper.Section"
    index: Optional[str] = None
    label: Optional[str] = None
    level: Optional[int] = None

class Source(Annotation):
    type: str = "org.texttechnologylab.annotation.paper.Source"
    authors: Optional[list[str]] = None
    doi: Optional[str] = None
    title: Optional[str] = None

class SubTitle(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.paper.SubTitle"
    pass

class Table(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.paper.Table"
    caption: Optional[UimaValue] = None

class TextContent(Annotation):
    type: str = "org.texttechnologylab.annotation.paper.TextContent"
    pass

class Title(Annotation):
    type: str = "org.texttechnologylab.annotation.paper.Title"
    pass

class URL_annotation_paper_URL(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.paper.URL"
    reference: Optional[UimaValue] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.paper.Abstract": Abstract,
    "org.texttechnologylab.annotation.paper.Author": Author,
    "org.texttechnologylab.annotation.paper.Caption": Caption_annotation_paper_Caption,
    "org.texttechnologylab.annotation.paper.Figure": Figure,
    "org.texttechnologylab.annotation.paper.FloatingElements": FloatingElements,
    "org.texttechnologylab.annotation.paper.Footline": Footline,
    "org.texttechnologylab.annotation.paper.Footnote": Footnote,
    "org.texttechnologylab.annotation.paper.Graphic": Graphic,
    "org.texttechnologylab.annotation.paper.Headline": Headline,
    "org.texttechnologylab.annotation.paper.Keyword": Keyword,
    "org.texttechnologylab.annotation.paper.NonTextContent": NonTextContent,
    "org.texttechnologylab.annotation.paper.Reference": Reference,
    "org.texttechnologylab.annotation.paper.Section": Section,
    "org.texttechnologylab.annotation.paper.Source": Source,
    "org.texttechnologylab.annotation.paper.SubTitle": SubTitle,
    "org.texttechnologylab.annotation.paper.Table": Table,
    "org.texttechnologylab.annotation.paper.TextContent": TextContent,
    "org.texttechnologylab.annotation.paper.Title": Title,
    "org.texttechnologylab.annotation.paper.URL": URL_annotation_paper_URL,
}

__all__ = [
    "Abstract",
    "Author",
    "Caption_annotation_paper_Caption",
    "Figure",
    "FloatingElements",
    "Footline",
    "Footnote",
    "Graphic",
    "Headline",
    "Keyword",
    "NonTextContent",
    "Reference",
    "Section",
    "Source",
    "SubTitle",
    "Table",
    "TextContent",
    "Title",
    "URL_annotation_paper_URL",
    "UIMA_TYPE_TO_CLASS",
]
