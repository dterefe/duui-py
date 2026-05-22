from __future__ import annotations

from functools import lru_cache
from time import time
from typing import Any

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.lua_custom import LuaCustomCodec
from duui_py.errors import unavailable, unprocessable
from duui_py.logging import get_event_logger_or_none
from duui_py.metrics import metrics
from duui_py.models import AnnotatorConfig, AnnotatorDescriptor, AnnotatorMeta, Domain, DomainSpec, IODescriptor


UIMA_TYPE_SENTENCE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
UIMA_TYPE_TOKEN = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"
UIMA_TYPE_LEMMA = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma"
UIMA_TYPE_POS = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"
UIMA_TYPE_MORPH = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.MorphologicalFeatures"
UIMA_TYPE_DEPENDENCY = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency"
UIMA_TYPE_NAMED_ENTITY = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"

VARIANT_OUTPUTS = {
    "": {UIMA_TYPE_SENTENCE, UIMA_TYPE_TOKEN, UIMA_TYPE_LEMMA, UIMA_TYPE_POS, UIMA_TYPE_MORPH, UIMA_TYPE_DEPENDENCY, UIMA_TYPE_NAMED_ENTITY},
    "-tokenizer": {UIMA_TYPE_TOKEN},
    "-sentencizer": {UIMA_TYPE_SENTENCE},
    "-lemmatizer": {UIMA_TYPE_LEMMA},
    "-tagger": {UIMA_TYPE_POS},
    "-ner": {UIMA_TYPE_NAMED_ENTITY},
    "-parser": {UIMA_TYPE_DEPENDENCY},
    "-morphologizer": {UIMA_TYPE_MORPH},
}

SPACY_MODELS = {
    "efficiency": {"de": "de_core_news_sm", "en": "en_core_web_sm", "xx": "xx_ent_wiki_sm"},
    "accuracy": {"de": "de_dep_news_trf", "en": "en_core_web_trf"},
    "trf": {"de": "de_dep_news_trf", "en": "en_core_web_trf"},
    "sm": {"de": "de_core_news_sm", "en": "en_core_web_sm"},
}

MORPH_KEYS = {
    "Gender": "gender",
    "Number": "number",
    "Case": "case",
    "Degree": "degree",
    "VerbForm": "verbForm",
    "Tense": "tense",
    "Mood": "mood",
    "Voice": "voice",
    "Definite": "definiteness",
    "Person": "person",
    "Aspect": "aspect",
    "Animacy": "animacy",
    "Polarity": "negative",
    "NumType": "numType",
    "Poss": "possessive",
    "PronType": "pronType",
    "Reflex": "reflex",
    "VerbType": "transitivity",
}


class TextImagerRequest(BaseModel):
    text: str = ""
    tokens: list[str] | None = None
    spaces: list[bool] | None = None
    lang: str = "x-unspecified"
    parameters: dict[str, Any] = Field(default_factory=dict)


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _parse_exclude(value: object | None) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return set()
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            value = [item.strip() for item in text.strip("[]").split(",") if item.strip()]
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip().strip("\"'") for item in value if str(item).strip()}
    return {str(value).strip()}


def _model_name(doc: TextImagerRequest) -> str:
    params = doc.parameters
    for key in ("model_name", "spacy_model", "single_model"):
        value = params.get(key)
        if value:
            return str(value)
    env_model = _env("TEXTIMAGER_SPACY_SINGLE_MODEL") or _env("SPACY_MODEL_NAME")
    if env_model:
        return env_model
    lang = str(params.get("spacy_language") or params.get("language") or doc.lang or _env("TEXTIMAGER_SPACY_SINGLE_MODEL_LANG", "de"))
    if lang == "x-unspecified":
        lang = "xx"
    variant = str(params.get("model_variant") or params.get("spacy_model_size") or "efficiency")
    if variant not in SPACY_MODELS:
        unprocessable("Unsupported spaCy model variant.", variant=variant)
    if lang not in SPACY_MODELS[variant]:
        lang = "xx" if "xx" in SPACY_MODELS[variant] else lang
    if lang not in SPACY_MODELS[variant]:
        unprocessable("Unsupported spaCy language for variant.", language=lang, variant=variant)
    return SPACY_MODELS[variant][lang]


