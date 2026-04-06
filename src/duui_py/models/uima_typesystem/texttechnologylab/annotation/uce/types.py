"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.uce."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class Metadata(Annotation):
    type: str = "org.texttechnologylab.annotation.uce.Metadata"
    comment: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None
    valueType: Optional[UimaValue] = None

class MetadataValueType(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.uce.MetadataValueType"
    pass

class Permission(Annotation):
    type: str = "org.texttechnologylab.annotation.uce.Permission"
    permissionLevel: Optional[UimaValue] = None
    permissionType: Optional[UimaValue] = None
    user: Optional[str] = None

class PermissionLevel(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.uce.PermissionLevel"
    pass

class PermissionType(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.uce.PermissionType"
    pass

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.uce.Metadata": Metadata,
    "org.texttechnologylab.annotation.uce.MetadataValueType": MetadataValueType,
    "org.texttechnologylab.annotation.uce.Permission": Permission,
    "org.texttechnologylab.annotation.uce.PermissionLevel": PermissionLevel,
    "org.texttechnologylab.annotation.uce.PermissionType": PermissionType,
}

__all__ = [
    "Metadata",
    "MetadataValueType",
    "Permission",
    "PermissionLevel",
    "PermissionType",
    "UIMA_TYPE_TO_CLASS",
]
