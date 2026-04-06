"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.semaf.IsoSpatial."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ObjectAttribute_semaf_IsoSpatial_ObjectAttribute(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.IsoSpatial.ObjectAttribute"
    key: Optional[str] = None
    value: Optional[str] = None

class Vec3(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.IsoSpatial.Vec3"
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

class Vec4(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.semaf.IsoSpatial.Vec4"
    w: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.semaf.IsoSpatial.ObjectAttribute": ObjectAttribute_semaf_IsoSpatial_ObjectAttribute,
    "org.texttechnologylab.annotation.semaf.IsoSpatial.Vec3": Vec3,
    "org.texttechnologylab.annotation.semaf.IsoSpatial.Vec4": Vec4,
}

__all__ = [
    "ObjectAttribute_semaf_IsoSpatial_ObjectAttribute",
    "Vec3",
    "Vec4",
    "UIMA_TYPE_TO_CLASS",
]