def _write_types(parameters: dict[str, Any]) -> set[str]:
    configured = parameters.get("write_types")
    variant = str(parameters.get("variant") or _env("TEXTIMAGER_SPACY_VARIANT") or "")
    base = set(VARIANT_OUTPUTS.get(variant, VARIANT_OUTPUTS[""]))
    if isinstance(configured, str):
        try:
            configured = json.loads(configured)
        except json.JSONDecodeError:
            configured = [item.strip() for item in configured.split(",") if item.strip()]
    if isinstance(configured, (list, tuple, set)) and configured:
        base.intersection_update({str(item) for item in configured})
    for excluded in _parse_exclude(parameters.get("exclude")):
        if excluded in {"tagger", "pos"}:
            base.discard(UIMA_TYPE_POS)
        elif excluded in {"parser", "dependency"}:
            base.discard(UIMA_TYPE_DEPENDENCY)
        elif excluded in {"ner", "entity"}:
            base.discard(UIMA_TYPE_NAMED_ENTITY)
        elif excluded in {"lemmatizer", "lemma"}:
            base.discard(UIMA_TYPE_LEMMA)
        elif excluded in {"morphologizer", "morph"}:
            base.discard(UIMA_TYPE_MORPH)
        elif excluded in {"sentencizer", "sentence"}:
            base.discard(UIMA_TYPE_SENTENCE)
        elif excluded in {"tokenizer", "token"}:
            base.discard(UIMA_TYPE_TOKEN)
    return base


@lru_cache(maxsize=4)
def _load_spacy(model_name: str, exclude: tuple[str, ...]):
    try:
        import spacy
    except Exception as exc:  # noqa: BLE001
        unavailable("spaCy is not installed in this runtime.", exception=type(exc).__name__)
    try:
        return spacy.load(model_name, exclude=list(exclude))
    except Exception as exc:  # noqa: BLE001
        unavailable("spaCy model could not be loaded.", model=model_name, exception=type(exc).__name__, detail=str(exc))


def _morph_details(token: Any) -> dict[str, object]:
    raw = token.morph.to_dict()
    return {legacy_key: raw[source_key] for source_key, legacy_key in MORPH_KEYS.items() if source_key in raw}


def _make_doc(nlp: Any, doc: TextImagerRequest) -> tuple[Any, bool]:
    is_pretokenized = bool(doc.tokens and doc.spaces and len(doc.tokens) == len(doc.spaces))
    if not is_pretokenized:
        return nlp(doc.text), False
    from spacy.tokens import Doc

    return nlp(Doc(nlp.vocab, words=doc.tokens or [], spaces=doc.spaces or [])), True


