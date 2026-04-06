from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from typing import Any, Generic, TypeVar

from duui_py.codecs.base import Codec
from duui_py.models import AnnotatorConfig, DuuiDocument, DuuiResult, load_annotator_config

RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")


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


class V1Process(ABC):
    @abstractmethod
    async def v1_process(
        self, input_payload: DuuiDocument, parameters: dict[str, Any], result: DuuiResult
    ) -> DuuiResult | None:
        raise NotImplementedError


class V2Process(ABC):
    @abstractmethod
    async def v2_process(self, input_payload: DuuiDocument, parameters: dict[str, Any]) -> AsyncIterable[DuuiResult]:
        """Full-input V2 process: framework provides fully assembled input payload."""
        raise NotImplementedError


class V2ProcessChunks(ABC):
    batch_size: int = 1

    @abstractmethod
    async def v2_process_chunks(
        self, input_chunks: list[DuuiDocument], parameters: dict[str, Any]
    ) -> AsyncIterable[DuuiResult]:
        """Chunked V2 process: framework provides input in batches of full object chunks."""
        raise NotImplementedError
