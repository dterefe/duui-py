"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.link."""

from __future__ import annotations

from typing import Optional
from pydantic import Field

from duui_py.models.uima import Annotation, FeatureStructure, UimaValue

class ADLink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.link.ADLink"
    from_: Optional[UimaValue] = Field(default=None, alias="from")
    linkId: Optional[int] = None
    linkType: Optional[str] = None
    to: Optional[str] = None

class ALink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.link.ALink"
    from_: Optional[UimaValue] = Field(default=None, alias="from")
    linkId: Optional[int] = None
    linkType: Optional[str] = None
    to: Optional[UimaValue] = None

class DALink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.link.DALink"
    from_: Optional[str] = Field(default=None, alias="from")
    linkId: Optional[int] = None
    linkType: Optional[str] = None
    to: Optional[UimaValue] = None

class DLink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.link.DLink"
    from_: Optional[str] = Field(default=None, alias="from")
    linkId: Optional[int] = None
    linkType: Optional[str] = None
    to: Optional[str] = None

class Link(Annotation):
    type: str = "org.texttechnologylab.annotation.link.Link"
    linkId: Optional[int] = None
    linkType: Optional[str] = None

class OLink(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.link.OLink"
    from_: Optional[str] = Field(default=None, alias="from")
    fromBegin: Optional[int] = None
    fromEnd: Optional[int] = None
    linkId: Optional[int] = None
    linkType: Optional[str] = None
    to: Optional[str] = None
    toBegin: Optional[int] = None
    toEnd: Optional[int] = None

UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.link.ADLink": ADLink,
    "org.texttechnologylab.annotation.link.ALink": ALink,
    "org.texttechnologylab.annotation.link.DALink": DALink,
    "org.texttechnologylab.annotation.link.DLink": DLink,
    "org.texttechnologylab.annotation.link.Link": Link,
    "org.texttechnologylab.annotation.link.OLink": OLink,
}

__all__ = [
    "ADLink",
    "ALink",
    "DALink",
    "DLink",
    "Link",
    "OLink",
    "UIMA_TYPE_TO_CLASS",
]
