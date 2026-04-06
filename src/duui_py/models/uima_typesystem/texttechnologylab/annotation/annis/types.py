"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.annis."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Annotation(Annotation):
    type: str = "org.texttechnologylab.annotation.annis.Annotation"
    value: Optional[str] = None

class Chapter(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.Chapter"
    value: Optional[str] = None

class Clause(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.Clause"
    value: Optional[str] = None

class Inflection(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.Inflection"
    value: Optional[str] = None

class InflectionClass(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.InflectionClass"
    value: Optional[str] = None

class InflectionClassLemma(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.InflectionClassLemma"
    value: Optional[str] = None

class Language_annotation_annis_Language(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.Language"
    value: Optional[str] = None

class Line(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.Line"
    value: Optional[str] = None

class Page(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.Page"
    value: Optional[str] = None

class PosLemma(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.PosLemma"
    value: Optional[str] = None

class Rhyme(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.Rhyme"
    value: Optional[str] = None

class SubChapter(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.SubChapter"
    value: Optional[str] = None

class Translation_annotation_annis_Translation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.Translation"
    value: Optional[str] = None

class Variation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.Variation"
    layer: Optional[str] = None
    value: Optional[str] = None

class Verse(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.Verse"
    value: Optional[str] = None

class Writer(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.annis.Writer"
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.annis.Annotation": Annotation,
    "org.texttechnologylab.annotation.annis.Chapter": Chapter,
    "org.texttechnologylab.annotation.annis.Clause": Clause,
    "org.texttechnologylab.annotation.annis.Inflection": Inflection,
    "org.texttechnologylab.annotation.annis.InflectionClass": InflectionClass,
    "org.texttechnologylab.annotation.annis.InflectionClassLemma": InflectionClassLemma,
    "org.texttechnologylab.annotation.annis.Language": Language_annotation_annis_Language,
    "org.texttechnologylab.annotation.annis.Line": Line,
    "org.texttechnologylab.annotation.annis.Page": Page,
    "org.texttechnologylab.annotation.annis.PosLemma": PosLemma,
    "org.texttechnologylab.annotation.annis.Rhyme": Rhyme,
    "org.texttechnologylab.annotation.annis.SubChapter": SubChapter,
    "org.texttechnologylab.annotation.annis.Translation": Translation_annotation_annis_Translation,
    "org.texttechnologylab.annotation.annis.Variation": Variation,
    "org.texttechnologylab.annotation.annis.Verse": Verse,
    "org.texttechnologylab.annotation.annis.Writer": Writer,
}

__all__ = [
    "Annotation",
    "Chapter",
    "Clause",
    "Inflection",
    "InflectionClass",
    "InflectionClassLemma",
    "Language_annotation_annis_Language",
    "Line",
    "Page",
    "PosLemma",
    "Rhyme",
    "SubChapter",
    "Translation_annotation_annis_Translation",
    "Variation",
    "Verse",
    "Writer",
    "UIMA_TYPE_TO_CLASS",
]
