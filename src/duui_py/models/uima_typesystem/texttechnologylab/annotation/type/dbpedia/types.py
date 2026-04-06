"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.type.dbpedia."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class DBPediaObject(Annotation):
    type: str = "org.texttechnologylab.annotation.type.dbpedia.DBPediaObject"
    percentageOfSecondRank: Optional[float] = None
    similarityScore: Optional[float] = None
    types: Optional[list[UimaValue]] = None
    uri: Optional[str] = None

class DBPediaType(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.type.dbpedia.DBPediaType"
    uri: Optional[str] = None
    value: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.type.dbpedia.DBPediaObject": DBPediaObject,
    "org.texttechnologylab.annotation.type.dbpedia.DBPediaType": DBPediaType,
}

__all__ = [
    "DBPediaObject",
    "DBPediaType",
    "UIMA_TYPE_TO_CLASS",
]
