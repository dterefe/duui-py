from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from functools import lru_cache
from time import time
from typing import Any

import json
import os

from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import unavailable, unprocessable
from duui_py.logging import get_event_logger_or_none
from duui_py.metrics import metrics
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

SPACY_MODELS = {
    "efficiency": {
        "de": "de_core_news_sm",
        "en": "en_core_web_sm",
        "xx": "xx_ent_wiki_sm",
    },
    "accuracy": {
        "de": "de_dep_news_trf",
        "en": "en_core_web_trf",
    },
    "trf": {
        "de": "de_dep_news_trf",
        "en": "en_core_web_trf",
    },
    "sm": {
        "de": "de_core_news_sm",
        "en": "en_core_web_sm",
    },
}

VARIANT_OUTPUTS = {
    "": {"tokenizer", "sentencizer", "lemmatizer", "tagger", "morphologizer", "parser", "ner"},
    "-tokenizer": {"tokenizer"},
    "tokenizer": {"tokenizer"},
    "-sentencizer": {"sentencizer"},
    "sentencizer": {"sentencizer"},
    "sentence": {"sentencizer"},
    "-lemmatizer": {"tokenizer", "lemmatizer"},
    "lemmatizer": {"tokenizer", "lemmatizer"},
    "-tagger": {"tokenizer", "tagger"},
    "tagger": {"tokenizer", "tagger"},
    "-morphologizer": {"tokenizer", "tagger", "morphologizer"},
    "morphologizer": {"tokenizer", "tagger", "morphologizer"},
    "-parser": {"tokenizer", "sentencizer", "parser"},
    "parser": {"tokenizer", "sentencizer", "parser"},
    "-ner": {"tokenizer", "ner"},
    "ner": {"tokenizer", "ner"},
}


def _parse_exclude(value: object | None) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return set()
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            decoded = [item.strip() for item in text.strip("[]").split(",") if item.strip()]
        value = decoded
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip().strip("\"'").lower() for item in value if str(item).strip()}
    return {str(value).strip().lower()}


def _language(doc: V1RequestEnvelope) -> str:
    for key in ("spacy_language", "language", "lang"):
        value = doc.parameters.get(key)
        if value:
            return str(value)
    return getattr(doc.sofa, "language", None) or os.environ.get("SPACY_MODEL_LANG", "de")


def _model_name(doc: V1RequestEnvelope) -> str:
    for key in ("model_name", "spacy_model", "single_model"):
        value = doc.parameters.get(key)
        if value:
            return str(value)
    env_model = os.environ.get("SPACY_MODEL_NAME") or os.environ.get("TEXTIMAGER_SPACY_SINGLE_MODEL")
    if env_model:
        return env_model

    language = _language(doc)
    variant = str(doc.parameters.get("model_variant") or doc.parameters.get("spacy_model_size") or "efficiency")
    if variant not in SPACY_MODELS:
        unprocessable("Unsupported spaCy model variant.", variant=variant, supported=sorted(SPACY_MODELS))
    if language not in SPACY_MODELS[variant]:
        if "xx" in SPACY_MODELS[variant]:
            language = "xx"
        else:
            unprocessable("Unsupported spaCy language for variant.", language=language, variant=variant)
    return SPACY_MODELS[variant][language]


def _outputs(parameters: dict[str, object]) -> set[str]:
    variant = str(parameters.get("variant") or os.environ.get("TEXTIMAGER_SPACY_VARIANT") or "")
    outputs = set(VARIANT_OUTPUTS.get(variant, VARIANT_OUTPUTS[""]))
    outputs.difference_update(_parse_exclude(parameters.get("exclude")))
    return outputs


@lru_cache(maxsize=4)
def _load_spacy(model_name: str, exclude: tuple[str, ...]) -> Any:
    try:
        import spacy
    except Exception as exc:  # noqa: BLE001
        unavailable("spaCy is not installed in this runtime.", exception=type(exc).__name__)
    try:
        return spacy.load(model_name, exclude=list(exclude))
    except Exception as exc:  # noqa: BLE001
        unavailable("spaCy model could not be loaded.", model=model_name, exception=type(exc).__name__, detail=str(exc))


