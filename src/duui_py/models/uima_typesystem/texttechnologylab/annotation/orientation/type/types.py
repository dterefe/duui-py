"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.orientation.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Above(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.Above"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class After(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.After"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class Around(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.Around"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class At(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.At"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class Behind(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.Behind"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class Below(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.Below"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class Between(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.Between"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class In(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.In"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class Infront(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.Infront"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class Left(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.Left"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class NotAt(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.NotAt"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class On(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.On"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

class Right(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.orientation.type.Right"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    edgetype: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    source: Optional[UimaValue] = None
    target: Optional[UimaValue] = None
    user: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.orientation.type.Above": Above,
    "org.texttechnologylab.annotation.orientation.type.After": After,
    "org.texttechnologylab.annotation.orientation.type.Around": Around,
    "org.texttechnologylab.annotation.orientation.type.At": At,
    "org.texttechnologylab.annotation.orientation.type.Behind": Behind,
    "org.texttechnologylab.annotation.orientation.type.Below": Below,
    "org.texttechnologylab.annotation.orientation.type.Between": Between,
    "org.texttechnologylab.annotation.orientation.type.In": In,
    "org.texttechnologylab.annotation.orientation.type.Infront": Infront,
    "org.texttechnologylab.annotation.orientation.type.Left": Left,
    "org.texttechnologylab.annotation.orientation.type.NotAt": NotAt,
    "org.texttechnologylab.annotation.orientation.type.On": On,
    "org.texttechnologylab.annotation.orientation.type.Right": Right,
}

__all__ = [
    "Above",
    "After",
    "Around",
    "At",
    "Behind",
    "Below",
    "Between",
    "In",
    "Infront",
    "Left",
    "NotAt",
    "On",
    "Right",
    "UIMA_TYPE_TO_CLASS",
]
