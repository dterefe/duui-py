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


class UCEImport(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.uce.UCEImport"
    finishedAt: Optional[str] = None
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    startedAt: Optional[str] = None
    status: Optional[str] = None
    uri: Optional[str] = None


class UCECorpus(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.uce.UCECorpus"
    configHash: Optional[str] = None
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    sourcePath: Optional[str] = None
    uri: Optional[str] = None


class UCEDocument(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.uce.UCEDocument"
    corpusId: Optional[str] = None
    documentId: Optional[str] = None
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    sourcePath: Optional[str] = None
    uri: Optional[str] = None


class UCEPage(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.uce.UCEPage"
    corpusId: Optional[str] = None
    documentId: Optional[str] = None
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    pageNumber: Optional[int] = None
    uri: Optional[str] = None


class UCEView(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.uce.UCEView"
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    uri: Optional[str] = None
    viewName: Optional[str] = None


class UCEType(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.uce.UCEType"
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    superTypeName: Optional[str] = None
    typeName: Optional[str] = None
    uri: Optional[str] = None


class UCEAnnotation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.uce.UCEAnnotation"
    beginOffset: Optional[int] = None
    coveredText: Optional[str] = None
    endOffset: Optional[int] = None
    featureJson: Optional[str] = None
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    typeName: Optional[str] = None
    uri: Optional[str] = None


class UCEOperation(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.uce.UCEOperation"
    error: Optional[str] = None
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    operationName: Optional[str] = None
    retries: Optional[int] = None
    status: Optional[str] = None
    uri: Optional[str] = None


UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.uce.Metadata": Metadata,
    "org.texttechnologylab.annotation.uce.MetadataValueType": MetadataValueType,
    "org.texttechnologylab.annotation.uce.Permission": Permission,
    "org.texttechnologylab.annotation.uce.PermissionLevel": PermissionLevel,
    "org.texttechnologylab.annotation.uce.PermissionType": PermissionType,
    "org.texttechnologylab.annotation.uce.UCEImport": UCEImport,
    "org.texttechnologylab.annotation.uce.UCECorpus": UCECorpus,
    "org.texttechnologylab.annotation.uce.UCEDocument": UCEDocument,
    "org.texttechnologylab.annotation.uce.UCEPage": UCEPage,
    "org.texttechnologylab.annotation.uce.UCEView": UCEView,
    "org.texttechnologylab.annotation.uce.UCEType": UCEType,
    "org.texttechnologylab.annotation.uce.UCEAnnotation": UCEAnnotation,
    "org.texttechnologylab.annotation.uce.UCEOperation": UCEOperation,
}

__all__ = [
    "Metadata",
    "MetadataValueType",
    "Permission",
    "PermissionLevel",
    "PermissionType",
    "UCEImport",
    "UCECorpus",
    "UCEDocument",
    "UCEPage",
    "UCEView",
    "UCEType",
    "UCEAnnotation",
    "UCEOperation",
    "UIMA_TYPE_TO_CLASS",
]
