"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.context.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class EventContext(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.context.type.EventContext"
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

class LocationContext(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.context.type.LocationContext"
    Id: Optional[str] = None
    ReferencedID: Optional[int] = None
    areaSize: Optional[str] = None
    attribute: Optional[UimaValue] = None
    contextInf: Optional[str] = None
    country: Optional[str] = None
    create: Optional[int] = None
    displayName: Optional[str] = None
    geoJson: Optional[str] = None
    geoNamesID: Optional[int] = None
    image: Optional[str] = None
    label: Optional[str] = None
    latLngs: Optional[list[float]] = None
    markerPoint: Optional[list[float]] = None
    modified: Optional[int] = None
    numberOfCitizen: Optional[float] = None
    user: Optional[str] = None
    wikiDataID: Optional[str] = None

class OrganisationContext(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.context.type.OrganisationContext"
    Id: Optional[str] = None
    ReferencedID: Optional[int] = None
    attribute: Optional[UimaValue] = None
    chiefExecutiveOfficer: Optional[str] = None
    contextInf: Optional[str] = None
    create: Optional[int] = None
    displayName: Optional[str] = None
    foundingDate: Optional[str] = None
    headquarter: Optional[str] = None
    image: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    setLabel: Optional[str] = None
    user: Optional[str] = None
    website: Optional[str] = None
    wikiDataID: Optional[str] = None

class PersonContext(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.context.type.PersonContext"
    Id: Optional[str] = None
    Name: Optional[str] = None
    ReferencedID: Optional[int] = None
    attribute: Optional[UimaValue] = None
    birthDate: Optional[str] = None
    birthPlace: Optional[str] = None
    contextInf: Optional[str] = None
    create: Optional[int] = None
    displayName: Optional[str] = None
    fieldOfWork: Optional[str] = None
    gender: Optional[str] = None
    image: Optional[str] = None
    label: Optional[str] = None
    modified: Optional[int] = None
    user: Optional[str] = None
    wikiDataID: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.context.type.EventContext": EventContext,
    "org.texttechnologylab.annotation.context.type.LocationContext": LocationContext,
    "org.texttechnologylab.annotation.context.type.OrganisationContext": OrganisationContext,
    "org.texttechnologylab.annotation.context.type.PersonContext": PersonContext,
}

__all__ = [
    "EventContext",
    "LocationContext",
    "OrganisationContext",
    "PersonContext",
    "UIMA_TYPE_TO_CLASS",
]
