"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.core."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Answer(Annotation):
    type: str = "org.texttechnologylab.annotation.core.Answer"
    description: Optional[str] = None
    key: Optional[str] = None

class Category(Annotation):
    type: str = "org.texttechnologylab.annotation.core.Category"
    description: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None

class Question(Annotation):
    type: str = "org.texttechnologylab.annotation.core.Question"
    description: Optional[str] = None
    key: Optional[str] = None

class URLToken(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.core.URLToken"
    form: Optional[UimaValue] = None
    id: Optional[str] = None
    lemma: Optional[UimaValue] = None
    morph: Optional[UimaValue] = None
    order: Optional[int] = None
    parent: Optional[UimaValue] = None
    pos: Optional[UimaValue] = None
    stem: Optional[UimaValue] = None
    syntacticFunction: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.core.Answer": Answer,
    "org.texttechnologylab.annotation.core.Category": Category,
    "org.texttechnologylab.annotation.core.Question": Question,
    "org.texttechnologylab.annotation.core.URLToken": URLToken,
}

__all__ = [
    "Answer",
    "Category",
    "Question",
    "URLToken",
    "UIMA_TYPE_TO_CLASS",
]
