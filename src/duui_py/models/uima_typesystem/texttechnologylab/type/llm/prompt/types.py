"""Auto-generated UIMA models for namespace: texttechnologylab.type.llm.prompt."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class FillableMessage(FeatureStructure):
    type: str = "org.texttechnologylab.type.llm.prompt.FillableMessage"
    classModule: Optional[str] = None
    className: Optional[str] = None
    content: Optional[str] = None
    contextName: Optional[str] = None
    role: Optional[str] = None

class Message(Annotation):
    type: str = "org.texttechnologylab.type.llm.prompt.Message"
    classModule: Optional[str] = None
    className: Optional[str] = None
    content: Optional[str] = None
    role: Optional[str] = None

class Prompt(Annotation):
    type: str = "org.texttechnologylab.type.llm.prompt.Prompt"
    args: Optional[str] = None
    messages: Optional[list[UimaValue]] = None
    reference: Optional[UimaValue] = None
    version: Optional[str] = None

class Result(Annotation):
    type: str = "org.texttechnologylab.type.llm.prompt.Result"
    message: Optional[UimaValue] = None
    meta: Optional[str] = None
    prompt: Optional[UimaValue] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.llm.prompt.FillableMessage": FillableMessage,
    "org.texttechnologylab.type.llm.prompt.Message": Message,
    "org.texttechnologylab.type.llm.prompt.Prompt": Prompt,
    "org.texttechnologylab.type.llm.prompt.Result": Result,
}

__all__ = [
    "FillableMessage",
    "Message",
    "Prompt",
    "Result",
    "UIMA_TYPE_TO_CLASS",
]
