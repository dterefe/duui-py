"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.semaf.isotimeml.time."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Date_isotimeml_time_Date(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isotimeml.time.Date"
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

class Duration(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isotimeml.time.Duration"
    anchor_time_id: Optional[UimaValue] = None
    beginPoint: Optional[UimaValue] = None
    comment: Optional[str] = None
    endPoint: Optional[UimaValue] = None
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

class Set(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isotimeml.time.Set"
    anchor_time_id: Optional[UimaValue] = None
    comment: Optional[str] = None
    freq: Optional[str] = None
    function_in_document: Optional[str] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    quant: Optional[str] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None
    temporal_function: Optional[bool] = None
    value: Optional[str] = None

class Time_isotimeml_time_Time(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isotimeml.time.Time"
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
    "org.texttechnologylab.annotation.semaf.isotimeml.time.Date": Date_isotimeml_time_Date,
    "org.texttechnologylab.annotation.semaf.isotimeml.time.Duration": Duration,
    "org.texttechnologylab.annotation.semaf.isotimeml.time.Set": Set,
    "org.texttechnologylab.annotation.semaf.isotimeml.time.Time": Time_isotimeml_time_Time,
}

__all__ = [
    "Date_isotimeml_time_Date",
    "Duration",
    "Set",
    "Time_isotimeml_time_Time",
    "UIMA_TYPE_TO_CLASS",
]
