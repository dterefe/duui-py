from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from duui_py.codecs.base import Codec
from duui_py.models import AnnotatorConfig, DuuiResult, load_annotator_config
from duui_py.models.uima import FeatureStructure
from duui_py.models.uima import SoFaBytes, SoFaText, SoFaURI, SoFaAnnotationSpans

RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")
PayloadT = TypeVar("PayloadT", bound="V1Payload")
ResultT = TypeVar("ResultT", bound=DuuiResult)


class V1Payload(BaseModel):
    view: str = ""
    feature_structures: dict[str, list[FeatureStructure]] = Field(default_factory=dict)


class _ConfigBackedAnnotator(ABC):
    config: AnnotatorConfig
    config_path: str | None = None

    def __init__(self, config_path: str | None = None, config: AnnotatorConfig | None = None):
        if config is not None:
            self.config = config
            return

        effective_path = config_path or self.__class__.config_path
        if effective_path:
            self.config = load_annotator_config(effective_path)
            return

        self.config = self.__class__.config


class DuuiAnnotator(_ConfigBackedAnnotator, Generic[RequestT, ResponseT], ABC):
    @abstractmethod
    def codec(self) -> Codec[RequestT, ResponseT]:
        raise NotImplementedError

    @abstractmethod
    async def process(self, doc: RequestT) -> ResponseT:
        raise NotImplementedError


class DUUIProcess(Generic[PayloadT, ResultT], ABC):
    payload_model: type[V1Payload] = V1Payload


class V1Process(DUUIProcess[PayloadT, ResultT], ABC):
    async def process_text(
        self, sofa: SoFaText, payload: PayloadT, parameters: dict[str, Any]
    ) -> ResultT | None:
        raise NotImplementedError("process_text not implemented")

    async def process_bytes(
        self, sofa: SoFaBytes, payload: PayloadT, parameters: dict[str, Any]
    ) -> ResultT | None:
        raise NotImplementedError("process_bytes not implemented")

    async def process_uri(
        self, sofa: SoFaURI, payload: PayloadT, parameters: dict[str, Any]
    ) -> ResultT | None:
        raise NotImplementedError("process_uri not implemented")

    async def process_spans(
        self, sofa: SoFaAnnotationSpans, payload: PayloadT, parameters: dict[str, Any]
    ) -> ResultT | None:
        raise NotImplementedError("process_spans not implemented")


class V1AsyncProcess(V1Process[PayloadT, DuuiResult], ABC):
    async def process_text(
        self, sofa: SoFaText, payload: PayloadT, parameters: dict[str, Any]
    ) -> AsyncIterable[DuuiResult]:
        raise NotImplementedError("process_text not implemented")

    async def process_bytes(
        self, sofa: SoFaBytes, payload: PayloadT, parameters: dict[str, Any]
    ) -> AsyncIterable[DuuiResult]:
        raise NotImplementedError("process_bytes not implemented")

    async def process_uri(
        self, sofa: SoFaURI, payload: PayloadT, parameters: dict[str, Any]
    ) -> AsyncIterable[DuuiResult]:
        raise NotImplementedError("process_uri not implemented")

    async def process_spans(
        self, sofa: SoFaAnnotationSpans, payload: PayloadT, parameters: dict[str, Any]
    ) -> AsyncIterable[DuuiResult]:
        raise NotImplementedError("process_spans not implemented")
