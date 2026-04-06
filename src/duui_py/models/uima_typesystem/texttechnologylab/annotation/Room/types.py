"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.Room."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Object(Annotation):
    type: str = "org.texttechnologylab.annotation.Room.Object"
    fatherObject: Optional[UimaValue] = None
    location: Optional[UimaValue] = None
    name: Optional[str] = None
    nextTimeObject: Optional[UimaValue] = None
    objectFeature: Optional[list[UimaValue]] = None
    prevTimeObject: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[float] = None
    shapeNetID: Optional[str] = None
    timeReference: Optional[UimaValue] = None

class ObjectAttribute(Annotation):
    type: str = "org.texttechnologylab.annotation.Room.ObjectAttribute"
    key: Optional[str] = None
    value: Optional[str] = None

class RoomWall(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Room.RoomWall"
    feature: Optional[list[UimaValue]] = None
    height: Optional[float] = None
    vectorlist: Optional[list[UimaValue]] = None

class TimeChain(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.Room.TimeChain"
    next: Optional[UimaValue] = None
    prev: Optional[UimaValue] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.Room.Object": Object,
    "org.texttechnologylab.annotation.Room.ObjectAttribute": ObjectAttribute,
    "org.texttechnologylab.annotation.Room.RoomWall": RoomWall,
    "org.texttechnologylab.annotation.Room.TimeChain": TimeChain,
}

__all__ = [
    "Object",
    "ObjectAttribute",
    "RoomWall",
    "TimeChain",
    "UIMA_TYPE_TO_CLASS",
]
