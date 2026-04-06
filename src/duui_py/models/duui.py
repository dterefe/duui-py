from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator
from typing import Optional, Any

from duui_py.models.uima import Annotation, SoFa, UimaValue


class FsRec(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: int
    ref: Optional[int] = None
    type: str
    begin: Optional[int] = None
    end: Optional[int] = Field(default=None, alias="end")
    features: dict[str, UimaValue] = Field(default_factory=dict)
    updated_features: list[str] = Field(default_factory=list)


class AnnotationMeta(BaseModel):
    name: str
    version: str
    modelName: Optional[str] = None
    modelVersion: Optional[str] = None


class DocumentModification(BaseModel):
    user: str
    timestamp: int
    comment: str


class DuuiDocument(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)
    view: str = ""
    sofa: SoFa
    fs: list[FsRec] = Field(default_factory=list)

    @property
    def text(self) -> Optional[str]:
        return self.sofa.data if isinstance(self.sofa.data, str) else None

    @property
    def bytes(self) -> Optional[bytes]:
        return self.sofa.data if isinstance(self.sofa.data, (bytes, bytearray)) else None


class FeatureStructureKeyRef(BaseModel):
    key: str


# Simplified to avoid recursion issues in Pydantic
# Original: UimaValue | FeatureStructureKeyRef | list["UimaValueOrKeyRef"]
UimaValueOrKeyRef = Any


class FeatureStructureNode(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    key: str
    ref: Optional[int] = None
    type: str
    begin: Optional[int] = None
    end: Optional[int] = Field(default=None, alias="end")
    features: dict[str, UimaValueOrKeyRef] = Field(default_factory=dict)
    updated_features: list[str] = Field(default_factory=list)

    _ref_locked: bool = PrivateAttr(default=False)

    @model_validator(mode="after")
    def _init_ref_lock(self) -> "FeatureStructureNode":
        if self.ref is not None and self.ref >= 0:
            object.__setattr__(self, "_ref_locked", True)
        return self

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "ref":
            locked = getattr(self, "_ref_locked", False)
            if locked:
                current = getattr(self, "ref", None)
                if value != current:
                    raise TypeError("existing feature structure ref is immutable")
        super().__setattr__(name, value)

    @property
    def is_new(self) -> bool:
        return self.ref is None or self.ref < 0

    @property
    def is_existing(self) -> bool:
        return self.ref is not None and self.ref >= 0

    def mark_updated(self, *feature_names: str) -> None:
        for name in feature_names:
            if name not in self.updated_features:
                self.updated_features.append(name)

    def set_feature(self, name: str, value: UimaValueOrKeyRef) -> None:
        self.features[name] = value
        self.mark_updated(name)

    @classmethod
    def new_with_negative_ref(
        cls,
        *,
        key: str,
        type: str,
        next_negative_ref: int,
        begin: Optional[int] = None,
        end: Optional[int] = None,
        features: Optional[dict[str, UimaValueOrKeyRef]] = None,
    ) -> "FeatureStructureNode":
        if next_negative_ref >= 0:
            raise ValueError("next_negative_ref must be negative")
        return cls(
            key=key,
            ref=next_negative_ref,
            type=type,
            begin=begin,
            end=end,
            features=features or {},
        )


class NegativeRefAllocator:
    """Allocates proprietary temporary refs for newly created FS nodes.

    Values are strictly negative and monotonically decreasing: -1, -2, -3, ...
    """

    def __init__(self, start: int = -1):
        if start >= 0:
            raise ValueError("NegativeRefAllocator start must be negative")
        self._next = start

    def next(self) -> int:
        value = self._next
        self._next -= 1
        return value


class DuuiResult(BaseModel):
    sofa: Optional[SoFa] = None
    annotations: list[Annotation] = Field(default_factory=list)
    feature_structures: list[FeatureStructureNode] = Field(default_factory=list)
    meta: Optional[AnnotationMeta] = None
    modification_meta: Optional[DocumentModification] = None
    errors: list[str] = Field(default_factory=list)
