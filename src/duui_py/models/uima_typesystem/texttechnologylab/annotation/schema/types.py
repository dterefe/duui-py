"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.schema."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class AnnotationAttribute(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.schema.AnnotationAttribute"
    key: Optional[UimaValue] = None
    value: Optional[str] = None

class AnnotationClass(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.schema.AnnotationClass"
    attributes: Optional[list[UimaValue]] = None
    description: Optional[str] = None
    name: Optional[str] = None

class AnnotationObject(Annotation):
    type: str = "org.texttechnologylab.annotation.schema.AnnotationObject"
    annotationType: Optional[UimaValue] = None
    attributes: Optional[list[UimaValue]] = None
    comment: Optional[str] = None

class AnnotationRelation_annotation_schema_AnnotationRelation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.schema.AnnotationRelation"
    attributes: Optional[list[UimaValue]] = None
    key: Optional[UimaValue] = None
    value: Optional[str] = None

class Attribute(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.schema.Attribute"
    description: Optional[str] = None
    mandatory: Optional[bool] = None
    name: Optional[str] = None
    range: Optional[UimaValue] = None

class Relation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.schema.Relation"
    attributes: Optional[list[UimaValue]] = None
    description: Optional[str] = None
    mandatory: Optional[bool] = None
    name: Optional[str] = None
    range: Optional[UimaValue] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.schema.AnnotationAttribute": AnnotationAttribute,
    "org.texttechnologylab.annotation.schema.AnnotationClass": AnnotationClass,
    "org.texttechnologylab.annotation.schema.AnnotationObject": AnnotationObject,
    "org.texttechnologylab.annotation.schema.AnnotationRelation": AnnotationRelation_annotation_schema_AnnotationRelation,
    "org.texttechnologylab.annotation.schema.Attribute": Attribute,
    "org.texttechnologylab.annotation.schema.Relation": Relation,
}

__all__ = [
    "AnnotationAttribute",
    "AnnotationClass",
    "AnnotationObject",
    "AnnotationRelation_annotation_schema_AnnotationRelation",
    "Attribute",
    "Relation",
    "UIMA_TYPE_TO_CLASS",
]
