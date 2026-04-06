"""Auto-generated UIMA models for namespace: texttechnologylab.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class LLMPrefixPrompt(Annotation):
    type: str = "org.texttechnologylab.type.LLMPrefixPrompt"
    message: Optional[str] = None

class LLMPrompt(Annotation):
    type: str = "org.texttechnologylab.type.LLMPrompt"
    prefix: Optional[UimaValue] = None
    prompt: Optional[str] = None
    suffix: Optional[UimaValue] = None
    systemPrompt: Optional[UimaValue] = None

class LLMResult(Annotation):
    type: str = "org.texttechnologylab.type.LLMResult"
    content: Optional[str] = None
    meta: Optional[str] = None
    prompt: Optional[UimaValue] = None
    result: Optional[str] = None

class LLMSuffixPrompt(Annotation):
    type: str = "org.texttechnologylab.type.LLMSuffixPrompt"
    message: Optional[str] = None

class LLMSystemPrompt(Annotation):
    type: str = "org.texttechnologylab.type.LLMSystemPrompt"
    message: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.LLMPrefixPrompt": LLMPrefixPrompt,
    "org.texttechnologylab.type.LLMPrompt": LLMPrompt,
    "org.texttechnologylab.type.LLMResult": LLMResult,
    "org.texttechnologylab.type.LLMSuffixPrompt": LLMSuffixPrompt,
    "org.texttechnologylab.type.LLMSystemPrompt": LLMSystemPrompt,
}

__all__ = [
    "LLMPrefixPrompt",
    "LLMPrompt",
    "LLMResult",
    "LLMSuffixPrompt",
    "LLMSystemPrompt",
    "UIMA_TYPE_TO_CLASS",
]
