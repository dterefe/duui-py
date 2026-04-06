"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.semaf.isobase."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Entity(Annotation):
    type: str = "org.texttechnologylab.annotation.semaf.isobase.Entity"
    comment: Optional[str] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None

class Event_semaf_isobase_Event(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isobase.Event"
    aspect: Optional[str] = None
    comment: Optional[str] = None
    countable: Optional[bool] = None
    domain: Optional[str] = None
    elevation: Optional[UimaValue] = None
    event_class: Optional[str] = None
    event_frame: Optional[str] = None
    event_type: Optional[str] = None
    gquant: Optional[str] = None
    lat: Optional[str] = None
    long: Optional[str] = None
    mod: Optional[str] = None
    mood: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    polarity: Optional[str] = None
    pos: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None
    scopes: Optional[list[UimaValue]] = None
    scopes_array: Optional[list[UimaValue]] = None
    tense: Optional[str] = None
    vform: Optional[str] = None

class Link_semaf_isobase_Link(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isobase.Link"
    comment: Optional[str] = None
    figure: Optional[UimaValue] = None
    ground: Optional[UimaValue] = None
    rel_type: Optional[str] = None
    trigger: Optional[UimaValue] = None

class Signal(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isobase.Signal"
    comment: Optional[str] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.semaf.isobase.Entity": Entity,
    "org.texttechnologylab.annotation.semaf.isobase.Event": Event_semaf_isobase_Event,
    "org.texttechnologylab.annotation.semaf.isobase.Link": Link_semaf_isobase_Link,
    "org.texttechnologylab.annotation.semaf.isobase.Signal": Signal,
}

__all__ = [
    "Entity",
    "Event_semaf_isobase_Event",
    "Link_semaf_isobase_Link",
    "Signal",
    "UIMA_TYPE_TO_CLASS",
]
