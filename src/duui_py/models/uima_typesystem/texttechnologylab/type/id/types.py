"""Auto-generated UIMA models for namespace: texttechnologylab.type.id."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class URI(Annotation):
    type: str = "org.texttechnologylab.type.id.URI"
    fragment: Optional[str] = None
    host: Optional[str] = None
    password: Optional[str] = None
    path: Optional[str] = None
    port: Optional[int] = None
    query: Optional[str] = None
    scheme: Optional[str] = None
    user: Optional[str] = None

class URL_type_id_URL(FeatureStructure):
    type: str = "org.texttechnologylab.type.id.URL"
    fragment: Optional[str] = None
    host: Optional[str] = None
    password: Optional[str] = None
    path: Optional[str] = None
    port: Optional[int] = None
    query: Optional[str] = None
    scheme: Optional[str] = None
    user: Optional[str] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.type.id.URI": URI,
    "org.texttechnologylab.type.id.URL": URL_type_id_URL,
}

__all__ = [
    "URI",
    "URL_type_id_URL",
    "UIMA_TYPE_TO_CLASS",
]