def _annotations(text: str, model_name: str, exclude: set[str], outputs: set[str]) -> tuple[list[Annotation], str, str]:
    nlp = _load_spacy(model_name, tuple(sorted(exclude)))
    spacy_doc = nlp(text)
    model_meta = getattr(nlp, "meta", {}) or {}
    annotations: list[Annotation] = []

    token_refs: dict[int, dict[str, int]] = {}
    if "tokenizer" in outputs:
        for order, token in enumerate(spacy_doc):
            if token.is_space:
                continue
            annotation = Token(begin=token.idx, end=token.idx + len(token), order=order)
            annotations.append(annotation)
            token_refs[token.i] = {"begin": token.idx, "end": token.idx + len(token)}

    if "lemmatizer" in outputs:
        for token in spacy_doc:
            if token.is_space:
                continue
            annotations.append(Lemma(begin=token.idx, end=token.idx + len(token), value=token.lemma_ or token.text))

    if "tagger" in outputs:
        for token in spacy_doc:
            if token.is_space:
                continue
            annotations.append(POS(begin=token.idx, end=token.idx + len(token), PosValue=token.tag_, coarseValue=token.pos_))

    if "morphologizer" in outputs:
        for token in spacy_doc:
            if token.is_space:
                continue
            annotations.append(MorphologicalFeatures(begin=token.idx, end=token.idx + len(token), value=str(token.morph)))

    if "sentencizer" in outputs:
        for sentence in spacy_doc.sents:
            annotations.append(Sentence(begin=sentence.start_char, end=sentence.end_char))

    if "ner" in outputs:
        for entity in spacy_doc.ents:
            annotations.append(NamedEntity(begin=entity.start_char, end=entity.end_char, value=entity.label_))

    if "parser" in outputs:
        for token in spacy_doc:
            if token.is_space:
                continue
            dependent = token_refs.get(token.i, {"begin": token.idx, "end": token.idx + len(token)})
            governor = token_refs.get(token.head.i, {"begin": token.head.idx, "end": token.head.idx + len(token.head)})
            annotations.append(
                Dependency(
                    begin=token.idx,
                    end=token.idx + len(token),
                    DependencyType=token.dep_,
                    Dependent=dependent,
                    Governor=governor,
                    flavor="basic",
                )
            )

    return annotations, str(model_meta.get("version", "runtime")), str(model_meta.get("lang", "x-unspecified"))


class SpacyAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "TTLab-UIMA/textimager-uima-spacy migration"}),
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
                "description": "Exact spaCy model package name.",
                "default": "de_core_news_sm",
            },
            "model_variant": {
                "type": "string",
                "description": "Legacy variant alias: efficiency, accuracy/trf, sm.",
                "default": "efficiency",
            },
            "spacy_language": {
                "type": "string",
                "description": "Legacy language hint used when model_name is not set.",
                "default": "de",
            },
            "exclude": {
                "type": "array",
                "description": "spaCy pipeline components or output groups to skip.",
            },
            "variant": {
                "type": "string",
                "description": "Legacy image variant such as -tokenizer, -ner, -parser.",
                "default": "",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        model_name = _model_name(doc)
        exclude = _parse_exclude(doc.parameters.get("exclude"))
        outputs = _outputs(doc.parameters)
        logger = get_event_logger_or_none()

        if logger is not None:
            await logger.info(
                "spaCy processing started",
                extra={"model": model_name, "exclude": sorted(exclude), "outputs": sorted(outputs), "text_length": len(text)},
            )

        annotations, model_version, model_lang = _annotations(text, model_name, exclude, outputs)
        counts: dict[str, int] = {}
        for annotation in annotations:
            counts[annotation.type] = counts.get(annotation.type, 0) + 1
            yield annotation

        elapsed_ms = int((time() - started) * 1000)
        await metrics.count("spacy_annotations", len(annotations), model=model_name)
        for annotation_type, count in counts.items():
            await metrics.count("spacy_annotations_by_type", count, type=annotation_type)
        await metrics.timing("spacy_processing_ms", elapsed_ms)

        if logger is not None:
            await logger.info(
                "spaCy processing completed",
                extra={"model": model_name, "annotations": len(annotations), "elapsed_ms": elapsed_ms},
            )

        yield AnnotatorMetaData(
            name=self.config.descriptor.name,
            version=self.config.descriptor.version,
            modelName=model_name,
            modelVersion=model_version,
            spacyVersion=_spacy_version(),
            modelLang=model_lang,
        )
        yield DocumentModification(
            user=self.config.descriptor.name,
            timestamp=int(time()),
            comment=f"{self.config.descriptor.name} spaCy model={model_name}",
        )


def _spacy_version() -> str | None:
    try:
        import spacy
    except Exception:
        return None
    return str(spacy.__version__)


app = create_app(SpacyAnnotator, request_adapter=AsyncChunkedRequestAdapter())
