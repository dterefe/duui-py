"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.semaf.isospace."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class EventPath(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.EventPath"
    cardinality: Optional[float] = None
    comment: Optional[str] = None
    countable: Optional[bool] = None
    dcl: Optional[bool] = None
    dimensionality: Optional[str] = None
    domain: Optional[str] = None
    elevation: Optional[UimaValue] = None
    endID: Optional[UimaValue] = None
    form: Optional[str] = None
    gazref: Optional[str] = None
    gquant: Optional[str] = None
    lat: Optional[str] = None
    long: Optional[str] = None
    midID_array: Optional[list[UimaValue]] = None
    midIDs: Optional[list[UimaValue]] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None
    scopes: Optional[list[UimaValue]] = None
    scopes_array: Optional[list[UimaValue]] = None
    spatial_entitiy_type: Optional[str] = None
    spatial_relator: Optional[list[UimaValue]] = None
    spatial_relator_array: Optional[list[UimaValue]] = None
    startID: Optional[UimaValue] = None
    trigger: Optional[UimaValue] = None

class Location_semaf_isospace_Location(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.Location"
    cardinality: Optional[float] = None
    comment: Optional[str] = None
    countable: Optional[bool] = None
    dcl: Optional[bool] = None
    dimensionality: Optional[str] = None
    domain: Optional[str] = None
    elevation: Optional[UimaValue] = None
    form: Optional[str] = None
    gazref: Optional[str] = None
    gquant: Optional[str] = None
    lat: Optional[str] = None
    long: Optional[str] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None
    scopes: Optional[list[UimaValue]] = None
    scopes_array: Optional[list[UimaValue]] = None
    spatial_entitiy_type: Optional[str] = None

class MLink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.MLink"
    bounds: Optional[list[UimaValue]] = None
    bounds_array: Optional[list[UimaValue]] = None
    comment: Optional[str] = None
    end_point1: Optional[UimaValue] = None
    end_point2: Optional[UimaValue] = None
    figure: Optional[UimaValue] = None
    ground: Optional[UimaValue] = None
    rel_type: Optional[str] = None
    trigger: Optional[UimaValue] = None
    val: Optional[UimaValue] = None

class MRelation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.MRelation"
    comment: Optional[str] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None
    value: Optional[str] = None

class Measure(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.Measure"
    comment: Optional[str] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None
    unit: Optional[str] = None
    value: Optional[str] = None

class Motion(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.Motion"
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
    manner: Optional[UimaValue] = None
    mod: Optional[str] = None
    mood: Optional[str] = None
    motion_class: Optional[str] = None
    motion_goal: Optional[UimaValue] = None
    motion_sense: Optional[str] = None
    motion_type: Optional[str] = None
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

class MotionSignal(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.MotionSignal"
    comment: Optional[str] = None
    mod: Optional[str] = None
    motion_signal_type: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None

class MoveLink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.MoveLink"
    adjunct_id: Optional[UimaValue] = None
    comment: Optional[str] = None
    figure: Optional[UimaValue] = None
    goal: Optional[UimaValue] = None
    goal_reached: Optional[str] = None
    ground: Optional[UimaValue] = None
    mid_point: Optional[list[UimaValue]] = None
    mid_point_array: Optional[list[UimaValue]] = None
    motionsignal_id: Optional[UimaValue] = None
    path_id: Optional[UimaValue] = None
    rel_type: Optional[str] = None
    source: Optional[UimaValue] = None
    trigger: Optional[UimaValue] = None

class NonMotionEvent(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.NonMotionEvent"
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

class OLink_semaf_isospace_OLink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.OLink"
    comment: Optional[str] = None
    figure: Optional[UimaValue] = None
    frame_type: Optional[str] = None
    ground: Optional[UimaValue] = None
    projective: Optional[bool] = None
    reference_pt: Optional[UimaValue] = None
    reference_pt_str: Optional[str] = None
    rel_type: Optional[str] = None
    trigger: Optional[UimaValue] = None

class Path(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.Path"
    beginID: Optional[UimaValue] = None
    cardinality: Optional[float] = None
    comment: Optional[str] = None
    countable: Optional[bool] = None
    dcl: Optional[bool] = None
    dimensionality: Optional[str] = None
    domain: Optional[str] = None
    elevation: Optional[UimaValue] = None
    endID: Optional[UimaValue] = None
    form: Optional[str] = None
    gazref: Optional[str] = None
    gquant: Optional[str] = None
    lat: Optional[str] = None
    long: Optional[str] = None
    midID_array: Optional[list[UimaValue]] = None
    midIDs: Optional[list[UimaValue]] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None
    scopes: Optional[list[UimaValue]] = None
    scopes_array: Optional[list[UimaValue]] = None
    spatial_entitiy_type: Optional[str] = None

class Place(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.Place"
    cardinality: Optional[float] = None
    comment: Optional[str] = None
    continent: Optional[str] = None
    countable: Optional[bool] = None
    country: Optional[str] = None
    county: Optional[str] = None
    ctv: Optional[str] = None
    dcl: Optional[bool] = None
    dimensionality: Optional[str] = None
    domain: Optional[str] = None
    elevation: Optional[UimaValue] = None
    form: Optional[str] = None
    gazref: Optional[str] = None
    gquant: Optional[str] = None
    lat: Optional[str] = None
    long: Optional[str] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None
    scopes: Optional[list[UimaValue]] = None
    scopes_array: Optional[list[UimaValue]] = None
    spatial_entitiy_type: Optional[str] = None
    state: Optional[str] = None

class QsLink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.QsLink"
    comment: Optional[str] = None
    figure: Optional[UimaValue] = None
    ground: Optional[UimaValue] = None
    rel_type: Optional[str] = None
    trigger: Optional[UimaValue] = None

class SRelation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.SRelation"
    cluster: Optional[str] = None
    comment: Optional[str] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    relation_type: Optional[str] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None
    value: Optional[str] = None

class SpatialEntity(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.SpatialEntity"
    cardinality: Optional[float] = None
    comment: Optional[str] = None
    countable: Optional[bool] = None
    dcl: Optional[bool] = None
    dimensionality: Optional[str] = None
    domain: Optional[str] = None
    elevation: Optional[UimaValue] = None
    form: Optional[str] = None
    gquant: Optional[str] = None
    lat: Optional[str] = None
    long: Optional[str] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None
    scopes: Optional[list[UimaValue]] = None
    scopes_array: Optional[list[UimaValue]] = None
    spatial_entitiy_type: Optional[str] = None

class SpatialSignal(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.isospace.SpatialSignal"
    cluster: Optional[str] = None
    comment: Optional[str] = None
    mod: Optional[str] = None
    object_feature: Optional[list[UimaValue]] = None
    object_feature_array: Optional[list[UimaValue]] = None
    object_id: Optional[str] = None
    position: Optional[UimaValue] = None
    rotation: Optional[UimaValue] = None
    scale: Optional[UimaValue] = None
    semantic_type: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.semaf.isospace.EventPath": EventPath,
    "org.texttechnologylab.annotation.semaf.isospace.Location": Location_semaf_isospace_Location,
    "org.texttechnologylab.annotation.semaf.isospace.MLink": MLink,
    "org.texttechnologylab.annotation.semaf.isospace.MRelation": MRelation,
    "org.texttechnologylab.annotation.semaf.isospace.Measure": Measure,
    "org.texttechnologylab.annotation.semaf.isospace.Motion": Motion,
    "org.texttechnologylab.annotation.semaf.isospace.MotionSignal": MotionSignal,
    "org.texttechnologylab.annotation.semaf.isospace.MoveLink": MoveLink,
    "org.texttechnologylab.annotation.semaf.isospace.NonMotionEvent": NonMotionEvent,
    "org.texttechnologylab.annotation.semaf.isospace.OLink": OLink_semaf_isospace_OLink,
    "org.texttechnologylab.annotation.semaf.isospace.Path": Path,
    "org.texttechnologylab.annotation.semaf.isospace.Place": Place,
    "org.texttechnologylab.annotation.semaf.isospace.QsLink": QsLink,
    "org.texttechnologylab.annotation.semaf.isospace.SRelation": SRelation,
    "org.texttechnologylab.annotation.semaf.isospace.SpatialEntity": SpatialEntity,
    "org.texttechnologylab.annotation.semaf.isospace.SpatialSignal": SpatialSignal,
}

__all__ = [
    "EventPath",
    "Location_semaf_isospace_Location",
    "MLink",
    "MRelation",
    "Measure",
    "Motion",
    "MotionSignal",
    "MoveLink",
    "NonMotionEvent",
    "OLink_semaf_isospace_OLink",
    "Path",
    "Place",
    "QsLink",
    "SRelation",
    "SpatialEntity",
    "SpatialSignal",
    "UIMA_TYPE_TO_CLASS",
]
