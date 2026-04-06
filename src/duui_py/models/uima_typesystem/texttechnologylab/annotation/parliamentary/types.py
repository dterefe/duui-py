"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.parliamentary."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Agenda(Annotation):
    type: str = "org.texttechnologylab.annotation.parliamentary.Agenda"
    index: Optional[int] = None
    protocol: Optional[UimaValue] = None
    speeches: Optional[list[UimaValue]] = None
    title: Optional[str] = None

class Comment(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.parliamentary.Comment"
    pass

class Protocol(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.parliamentary.Protocol"
    date: Optional[float] = None
    electionPeriod: Optional[int] = None
    sessionNumber: Optional[int] = None

class Speaker_annotation_parliamentary_Speaker(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.parliamentary.Speaker"
    firstName: Optional[str] = None
    group: Optional[str] = None
    id: Optional[str] = None
    lastName: Optional[str] = None
    role: Optional[str] = None

class Speech_annotation_parliamentary_Speech(Annotation):
    type: str = "org.texttechnologylab.annotation.parliamentary.Speech"
    id: Optional[str] = None
    index: Optional[int] = None

class SpeechSection(Annotation):
    type: str = "org.texttechnologylab.annotation.parliamentary.SpeechSection"
    pass

class SpeechText(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.parliamentary.SpeechText"
    speaker: Optional[UimaValue] = None

class Video(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.parliamentary.Video"
    id: Optional[str] = None
    index: Optional[int] = None
    url: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.parliamentary.Agenda": Agenda,
    "org.texttechnologylab.annotation.parliamentary.Comment": Comment,
    "org.texttechnologylab.annotation.parliamentary.Protocol": Protocol,
    "org.texttechnologylab.annotation.parliamentary.Speaker": Speaker_annotation_parliamentary_Speaker,
    "org.texttechnologylab.annotation.parliamentary.Speech": Speech_annotation_parliamentary_Speech,
    "org.texttechnologylab.annotation.parliamentary.SpeechSection": SpeechSection,
    "org.texttechnologylab.annotation.parliamentary.SpeechText": SpeechText,
    "org.texttechnologylab.annotation.parliamentary.Video": Video,
}

__all__ = [
    "Agenda",
    "Comment",
    "Protocol",
    "Speaker_annotation_parliamentary_Speaker",
    "Speech_annotation_parliamentary_Speech",
    "SpeechSection",
    "SpeechText",
    "Video",
    "UIMA_TYPE_TO_CLASS",
]
