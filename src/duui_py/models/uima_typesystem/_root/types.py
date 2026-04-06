"""Auto-generated UIMA models for namespace: _root."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class GeoNamesFeatureClass(FeatureStructure):
    type: str = "GeoNamesFeatureClass"
    pass

class GeoNamesFeatureCode(FeatureStructure):
    type: str = "GeoNamesFeatureCode"
    pass

UIMA_TYPE_TO_CLASS = {
    "GeoNamesFeatureClass": GeoNamesFeatureClass,
    "GeoNamesFeatureCode": GeoNamesFeatureCode,
}

__all__ = [
    "GeoNamesFeatureClass",
    "GeoNamesFeatureCode",
    "UIMA_TYPE_TO_CLASS",
]
