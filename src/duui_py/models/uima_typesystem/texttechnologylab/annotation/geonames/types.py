"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.geonames."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class GeoNamesEntity_annotation_geonames_GeoNamesEntity(Annotation):
    type: str = "org.texttechnologylab.annotation.geonames.GeoNamesEntity"
    adm1: Optional[str] = None
    adm2: Optional[str] = None
    adm3: Optional[str] = None
    adm4: Optional[str] = None
    countryCode: Optional[str] = None
    elevation: Optional[int] = None
    featureClass: Optional[UimaValue] = None
    featureCode: Optional[UimaValue] = None
    id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    name: Optional[str] = None
    referenceAnnotation: Optional[UimaValue] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.geonames.GeoNamesEntity": GeoNamesEntity_annotation_geonames_GeoNamesEntity,
}

__all__ = [
    "GeoNamesEntity_annotation_geonames_GeoNamesEntity",
    "UIMA_TYPE_TO_CLASS",
]
