from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from duui_py.codecs.base import Codec
from duui_py.models import AnnotatorConfig, load_annotator_config

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