class SpacyLegacyAnnotator(DuuiAnnotator[TextImagerRequest, dict[str, object]]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "TTLab-UIMA/textimager-uima-spacy legacy Lua migration"}),
        descriptor=AnnotatorDescriptor(
            name="spacy-legacy-lua",
            version="0.1.4",
            input=IODescriptor(text=DomainSpec(default=Domain(mimeType="application/json", languages=["x-unspecified"]))),
            output=IODescriptor(
                types={
                    "Sentence": [UIMA_TYPE_SENTENCE],
                    "Token": [UIMA_TYPE_TOKEN],
                    "Lemma": [UIMA_TYPE_LEMMA],
                    "POS": [UIMA_TYPE_POS],
                    "MorphologicalFeatures": [UIMA_TYPE_MORPH],
                    "Dependency": [UIMA_TYPE_DEPENDENCY],
                    "NamedEntity": [UIMA_TYPE_NAMED_ENTITY],
                },
                text=DomainSpec(default=Domain(mimeType="application/json", languages=["x-unspecified"])),
            ),
        ),
        typesystem_xml_path="TypeSystemSpacyLegacy.xml",
        parameters_schema={},
    )

    def codec(self):
        return LuaCustomCodec(
            (Path(__file__).resolve().parent / "communication.lua").read_text(encoding="utf-8"),
            request_media_type="application/json",
            response_media_type="application/json",
            decode_request=lambda body: TextImagerRequest.model_validate_json(body),
            encode_response=lambda result: json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            name="spacy-legacy-lua",
        )

    async def process(self, doc: TextImagerRequest) -> dict[str, object]:
        started = time()
        model_name = _model_name(doc)
        write_types = _write_types(doc.parameters)
        exclude = tuple(sorted(_parse_exclude(doc.parameters.get("exclude"))))
        nlp = _load_spacy(model_name, exclude)
        logger = get_event_logger_or_none()
        if logger is not None:
            await logger.info("spaCy legacy processing started", extra={"model": model_name, "write_types": sorted(write_types)})

        spacy_doc, is_pretokenized = _make_doc(nlp, doc)
        meta = getattr(nlp, "meta", {}) or {}
        sentences: list[dict[str, object]] = []
        tokens: list[dict[str, object]] = []
        dependencies: list[dict[str, object]] = []
        entities: list[dict[str, object]] = []

        if UIMA_TYPE_SENTENCE in write_types:
            for sent in spacy_doc.sents:
                sentences.append({"begin": sent.start_char, "end": sent.end_char, "write_sentence": True})

        for token in spacy_doc:
            if token.is_space:
                continue
            token_data = {
                "begin": token.idx,
                "end": token.idx + len(token),
                "ind": token.i,
                "write_token": UIMA_TYPE_TOKEN in write_types and not is_pretokenized,
                "lemma": token.lemma_ or token.text,
                "write_lemma": UIMA_TYPE_LEMMA in write_types,
                "pos": token.tag_,
                "pos_coarse": token.pos_,
                "write_pos": UIMA_TYPE_POS in write_types,
                "morph": str(token.morph),
                "morph_details": _morph_details(token),
                "write_morph": UIMA_TYPE_MORPH in write_types,
                "parent_ind": token.head.i,
                "write_dep": UIMA_TYPE_DEPENDENCY in write_types,
            }
            tokens.append(token_data)

            if UIMA_TYPE_DEPENDENCY in write_types:
                dependencies.append(
                    {
                        "begin": token.idx,
                        "end": token.idx + len(token),
                        "type": token.dep_,
                        "flavor": "basic",
                        "dependent_ind": token.i,
                        "governor_ind": token.head.i,
                        "write_dep": True,
                    }
                )

        if UIMA_TYPE_NAMED_ENTITY in write_types:
            for ent in spacy_doc.ents:
                entities.append({"begin": ent.start_char, "end": ent.end_char, "value": ent.label_, "write_entity": True})

        elapsed_ms = int((time() - started) * 1000)
        await metrics.count("spacy_legacy_annotations", len(sentences) + len(tokens) + len(dependencies) + len(entities), model=model_name)
        await metrics.timing("spacy_legacy_processing_ms", elapsed_ms)
        if logger is not None:
            await logger.info(
                "spaCy legacy processing completed",
                extra={"tokens": len(tokens), "sentences": len(sentences), "dependencies": len(dependencies), "entities": len(entities), "elapsed_ms": elapsed_ms},
            )

        name = _env("TEXTIMAGER_SPACY_ANNOTATOR_NAME", "textimager-duui-spacy")
        version = _env("TEXTIMAGER_SPACY_ANNOTATOR_VERSION", "0.1.4")
        try:
            import spacy

            spacy_version = str(spacy.__version__)
        except Exception:
            spacy_version = ""
        return {
            "sentences": sentences,
            "tokens": tokens,
            "dependencies": dependencies,
            "entities": entities,
            "meta": {
                "name": name,
                "version": version,
                "modelName": str(meta.get("name", model_name)),
                "modelVersion": str(meta.get("version", "runtime")),
                "spacyVersion": spacy_version,
                "modelLang": str(meta.get("lang", doc.lang)),
                "modelSpacyVersion": str(meta.get("spacy_version", "")),
                "modelSpacyGitVersion": str(meta.get("spacy_git_version", "")),
            },
            "modification_meta": {
                "user": name,
                "timestamp": int(time()),
                "comment": f"{name} ({version}), spaCy ({spacy_version}), {meta.get('lang', doc.lang)} {meta.get('name', model_name)} ({meta.get('version', 'runtime')})",
            },
            "is_pretokenized": is_pretokenized,
        }


app = create_app(SpacyLegacyAnnotator)
