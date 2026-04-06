"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.semaf.isotimeml."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ALink_semaf_isotimeml_ALink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isotimeml.ALink"
    comment: Optional[str] = None
    figure: Optional[UimaValue] = None
    ground: Optional[UimaValue] = None
    rel_type: Optional[str] = None
    syntax: Optional[str] = None
    trigger: Optional[UimaValue] = None

class MLink_semaf_isotimeml_MLink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isotimeml.MLink"
    comment: Optional[str] = None
    event_id: Optional[UimaValue] = None
    figure: Optional[UimaValue] = None
    ground: Optional[UimaValue] = None
    rel_type: Optional[str] = None
    related_to_time: Optional[UimaValue] = None
    trigger: Optional[UimaValue] = None

class SLink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isotimeml.SLink"
    comment: Optional[str] = None
    figure: Optional[UimaValue] = None
    ground: Optional[UimaValue] = None
    origin: Optional[str] = None
    rel_type: Optional[str] = None
    trigger: Optional[UimaValue] = None

class TLink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isotimeml.TLink"
    comment: Optional[str] = None
    figure: Optional[UimaValue] = None
    ground: Optional[UimaValue] = None
    origin: Optional[str] = None
    rel_type: Optional[str] = None
    syntax: Optional[str] = None
    trigger: Optional[UimaValue] = None

class TimeSignal(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isotimeml.TimeSignal"
    comment: Optional[str] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None

class TimeX3(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isotimeml.TimeX3"
    anchor_time_id: Optional[UimaValue] = None
    comment: Optional[str] = None
    function_in_document: Optional[str] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None
    temporal_function: Optional[bool] = None
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.semaf.isotimeml.ALink": ALink_semaf_isotimeml_ALink,
    "org.texttechnologylab.annotation.semaf.isotimeml.MLink": MLink_semaf_isotimeml_MLink,
    "org.texttechnologylab.annotation.semaf.isotimeml.SLink": SLink,
    "org.texttechnologylab.annotation.semaf.isotimeml.TLink": TLink,
    "org.texttechnologylab.annotation.semaf.isotimeml.TimeSignal": TimeSignal,
    "org.texttechnologylab.annotation.semaf.isotimeml.TimeX3": TimeX3,
}

__all__ = [
    "ALink_semaf_isotimeml_ALink",
    "MLink_semaf_isotimeml_MLink",
    "SLink",
    "TLink",
    "TimeSignal",
    "TimeX3",
    "UIMA_TYPE_TO_CLASS",
]
