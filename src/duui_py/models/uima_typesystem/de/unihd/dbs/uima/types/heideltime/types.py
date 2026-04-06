"""Auto-generated UIMA models for namespace: de.unihd.dbs.uima.types.heideltime."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Dct(Annotation):
    type: str = "de.unihd.dbs.uima.types.heideltime.Dct"
    filename: Optional[str] = None
    timexId: Optional[str] = None
    value: Optional[str] = None

class Event_types_heideltime_Event(Annotation):
    type: str = "de.unihd.dbs.uima.types.heideltime.Event"
    aspect: Optional[str] = None
    eventId: Optional[str] = None
    eventInstanceId: Optional[int] = None
    filename: Optional[str] = None
    modality: Optional[str] = None
    polarity: Optional[str] = None
    sentId: Optional[int] = None
    tense: Optional[str] = None
    tokId: Optional[int] = None
    token: Optional[UimaValue] = None

class GoldEvent(FeatureStructure):
    type: str = "de.unihd.dbs.uima.types.heideltime.GoldEvent"
    aspect: Optional[str] = None
    eventId: Optional[str] = None
    eventInstanceId: Optional[int] = None
    filename: Optional[str] = None
    modality: Optional[str] = None
    polarity: Optional[str] = None
    sentId: Optional[int] = None
    tense: Optional[str] = None
    tokId: Optional[int] = None
    token: Optional[UimaValue] = None

class IntervalCandidateSentence(FeatureStructure):
    type: str = "de.unihd.dbs.uima.types.heideltime.IntervalCandidateSentence"
    filename: Optional[str] = None
    sentenceId: Optional[int] = None

class Sentence_types_heideltime_Sentence(Annotation):
    type: str = "de.unihd.dbs.uima.types.heideltime.Sentence"
    filename: Optional[str] = None
    sentenceId: Optional[int] = None

class SourceDocInfo(Annotation):
    type: str = "de.unihd.dbs.uima.types.heideltime.SourceDocInfo"
    offsetInSource: Optional[int] = None
    uri: Optional[str] = None

class Timex3(Annotation):
    type: str = "de.unihd.dbs.uima.types.heideltime.Timex3"
    allTokIds: Optional[str] = None
    emptyValue: Optional[str] = None
    filename: Optional[str] = None
    firstTokId: Optional[int] = None
    foundByRule: Optional[str] = None
    sentId: Optional[int] = None
    timexFreq: Optional[str] = None
    timexId: Optional[str] = None
    timexInstance: Optional[int] = None
    timexMod: Optional[str] = None
    timexQuant: Optional[str] = None
    timexType: Optional[str] = None
    timexValue: Optional[str] = None

class Timex3Interval(FeatureStructure):
    type: str = "de.unihd.dbs.uima.types.heideltime.Timex3Interval"
    TimexValueEB: Optional[str] = None
    TimexValueEE: Optional[str] = None
    TimexValueLB: Optional[str] = None
    TimexValueLE: Optional[str] = None
    allTokIds: Optional[str] = None
    beginTimex: Optional[str] = None
    emptyValue: Optional[str] = None
    endTimex: Optional[str] = None
    filename: Optional[str] = None
    firstTokId: Optional[int] = None
    foundByRule: Optional[str] = None
    sentId: Optional[int] = None
    timexFreq: Optional[str] = None
    timexId: Optional[str] = None
    timexInstance: Optional[int] = None
    timexMod: Optional[str] = None
    timexQuant: Optional[str] = None
    timexType: Optional[str] = None
    timexValue: Optional[str] = None

class Token_types_heideltime_Token(Annotation):
    type: str = "de.unihd.dbs.uima.types.heideltime.Token"
    filename: Optional[str] = None
    pos: Optional[str] = None
    sentId: Optional[int] = None
    tokenId: Optional[int] = None

UIMA_TYPE_TO_CLASS = {
    "de.unihd.dbs.uima.types.heideltime.Dct": Dct,
    "de.unihd.dbs.uima.types.heideltime.Event": Event_types_heideltime_Event,
    "de.unihd.dbs.uima.types.heideltime.GoldEvent": GoldEvent,
    "de.unihd.dbs.uima.types.heideltime.IntervalCandidateSentence": IntervalCandidateSentence,
    "de.unihd.dbs.uima.types.heideltime.Sentence": Sentence_types_heideltime_Sentence,
    "de.unihd.dbs.uima.types.heideltime.SourceDocInfo": SourceDocInfo,
    "de.unihd.dbs.uima.types.heideltime.Timex3": Timex3,
    "de.unihd.dbs.uima.types.heideltime.Timex3Interval": Timex3Interval,
    "de.unihd.dbs.uima.types.heideltime.Token": Token_types_heideltime_Token,
}

__all__ = [
    "Dct",
    "Event_types_heideltime_Event",
    "GoldEvent",
    "IntervalCandidateSentence",
    "Sentence_types_heideltime_Sentence",
    "SourceDocInfo",
    "Timex3",
    "Timex3Interval",
    "Token_types_heideltime_Token",
    "UIMA_TYPE_TO_CLASS",
]
