from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import re
from functools import lru_cache
from time import time
from typing import Any

from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.logging import get_event_logger_or_none, log_errors
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    AnnotatorMetaData,
    DocumentModification,
    Domain,
    DomainSpec,
    IODescriptor,
    V1RequestEnvelope,
)
from duui_py.models.uima import Annotation, sofa_text_value
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.types import (
    MorphologicalFeatures,
)
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.types import POS
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.ner.type.types import NamedEntity
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.types import (
    Lemma,
    Sentence,
    Token,
)
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.types import Dependency

TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
SENTENCE_PATTERN = re.compile(r"[^.!?\n]+[.!?]?", re.UNICODE)


class SpacyAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"spacy_version": "optional"}),
        descriptor=AnnotatorDescriptor(
            name="spacy-lua-msgpack",
            version="1.0.0",
            input=IODescriptor(
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                )
            ),
            output=IODescriptor(
                types={
                    "Sentence": ["de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"],
                    "Token": ["de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"],
                    "Lemma": ["de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma"],
                    "POS": ["de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"],
                    "MorphologicalFeatures": [
                        "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.MorphologicalFeatures"
                    ],
                    "Dependency": ["de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency"],
                    "NamedEntity": ["de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"],
                },
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemSpacy.xml",
        parameters_schema={
            "model_name": {
                "type": "string",
                "description": "Name of the spaCy model to use when spaCy is installed.",
                "default": "en_core_web_sm",
            },
            "use_existing_tokens": {
                "type": "boolean",
                "description": "Use existing tokens from CAS.",
                "default": False,
            },
            "use_existing_sentences": {
                "type": "boolean",
                "description": "Use existing sentences from CAS.",
                "default": False,
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @log_errors(recovery_suggestion="Check sofa text, spaCy model availability, and model_name parameter.")
    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        logger = get_event_logger_or_none()
        text = sofa_text_value(doc.sofa) or ""
        model_name = str(doc.parameters.get("model_name") or "en_core_web_sm")
        if logger:
            await logger.info(
                "spaCy processing started",
                {"characters": len(text), "requested_model": model_name},
            )
            await logger.debug("spaCy parameters resolved", {"parameters": dict(doc.parameters)})

        generated, model_version = self._try_spacy(text, model_name)
        engine = "spacy"
        if generated is None:
            generated = self._heuristic_annotations(text)
            model_name = "heuristic-tokenizer"
            model_version = "1"
            engine = "heuristic"

        counts: dict[str, int] = {}
        total = 0
        for annotation in generated:
            total += 1
            counts[annotation.type] = counts.get(annotation.type, 0) + 1
            yield annotation

        elapsed_ms = int((time() - started) * 1000)
        if logger:
            await logger.metric("processing", "spacy_annotations", total, "count", elapsed_ms)
            await logger.info(
                "spaCy processing completed",
                {
                    "engine": engine,
                    "model": model_name,
                    "annotations": total,
                    "annotation_types": counts,
                    "elapsed_ms": elapsed_ms,
                },
            )

        yield AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName=model_name,
                modelVersion=model_version,
        )
        yield DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} tokenization and lightweight NLP annotations",
        )

    @staticmethod
    def _heuristic_annotations(text: str) -> Iterator[Annotation]:
        tokens: list[Token] = []

        for i, match in enumerate(TOKEN_PATTERN.finditer(text)):
            token_text = match.group(0)
            token = Token(begin=match.start(), end=match.end(), order=i)
            tokens.append(token)
            yield token
            yield Lemma(begin=match.start(), end=match.end(), value=token_text.lower())
            yield (
                POS(
                    begin=match.start(),
                    end=match.end(),
                    PosValue="PUNCT" if re.fullmatch(r"[^\w\s]", token_text) else "X",
                    coarseValue="PUNCT" if re.fullmatch(r"[^\w\s]", token_text) else "X",
                )
            )
            yield MorphologicalFeatures(begin=match.start(), end=match.end(), value="")

            if token_text[:1].isupper() and token_text.isalpha():
                yield NamedEntity(begin=match.start(), end=match.end(), value="MISC")

        for match in SENTENCE_PATTERN.finditer(text):
            sentence = match.group(0)
            begin = match.start() + len(sentence) - len(sentence.lstrip())
            end = match.end() - (len(sentence) - len(sentence.rstrip()))
            if begin < end:
                yield Sentence(begin=begin, end=end)

        for left, right in zip(tokens, tokens[1:]):
            yield (
                Dependency(
                    begin=right.begin,
                    end=right.end,
                    DependencyType="dep",
                    Dependent={"begin": right.begin, "end": right.end},
                    Governor={"begin": left.begin, "end": left.end},
                    flavor="basic",
                )
            )

    @staticmethod
    @lru_cache(maxsize=2)
    def _load_spacy(model_name: str) -> Any:
        import spacy

        try:
            return spacy.load(model_name)
        except Exception:
            nlp = spacy.blank("en")
            nlp.add_pipe("sentencizer")
            return nlp

    def _try_spacy(self, text: str, model_name: str) -> tuple[Iterator[Annotation], str] | tuple[None, None]:
        try:
            nlp = self._load_spacy(model_name)
        except Exception:
            return None, None

        spacy_doc = nlp(text)

        def iter_annotations() -> Iterator[Annotation]:
            for i, token in enumerate(spacy_doc):
                if token.is_space:
                    continue
                yield Token(begin=token.idx, end=token.idx + len(token), order=i)
                yield Lemma(begin=token.idx, end=token.idx + len(token), value=token.lemma_ or token.text.lower())
                yield POS(begin=token.idx, end=token.idx + len(token), PosValue=token.tag_, coarseValue=token.pos_)
                yield MorphologicalFeatures(begin=token.idx, end=token.idx + len(token), value=str(token.morph))

            for sent in spacy_doc.sents:
                yield Sentence(begin=sent.start_char, end=sent.end_char)

            for ent in spacy_doc.ents:
                yield NamedEntity(begin=ent.start_char, end=ent.end_char, value=ent.label_)

            token_by_i = {token.i: token for token in spacy_doc if not token.is_space}
            for token in spacy_doc:
                if token.is_space or token.head.i not in token_by_i:
                    continue
                yield Dependency(
                        begin=token.idx,
                        end=token.idx + len(token),
                        DependencyType=token.dep_,
                        Dependent={"begin": token.idx, "end": token.idx + len(token)},
                        Governor={"begin": token.head.idx, "end": token.head.idx + len(token.head)},
                        flavor="basic",
                )

        return iter_annotations(), str(getattr(nlp, "meta", {}).get("version", "runtime"))


app = create_app(SpacyAnnotator, request_adapter=AsyncChunkedRequestAdapter())
