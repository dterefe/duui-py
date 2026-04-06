"""Auto-generated UIMA models for namespace: de.tudarmstadt.ukp.dkpro.core.api.metadata.type."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class DocumentMetaData(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.metadata.type.DocumentMetaData"
    collectionId: Optional[str] = None
    documentBaseUri: Optional[str] = None
    documentId: Optional[str] = None
    documentTitle: Optional[str] = None
    documentUri: Optional[str] = None
    isLastSegment: Optional[bool] = None

class MetaDataStringField(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.metadata.type.MetaDataStringField"
    key: Optional[str] = None
    value: Optional[str] = None

class TagDescription(FeatureStructure):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.metadata.type.TagDescription"
    name: Optional[str] = None

class TagsetDescription(Annotation):
    type: str = "de.tudarmstadt.ukp.dkpro.core.api.metadata.type.TagsetDescription"
    componentName: Optional[str] = None
    input: Optional[bool] = None
    layer: Optional[str] = None
    modelLanguage: Optional[str] = None
    modelLocation: Optional[str] = None
    modelVariant: Optional[str] = None
    modelVersion: Optional[str] = None
    name: Optional[str] = None
    tags: Optional[list[UimaValue]] = None

UIMA_TYPE_TO_CLASS = {
    "de.tudarmstadt.ukp.dkpro.core.api.metadata.type.DocumentMetaData": DocumentMetaData,
    "de.tudarmstadt.ukp.dkpro.core.api.metadata.type.MetaDataStringField": MetaDataStringField,
    "de.tudarmstadt.ukp.dkpro.core.api.metadata.type.TagDescription": TagDescription,
    "de.tudarmstadt.ukp.dkpro.core.api.metadata.type.TagsetDescription": TagsetDescription,
}

__all__ = [
    "DocumentMetaData",
    "MetaDataStringField",
    "TagDescription",
    "TagsetDescription",
    "UIMA_TYPE_TO_CLASS",
]
