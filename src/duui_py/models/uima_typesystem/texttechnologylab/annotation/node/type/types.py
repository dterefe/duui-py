"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.node.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Context(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.node.type.Context"
    Id: Optional[str] = None
    ReferencedID: Optional[int] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    displayName: Optional[str] = None
    image: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None
    wikiDataID: Optional[str] = None

class DepthList(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.node.type.DepthList"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    displayName: Optional[str] = None
    hierarchie: Optional[list[int]] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None

class EntityVis(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.node.type.EntityVis"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    displayName: Optional[str] = None
    geoJson: Optional[str] = None
    geonamesID: Optional[int] = None
    image: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    ofClass: Optional[str] = None
    user: Optional[str] = None
    wikiDataID: Optional[str] = None

class IndividualVis(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.node.type.IndividualVis"
    Id: Optional[str] = None
    URI: Optional[str] = None
    areaSize: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    displayName: Optional[str] = None
    geoJson: Optional[str] = None
    geonamesID: Optional[int] = None
    image: Optional[str] = None
    label: Optional[str] = None
    markerPoint: Optional[list[float]] = None
    modified: Optional[int] = None
    ofClass: Optional[str] = None
    user: Optional[str] = None
    wikiDataID: Optional[str] = None

class RelationContext(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.node.type.RelationContext"
    Id: Optional[str] = None
    ReferencedID: Optional[int] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    displayName: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    relatesTo: Optional[str] = None
    user: Optional[str] = None
    wikiDataID: Optional[str] = None

class RelationGroup(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.node.type.RelationGroup"
    Id: Optional[str] = None
    attribute: Optional[UimaValue] = None
    create: Optional[int] = None
    label: Optional[str] = None
    locationID: Optional[int] = None
    modified: Optional[int] = None
    relation: Optional[UimaValue] = None
    sentence: Optional[int] = None
    user: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.node.type.Context": Context,
    "org.texttechnologylab.annotation.node.type.DepthList": DepthList,
    "org.texttechnologylab.annotation.node.type.EntityVis": EntityVis,
    "org.texttechnologylab.annotation.node.type.IndividualVis": IndividualVis,
    "org.texttechnologylab.annotation.node.type.RelationContext": RelationContext,
    "org.texttechnologylab.annotation.node.type.RelationGroup": RelationGroup,
}

__all__ = [
    "Context",
    "DepthList",
    "EntityVis",
    "IndividualVis",
    "RelationContext",
    "RelationGroup",
    "UIMA_TYPE_TO_CLASS",
]
