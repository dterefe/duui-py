"""Auto-generated UIMA models for namespace: texttechnologylab.annotation.domain."""

from __future__ import annotations

from typing import Optional

from duui_py.models.uima import FeatureStructure, UimaValue


class Domain(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.domain.Domain"
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None
    uri: Optional[str] = None


class Association(FeatureStructure):
    type: str = "org.texttechnologylab.annotation.domain.Association"
    id: Optional[str] = None
    metadata: Optional[str] = None
    name: Optional[str] = None


class Membership(Association):
    type: str = "org.texttechnologylab.annotation.domain.Membership"
    order: Optional[int] = None
    part: Optional[UimaValue] = None
    whole: Optional[UimaValue] = None


class Sequence(Association):
    type: str = "org.texttechnologylab.annotation.domain.Sequence"
    next: Optional[UimaValue] = None
    order: Optional[int] = None
    previous: Optional[UimaValue] = None


class Reference(Association):
    type: str = "org.texttechnologylab.annotation.domain.Reference"
    context: Optional[UimaValue] = None
    referent: Optional[UimaValue] = None
    role: Optional[str] = None


class Equivalence(Association):
    type: str = "org.texttechnologylab.annotation.domain.Equivalence"
    basis: Optional[str] = None
    one: Optional[UimaValue] = None
    other: Optional[UimaValue] = None


UIMA_TYPE_TO_CLASS = {
    "org.texttechnologylab.annotation.domain.Domain": Domain,
    "org.texttechnologylab.annotation.domain.Association": Association,
    "org.texttechnologylab.annotation.domain.Membership": Membership,
    "org.texttechnologylab.annotation.domain.Sequence": Sequence,
    "org.texttechnologylab.annotation.domain.Reference": Reference,
    "org.texttechnologylab.annotation.domain.Equivalence": Equivalence,
}

__all__ = [
    "Domain",
    "Association",
    "Membership",
    "Sequence",
    "Reference",
    "Equivalence",
    "UIMA_TYPE_TO_CLASS",
]
