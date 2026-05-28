from __future__ import annotations

import asyncio
import json
from collections import OrderedDict
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from functools import lru_cache
from time import time
from threading import Lock, local
from typing import Any

from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import bad_gateway, unavailable, unprocessable
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    AnnotatorMetaData,
    DocumentModification,
    Domain,
    DomainSpec,
    DuuiResult,
    IODescriptor,
    V1RequestEnvelope,
)
from duui_py.models.uima import FeatureStructure, sofa_text_value
from duui_py.models.uima_typesystem.texttechnologylab.annotation.types import (
    AnnotationComment,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.type.types import Taxon
from duui_py.telemetry import telemetry

TAXON_TYPE = "org.texttechnologylab.annotation.type.Taxon"
ANNOTATION_COMMENT_TYPE = "org.texttechnologylab.annotation.AnnotationComment"
SENTENCE_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
PARAGRAPH_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Paragraph"
DIV_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Div"
HUCOMPUTE_DIV_TYPE = "org.hucompute.textimager.uima.type.segmentation.Div"
SECTION_TYPE = "org.texttechnologylab.annotation.paper.Section"
TITLE_TYPE = "org.texttechnologylab.annotation.paper.Title"
OCR_PARAGRAPH_TYPE = "org.texttechnologylab.annotation.ocr.OCRParagraph"
ABBYY_PARAGRAPH_TYPE = "org.texttechnologylab.annotation.ocr.abbyy.Paragraph"

TAXONERD_MODELS = {
    "biobert": "en_ner_eco_biobert",
    "biobert_weak": "en_ner_eco_biobert_weak",
    "md": "en_ner_eco_md",
    "md_weak": "en_ner_eco_md_weak",
    "en_ner_eco_biobert": "en_ner_eco_biobert",
    "en_ner_eco_biobert_weak": "en_ner_eco_biobert_weak",
    "en_ner_eco_md": "en_ner_eco_md",
    "en_ner_eco_md_weak": "en_ner_eco_md_weak",
}
TAXONERD_LINKERS = {
    "gbif": "gbif_backbone",
    "gbif_backbone": "gbif_backbone",
    "fuseki": "gbif_fuseki",
    "gbif_fuseki": "gbif_fuseki",
    "biofid_fuseki": "gbif_fuseki",
    "sparql": "gbif_fuseki",
    "taxref": "taxref",
    "ncbi": "ncbi_taxonomy",
    "ncbi_taxonomy": "ncbi_taxonomy",
    "ncbi_lite": "ncbi_taxonomy_lite",
    "ncbi_taxonomy_lite": "ncbi_taxonomy_lite",
    "none": None,
    "": None,
}
STRATEGY_ALIASES = {
    "whole": "whole-document",
    "whole-document": "whole-document",
    "document": "whole-document",
    "legacy": "legacy-procedure",
    "legacy-parity": "legacy-procedure",
    "legacy-procedure": "legacy-procedure",
    "whole-document-legacy": "legacy-procedure",
    "whole-document-legacy-procedure": "legacy-procedure",
    "legacy-compatible": "legacy-compatible",
    "legacy-compatible-linker": "legacy-compatible",
    "whole-document-legacy-compatible": "legacy-compatible",
    "whole-document-legacy-linker": "legacy-compatible",
    "span": "span-window",
    "span-window": "span-window",
    "window": "span-window",
}
LINKER_STRATEGY_ALIASES = {
    "optimized": "exact-first-batched",
    "batched": "exact-first-batched",
    "exact-first": "exact-first-batched",
    "exact-first-batched": "exact-first-batched",
    "current": "exact-first-original",
    "original": "exact-first-original",
    "exact-first-original": "exact-first-original",
    "ann": "ann-batched",
    "ann-batched": "ann-batched",
    "ann-original": "ann-original",
    "exact-only": "exact-only",
}
SPAN_TYPE_ALIASES = {
    "sentence": SENTENCE_TYPE,
    "sentences": SENTENCE_TYPE,
    "paragraph": PARAGRAPH_TYPE,
    "paragraphs": PARAGRAPH_TYPE,
    "div": DIV_TYPE,
    "dkpro-div": DIV_TYPE,
    "hucompute-div": HUCOMPUTE_DIV_TYPE,
    "section": SECTION_TYPE,
    "sections": SECTION_TYPE,
    "title": TITLE_TYPE,
    "titles": TITLE_TYPE,
    "ocr-paragraph": OCR_PARAGRAPH_TYPE,
    "ocr_paragraph": OCR_PARAGRAPH_TYPE,
    "abbyy-paragraph": ABBYY_PARAGRAPH_TYPE,
    "abbyy_paragraph": ABBYY_PARAGRAPH_TYPE,
}
DEFAULT_SPAN_PRIORITY = (
    SENTENCE_TYPE,
    PARAGRAPH_TYPE,
    DIV_TYPE,
    HUCOMPUTE_DIV_TYPE,
    SECTION_TYPE,
    TITLE_TYPE,
    OCR_PARAGRAPH_TYPE,
    ABBYY_PARAGRAPH_TYPE,
)
LINK_ID_FEATURE = "_taxonerd_link_id"
LINK_VALUE_FEATURE = "_taxonerd_link_value"
LINK_SCORE_FEATURE = "_taxonerd_link_score"
NER_LABEL_FEATURE = "_taxonerd_ner_label"
DEFAULT_SPARQL_ENDPOINT = "http://host.containers.internal:8098/biofid-search/sparql"
LINK_CACHE_MAX = 20000
_LINK_CACHE: OrderedDict[tuple[object, ...], list[dict[str, object]]] = OrderedDict()
_LINK_CACHE_LOCK = Lock()
_CANDIDATE_GENERATOR_LOCK = Lock()
_LINKER_BACKEND_STATS = local()


@dataclass(frozen=True)
class TextWindow:
    begin: int
    end: int
    text: str
    source_type: str


@dataclass(frozen=True)
class Mention:
    begin: int
    end: int
    text: str
    source_type: str
    label: str | None
    link_text: str | None = None


@dataclass(frozen=True)
class StrategyResult:
    taxons: list[Taxon]
    windows: int = 0
    mentions: int = 0
    metrics: dict[str, float] = field(default_factory=dict)


def _model_name(value: object | None) -> str:
    configured = str(value or "en_ner_eco_md")
    return TAXONERD_MODELS.get(configured, configured)


def _linker_name(value: object | None) -> str | None:
    configured = str(
        value
        if value is not None
        else "gbif_backbone"
    )
    if configured not in TAXONERD_LINKERS:
        unprocessable(
            "Unsupported TaxoNERD linker.",
            linker=configured,
            supported=sorted(TAXONERD_LINKERS),
        )
    return TAXONERD_LINKERS[configured]


def _strategy(value: object | None) -> str:
    configured = str(value or "whole-document").strip().lower().replace("_", "-")
    strategy = STRATEGY_ALIASES.get(configured)
    if strategy is None:
        unprocessable(
            "Unsupported TaxoNERD input strategy.",
            strategy=configured,
            supported=sorted(set(STRATEGY_ALIASES.values())),
        )
    return strategy


def _linker_strategy(value: object | None) -> str:
    configured = str(value or "exact-first-batched").strip().lower().replace("_", "-")
    strategy = LINKER_STRATEGY_ALIASES.get(configured)
    if strategy is None:
        unprocessable(
            "Unsupported TaxoNERD linker strategy.",
            strategy=configured,
            supported=sorted(set(LINKER_STRATEGY_ALIASES.values())),
        )
    return strategy


def _bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _int(value: object, default: int, minimum: int = 1) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, parsed)


def _float(value: object, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _string(value: object | None, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _emit_telemetry(coro: object) -> None:
    try:
        asyncio.create_task(coro)  # type: ignore[arg-type]
    except RuntimeError:
        return


def _csv(value: object | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default
    if isinstance(value, str):
        raw = [item.strip() for item in value.split(",")]
    elif isinstance(value, (list, tuple, set)):
        raw = [str(item).strip() for item in value]
    else:
        raw = [str(value).strip()]
    return tuple(item for item in raw if item) or default


def _aliased_types(
    value: object | None,
    default: tuple[str, ...],
    aliases: dict[str, str],
) -> tuple[str, ...]:
    out: list[str] = []
    for item in _csv(value, default):
        key = item.lower().replace("_", "-")
        out.append(aliases.get(key, item))
    return tuple(dict.fromkeys(out))


def _exclude(value: object | None) -> tuple[str, ...]:
    if value is None:
        return (
            "tagger",
            "parser",
            "taxo_abbrev_detector",
            "taxon_linker",
            "pysbd_sentencizer",
        )
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value)
    text = str(value).strip()
    if not text or text == "[]":
        return ()
    return tuple(
        item.strip().strip("'\"")
        for item in text.strip("[]").split(",")
        if item.strip()
    )


def _offsets(value: object, text: str, mention: str) -> tuple[int, int] | None:
    if isinstance(value, str):
        ints = []
        for part in value.split():
            try:
                ints.append(int(part))
            except ValueError:
                continue
        if len(ints) >= 2:
            return (ints[-2], ints[-1])
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return (int(value[0]), int(value[1]))
        except (TypeError, ValueError):
            pass
    if mention:
        begin = text.find(mention)
        if begin >= 0:
            return (begin, begin + len(mention))
    return None


def _links(entity: object) -> list[dict[str, object]]:
    if entity is None:
        return []
    values = entity if isinstance(entity, list) else [entity]
    links = []
    for value in values:
        if isinstance(value, dict):
            links.append(value)
            continue
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            item: dict[str, object] = {"id": str(value[0]), "value": str(value[1])}
            if len(value) >= 3:
                try:
                    item["probability"] = float(value[2])
                except (TypeError, ValueError):
                    item["probability"] = value[2]
            links.append(item)
    return links


def _links_from_ent(ent: Any) -> list[dict[str, object]]:
    try:
        return _links(ent._.kb_ents)
    except Exception:
        return []


def _taxonerd_linker_metrics(taxonerd: object) -> dict[str, float]:
    nlp = getattr(taxonerd, "nlp", None)
    if nlp is None or "taxon_linker" not in getattr(nlp, "pipe_names", ()):
        return {}
    try:
        linker_pipe = nlp.get_pipe("taxon_linker")
    except Exception:
        return {}
    generator = getattr(linker_pipe, "candidate_generator", None)
    kb = getattr(generator, "kb", None)
    return {
        f"linker_{name}": float(value)
        for name, value in dict(getattr(kb, "last_stats", None) or {}).items()
    }


@lru_cache(maxsize=8)
def _load_taxonerd(
    model: str,
    linker: str | None,
    threshold: float,
    exclude: tuple[str, ...],
    prefer_gpu: bool,
):
    try:
        from taxonerd import TaxoNERD
    except Exception as exc:
        unavailable(
            "TaxoNERD is not installed in this runtime.", exception=type(exc).__name__
        )
    ner = TaxoNERD(prefer_gpu=prefer_gpu)
    ner.load(
        model=model,
        exclude=list(exclude),
        linker=linker,
        threshold=threshold,
    )
    _require_livb_ner_model(ner, model)
    return ner


def _require_livb_ner_model(taxonerd: Any, model: str) -> None:
    nlp = getattr(taxonerd, "nlp", None)
    if nlp is None or "ner" not in getattr(nlp, "pipe_names", []):
        unprocessable("TaxoNERD requires a spaCy NER model with a TaxoNERD LIVB label.", model=model)
    labels = tuple(getattr(nlp.get_pipe("ner"), "labels", ()))
    if labels and "LIVB" not in labels:
        unprocessable(
            "Configured model is not a TaxoNERD taxonomic NER model.",
            model=model,
            labels=list(labels),
            required_label="LIVB",
        )


def _ner_only_exclude(exclude: tuple[str, ...]) -> tuple[str, ...]:
    optimized = set(exclude)
    optimized.update({"taxon_linker", "lemmatizer", "attribute_ruler"})
    return tuple(sorted(optimized))


def _load_taxonerd_ner_only(model: str, exclude: tuple[str, ...], prefer_gpu: bool):
    return _load_taxonerd(model, None, 0.0, _ner_only_exclude(exclude), prefer_gpu)


def _load_taxonerd_legacy_components(model: str, exclude: tuple[str, ...], prefer_gpu: bool):
    return _load_taxonerd(model, None, 0.0, exclude, prefer_gpu)

def _configure_fuseki_kb(kb: object, endpoint: str | None, batch_size: int, concurrency: int, timeout: float) -> None:
    configure = getattr(kb, "configure", None)
    if callable(configure):
        configure(
            endpoint=endpoint,
            batch_size=batch_size,
            concurrency=concurrency,
            timeout=timeout,
        )


def _configure_taxonerd_fuseki_linker(taxonerd: object, endpoint: str | None, batch_size: int, concurrency: int, timeout: float) -> None:
    nlp = getattr(taxonerd, "nlp", None)
    if nlp is None or "taxon_linker" not in getattr(nlp, "pipe_names", ()):
        return
    linker_pipe = nlp.get_pipe("taxon_linker")
    generator = getattr(linker_pipe, "candidate_generator", None)
    if generator is not None:
        _configure_fuseki_kb(getattr(generator, "kb", None), endpoint, batch_size, concurrency, timeout)


@lru_cache(maxsize=4)
def _load_exact_linker(linker: str):
    try:
        from taxonerd.linking.linking_utils import KnowledgeBaseFactory
    except Exception as exc:
        unavailable("TaxoNERD linker utilities are not installed in this runtime.", exception=type(exc).__name__)
    kb = KnowledgeBaseFactory().get_kb(linker)
    try:
        kb.conn.execute("CREATE INDEX IF NOT EXISTS idx_alias_to_cuis_alias ON alias_to_cuis(alias)")
        kb.conn.commit()
    except Exception:
        pass
    return kb


@lru_cache(maxsize=4)
def _load_candidate_generator(linker: str):
    try:
        from taxonerd.linking.candidate_generation import CandidateGenerator
        from taxonerd.linking.linking_utils import KnowledgeBaseFactory
    except Exception as exc:
        unavailable("TaxoNERD ANN candidate generator is not installed in this runtime.", exception=type(exc).__name__)
    if linker == "gbif_fuseki":
        base = _load_candidate_generator("gbif_backbone")
        return CandidateGenerator(
            ann_index=base.ann_index,
            tfidf_vectorizer=base.vectorizer,
            ann_concept_aliases_list=base.ann_concept_aliases_list,
            kb=KnowledgeBaseFactory().get_kb("gbif_fuseki"),
        )
    return CandidateGenerator(name_or_path=linker)


def _candidate_generator(
    linker: str,
    ef_search: int,
    sparql_endpoint: str | None = None,
    sparql_batch_size: int = 64,
    sparql_concurrency: int = 8,
    sparql_timeout: float = 20.0,
):
    generator = _load_candidate_generator(linker)
    _configure_fuseki_kb(
        getattr(generator, "kb", None),
        sparql_endpoint,
        sparql_batch_size,
        sparql_concurrency,
        sparql_timeout,
    )
    try:
        generator.ann_index.setQueryTimeParams({"efSearch": ef_search})
    except Exception:
        pass
    return generator


def _clear_linker_backend_stats() -> None:
    _LINKER_BACKEND_STATS.value = {}


def _record_linker_backend_stats(generator: object) -> None:
    kb = getattr(generator, "kb", None)
    stats = getattr(kb, "last_stats", None)
    _LINKER_BACKEND_STATS.value = {
        f"linker_{name}": float(value)
        for name, value in dict(stats or {}).items()
    }


def _linker_backend_stats() -> dict[str, float]:
    return dict(getattr(_LINKER_BACKEND_STATS, "value", {}) or {})


async def _flush_telemetry_queue() -> None:
    try:
        from duui_py.logging.core import get_configured_event_logger
    except Exception:
        return
    logger = get_configured_event_logger()
    queue = getattr(logger, "_queue", None) if logger is not None else None
    if queue is not None:
        await queue.join()


def _require_taxonerd_method(taxonerd: Any, method: str):
    fn = getattr(taxonerd, method, None)
    if fn is None:
        unavailable(
            "Local abrami TaxoNERD fork is not active in this runtime.",
            expected_method=method,
            loaded_class=taxonerd.__class__.__module__,
        )
    return fn


def _taxon_from_row(row: dict[str, object], text: str) -> Taxon:
    mention = str(
        row.get("mention")
        or row.get("text")
        or row.get("name")
        or row.get("entity_text")
        or ""
    )
    if not mention and row.get("entity") is not None:
        mention = str(row.get("entity"))
    offsets = _offsets(row.get("offsets"), text, mention)
    if offsets is None:
        bad_gateway("TaxoNERD returned a row without usable offsets.", row=row)
    begin, end = offsets
    links = _links(row.get("entity"))
    identifier = links[0]["id"] if links else None
    value = text[begin:end] if text and 0 <= begin <= end <= len(text) else mention
    link_value = links[0].get("value") if links else None
    link_score = links[0].get("probability") if links else None
    return Taxon(
        begin=begin,
        end=end,
        value=value,
        identifier=str(identifier) if identifier is not None else None,
        features={
            LINK_ID_FEATURE: str(identifier) if identifier is not None else "",
            LINK_VALUE_FEATURE: str(link_value) if link_value is not None else "",
            LINK_SCORE_FEATURE: str(link_score) if link_score is not None else "",
            NER_LABEL_FEATURE: "LIVB",
        },
    )


def _taxon_from_legacy_row(row: list[object], text: str) -> Taxon:
    if len(row) < 2:
        bad_gateway("TaxoNERD returned a malformed row.", row=str(row))
    marker = str(row[0]).split()
    if len(marker) < 3:
        bad_gateway("TaxoNERD returned a malformed span marker.", marker=str(row[0]))
    begin = int(marker[1])
    end = int(marker[2])
    mention = str(row[1])
    links = _links(row[2]) if len(row) > 2 else []
    identifier = links[0]["id"] if links else None
    link_value = links[0].get("value") if links else None
    link_score = links[0].get("probability") if links else None
    value = text[begin:end] if text and 0 <= begin <= end <= len(text) else mention
    return Taxon(
        begin=begin,
        end=end,
        value=value,
        identifier=str(identifier) if identifier is not None else None,
        features={
            LINK_ID_FEATURE: str(identifier) if identifier is not None else "",
            LINK_VALUE_FEATURE: str(link_value) if link_value is not None else "",
            LINK_SCORE_FEATURE: str(link_score) if link_score is not None else "",
            NER_LABEL_FEATURE: marker[0] if marker else "LIVB",
        },
    )


def _taxon_from_ent(ent: Any, base_offset: int, linker: str | None) -> Taxon | None:
    if ent.label_ != "LIVB":
        return None
    covered = ent.text.replace("\n", " ")
    if "\n" in ent.text.strip("\n"):
        return None
    links = _links_from_ent(ent)
    if linker and not links:
        return None
    identifier = links[0]["id"] if links else None
    link_value = links[0].get("value") if links else None
    link_score = links[0].get("probability") if links else None
    return Taxon(
        begin=base_offset + int(ent.start_char),
        end=base_offset + int(ent.end_char),
        value=covered,
        identifier=str(identifier) if identifier is not None else None,
        features={
            LINK_ID_FEATURE: str(identifier) if identifier is not None else "",
            LINK_VALUE_FEATURE: str(link_value) if link_value is not None else "",
            LINK_SCORE_FEATURE: str(link_score) if link_score is not None else "",
            NER_LABEL_FEATURE: str(ent.label_ or "LIVB"),
        },
    )


def _taxon_from_mention(mention: Mention, links: list[dict[str, object]], linker: str | None) -> Taxon | None:
    if linker and not links:
        return None
    identifier = links[0]["id"] if links else None
    link_value = links[0].get("value") if links else None
    link_score = links[0].get("probability") if links else None
    return Taxon(
        begin=mention.begin,
        end=mention.end,
        value=mention.text,
        identifier=str(identifier) if identifier is not None else None,
        features={
            LINK_ID_FEATURE: str(identifier) if identifier is not None else "",
            LINK_VALUE_FEATURE: str(link_value) if link_value is not None else "",
            LINK_SCORE_FEATURE: str(link_score) if link_score is not None else "",
            NER_LABEL_FEATURE: str(mention.label or "LIVB"),
        },
    )


def _dedupe_taxons(taxons: Iterator[Taxon]) -> list[Taxon]:
    seen: set[tuple[int, int, str, str | None]] = set()
    out: list[Taxon] = []
    for taxon in taxons:
        key = (taxon.begin, taxon.end, taxon.value or "", taxon.identifier)
        if key in seen:
            continue
        seen.add(key)
        out.append(taxon)
    return out


def _legacy_annotation_comments(taxons: list[Taxon]) -> list[AnnotationComment]:
    comments: list[AnnotationComment] = []
    next_ref = 1
    for taxon in taxons:
        if taxon.ref is None:
            taxon.ref = next_ref
            next_ref += 1
        elif taxon.ref >= next_ref:
            next_ref = taxon.ref + 1

        features = dict(taxon.features or {})
        link_id = str(features.pop(LINK_ID_FEATURE, taxon.identifier or "") or "")
        link_value = str(features.pop(LINK_VALUE_FEATURE, taxon.value or "") or "")
        link_score = str(features.pop(LINK_SCORE_FEATURE, "") or "")
        ner_label = str(features.pop(NER_LABEL_FEATURE, "LIVB") or "LIVB")
        taxon.identifier = None
        taxon.features = features

        reference = {"$ref": int(taxon.ref)}
        comments.extend(
            [
                AnnotationComment(reference=reference, key="link", value=link_id),
                AnnotationComment(
                    reference=reference, key="identified_as", value=link_value
                ),
                AnnotationComment(reference=reference, key="similarity", value=link_score),
                AnnotationComment(reference=reference, key="unknown", value=ner_label),
            ]
        )
    return comments


def _alias_variants(value: str) -> tuple[str, ...]:
    stripped = " ".join(value.strip().split())
    if not stripped:
        return ()
    variants = [
        stripped,
        stripped.lower(),
        stripped.capitalize(),
    ]
    return tuple(dict.fromkeys(variants))


def _link_text_key(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _link_key(mention: Mention) -> str:
    return _link_text_key(mention.link_text or mention.text)


def _link_cache_get(key: tuple[object, ...]) -> list[dict[str, object]] | None:
    if LINK_CACHE_MAX <= 0:
        return None
    with _LINK_CACHE_LOCK:
        value = _LINK_CACHE.get(key)
        if value is None:
            return None
        _LINK_CACHE.move_to_end(key)
        return [dict(item) for item in value]


def _link_cache_put(key: tuple[object, ...], value: list[dict[str, object]]) -> None:
    if LINK_CACHE_MAX <= 0:
        return
    with _LINK_CACHE_LOCK:
        _LINK_CACHE[key] = [dict(item) for item in value]
        _LINK_CACHE.move_to_end(key)
        while len(_LINK_CACHE) > LINK_CACHE_MAX:
            _LINK_CACHE.popitem(last=False)


def _exact_links(
    mentions: list[Mention],
    linker: str,
) -> tuple[dict[str, list[dict[str, object]]], list[Mention]]:
    kb = _load_exact_linker(linker)
    alias_to_mentions: dict[str, list[Mention]] = {}
    for mention in mentions:
        for alias in _alias_variants(mention.link_text or mention.text):
            alias_to_mentions.setdefault(alias, []).append(mention)
    if not alias_to_mentions:
        return {}, mentions

    matches = kb.get_cuis_from_aliases(list(alias_to_mentions))
    linked: dict[str, list[dict[str, object]]] = {}
    matched_mentions: set[tuple[int, int, str]] = set()
    for alias, concept_ids in matches.items():
        links = [
            {"id": concept_id, "value": alias, "probability": 1.0}
            for concept_id in concept_ids
        ]
        if not links:
            continue
        for mention in alias_to_mentions.get(alias, []):
            key = _link_key(mention)
            linked.setdefault(key, links)
            matched_mentions.add((mention.begin, mention.end, mention.text))

    missed = [
        mention
        for mention in mentions
        if (mention.begin, mention.end, mention.text) not in matched_mentions
    ]
    return linked, missed


def _candidate_links_original(
    mention_strings: list[str],
    linker: str,
    neighbours: int,
    threshold: float,
    ann_ef_search: int,
    sparql_endpoint: str | None = None,
    sparql_batch_size: int = 64,
    sparql_concurrency: int = 8,
    sparql_timeout: float = 20.0,
) -> dict[str, list[dict[str, object]]]:
    with _CANDIDATE_GENERATOR_LOCK:
        generator = _candidate_generator(
            linker,
            ann_ef_search,
            sparql_endpoint,
            sparql_batch_size,
            sparql_concurrency,
            sparql_timeout,
        )
        batch_candidates = generator(mention_strings, neighbours)
        _record_linker_backend_stats(generator)
    return _candidate_links_from_batches(mention_strings, batch_candidates, generator, threshold)


def _candidate_links_batched(
    mention_strings: list[str],
    linker: str,
    neighbours: int,
    threshold: float,
    ann_ef_search: int,
    sparql_endpoint: str | None = None,
    sparql_batch_size: int = 64,
    sparql_concurrency: int = 8,
    sparql_timeout: float = 20.0,
) -> dict[str, list[dict[str, object]]]:
    if not mention_strings:
        return {}

    with _CANDIDATE_GENERATOR_LOCK:
        generator = _candidate_generator(
            linker,
            ann_ef_search,
            sparql_endpoint,
            sparql_batch_size,
            sparql_concurrency,
            sparql_timeout,
        )
        tfidfs = generator.vectorizer.transform(mention_strings)
        batch_neighbors, batch_distances = generator.nmslib_knn_with_zero_vectors(tfidfs, neighbours)
        alias_list = generator.ann_concept_aliases_list
        mention_alias_scores: list[dict[str, float] | None] = []
        all_aliases: set[str] = set()
        for neighbors, distances in zip(batch_neighbors, batch_distances, strict=False):
            alias_scores: dict[str, float] = {}
            if neighbors is not None and distances is not None:
                for neighbor_index, distance in zip(neighbors, distances, strict=False):
                    if neighbor_index is None:
                        continue
                    alias = alias_list[int(neighbor_index)]
                    similarity = 1.0 - float(distance)
                    previous = alias_scores.get(alias)
                    if previous is None or similarity > previous:
                        alias_scores[alias] = similarity
            if alias_scores:
                mention_alias_scores.append(alias_scores)
                all_aliases.update(alias_scores)
            else:
                mention_alias_scores.append(None)

        aliases_to_concepts = generator.kb.get_cuis_from_aliases(list(all_aliases)) if all_aliases else {}
        _record_linker_backend_stats(generator)
        out: dict[str, list[dict[str, object]]] = {}
        for mention_string, alias_scores in zip(mention_strings, mention_alias_scores, strict=False):
            if not alias_scores:
                out[mention_string] = []
                continue
            concept_to_best_alias: dict[str, str] = {}
            concept_to_best_score: dict[str, float] = {}
            for alias, similarity in alias_scores.items():
                for concept_id in aliases_to_concepts.get(alias, ()):
                    previous = concept_to_best_score.get(concept_id)
                    if previous is None or similarity > previous:
                        concept_to_best_score[concept_id] = similarity
                        concept_to_best_alias[concept_id] = alias
            predicted: list[dict[str, object]] = []
            for concept_id, score in concept_to_best_score.items():
                if score <= threshold:
                    continue
                predicted.append(
                    {
                        "id": concept_id,
                        "value": concept_to_best_alias[concept_id],
                        "probability": score,
                    }
                )
            predicted.sort(key=lambda item: float(item.get("probability", 0.0)), reverse=True)
            if predicted:
                best = predicted[0]["probability"]
                out[mention_string] = [
                    item for item in predicted if item.get("probability") == best
                ]
            else:
                out[mention_string] = []
    return out


def _candidate_links_from_batches(
    mention_strings: list[str],
    batch_candidates: list[list[Any]],
    generator: Any,
    threshold: float,
) -> dict[str, list[dict[str, object]]]:
    out: dict[str, list[dict[str, object]]] = {}
    for mention_string, candidates in zip(mention_strings, batch_candidates, strict=False):
        predicted: list[dict[str, object]] = []
        for candidate in candidates:
            score = max(candidate.similarities) if candidate.similarities else 0.0
            if score <= threshold:
                continue
            predicted.append(
                {
                    "id": candidate.concept_id,
                    "value": candidate.aliases[0],
                    "probability": score,
                }
            )
        predicted.sort(key=lambda item: float(item.get("probability", 0.0)), reverse=True)
        if predicted:
            best = predicted[0]["probability"]
            out[mention_string] = [
                item for item in predicted if item.get("probability") == best
            ]
        else:
            out[mention_string] = []
    return out


def _link_mention_batch(
    mentions: list[Mention],
    linker: str,
    neighbours: int,
    threshold: float,
    ann_ef_search: int = 80,
    strategy: str = "exact-first-batched",
    use_cache: bool = True,
    sparql_endpoint: str | None = None,
    sparql_batch_size: int = 64,
    sparql_concurrency: int = 8,
    sparql_timeout: float = 20.0,
) -> tuple[dict[str, list[dict[str, object]]], dict[str, float]]:
    started = time()
    exact: dict[str, list[dict[str, object]]] = {}
    missed = mentions
    if strategy in {"exact-first-batched", "exact-first-original", "exact-only"}:
        exact, missed = _exact_links(mentions, linker)
    exact_ms = (time() - started) * 1000.0
    if strategy == "exact-only":
        return exact, {
            "linker_exact_ms": exact_ms,
            "linker_ann_ms": 0.0,
            "linker_exact_matches": float(len(exact)),
            "linker_ann_mentions": 0.0,
            "linker_cache_hits": 0.0,
            "linker_cache_misses": 0.0,
        }

    mention_source = missed if strategy in {"exact-first-batched", "exact-first-original"} else mentions
    mention_strings = list(dict.fromkeys(_link_key(mention) for mention in mention_source if _link_key(mention)))
    cached: dict[str, list[dict[str, object]]] = {}
    pending: list[str] = []
    cache_hits = 0
    for mention_string in mention_strings:
        cache_key = (linker, strategy, neighbours, round(threshold, 6), ann_ef_search, mention_string)
        cached_value = _link_cache_get(cache_key) if use_cache else None
        if cached_value is None:
            pending.append(mention_string)
            continue
        cached[mention_string] = cached_value
        cache_hits += 1

    ann_pending = pending

    ann_started = time()
    _clear_linker_backend_stats()
    if strategy in {"exact-first-original", "ann-original"}:
        ann = _candidate_links_original(
            ann_pending,
            linker,
            neighbours,
            threshold,
            ann_ef_search,
            sparql_endpoint,
            sparql_batch_size,
            sparql_concurrency,
            sparql_timeout,
        )
    else:
        ann = _candidate_links_batched(
            ann_pending,
            linker,
            neighbours,
            threshold,
            ann_ef_search,
            sparql_endpoint,
            sparql_batch_size,
            sparql_concurrency,
            sparql_timeout,
        )
    ann_ms = (time() - ann_started) * 1000.0
    backend_stats = _linker_backend_stats()

    if use_cache:
        for mention_string, links in ann.items():
            cache_key = (linker, strategy, neighbours, round(threshold, 6), ann_ef_search, mention_string)
            _link_cache_put(cache_key, links)

    out = dict(exact)
    out.update(cached)
    out.update(ann)
    return out, {
        "linker_exact_ms": exact_ms,
        "linker_ann_ms": ann_ms,
        "linker_exact_matches": float(len(exact)),
        "linker_ann_mentions": float(len(ann_pending)),
        "linker_cache_hits": float(cache_hits),
        "linker_cache_misses": float(len(pending)),
        **backend_stats,
    }



def _taxons_from_doc(spacy_doc: Any, base_offset: int, linker: str | None) -> list[Taxon]:
    return _dedupe_taxons(
        taxon
        for ent in spacy_doc.ents
        for taxon in [_taxon_from_ent(ent, base_offset, linker)]
        if taxon is not None
    )


def _mentions_from_doc(spacy_doc: Any, base_offset: int = 0) -> list[Mention]:
    mentions: list[Mention] = []
    for ent in spacy_doc.ents:
        if ent.label_ != "LIVB":
            continue
        if "\n" in ent.text.strip("\n"):
            continue
        long_form = getattr(getattr(ent, "_", None), "long_form", None)
        link_source = long_form if long_form is not None else ent
        link_text = " ".join(
            (getattr(token, "lemma_", "") or getattr(token, "text", "")).lower()
            for token in link_source
        ).strip()
        mentions.append(
            Mention(
                base_offset + int(ent.start_char),
                base_offset + int(ent.end_char),
                ent.text.replace("\n", " "),
                "taxonerd-livb",
                str(ent.label_ or "LIVB"),
                link_text or None,
            )
        )
    return mentions


def _taxons_from_mentions(
    mentions: list[Mention],
    linker: str | None,
    neighbours: int,
    threshold: float,
    ann_ef_search: int,
    linker_strategy: str = "exact-first-batched",
    link_cache: bool = True,
    sparql_endpoint: str | None = None,
    sparql_batch_size: int = 64,
    sparql_concurrency: int = 8,
    sparql_timeout: float = 20.0,
) -> tuple[list[Taxon], dict[str, float]]:
    if linker is None:
        return (
            _dedupe_taxons(
                taxon
                for mention in mentions
                for taxon in [_taxon_from_mention(mention, [], linker)]
                if taxon is not None
            ),
            {},
        )
    linked, metrics = _link_mention_batch(
        mentions,
        linker,
        neighbours,
        threshold,
        ann_ef_search=ann_ef_search,
        strategy=linker_strategy,
        use_cache=link_cache,
        sparql_endpoint=sparql_endpoint,
        sparql_batch_size=sparql_batch_size,
        sparql_concurrency=sparql_concurrency,
        sparql_timeout=sparql_timeout,
    )
    return (
        _dedupe_taxons(
            taxon
            for mention in mentions
            for taxon in [
                _taxon_from_mention(
                    mention,
                    _links(linked.get(_link_key(mention))),
                    linker,
                )
            ]
            if taxon is not None
        ),
        metrics,
    )


def _valid_span(fs: FeatureStructure, text_len: int, accepted_types: set[str]) -> tuple[int, int, str] | None:
    if fs.type not in accepted_types or fs.begin is None or fs.end is None:
        return None
    begin = max(0, int(fs.begin))
    end = min(text_len, int(fs.end))
    if begin >= end:
        return None
    return begin, end, fs.type


def _select_spans(
    items: list[FeatureStructure],
    text_len: int,
    preferred_types: tuple[str, ...],
) -> list[tuple[int, int, str]]:
    by_type: dict[str, list[tuple[int, int, str]]] = {}
    accepted = set(preferred_types)
    for item in items:
        span = _valid_span(item, text_len, accepted)
        if span is None:
            continue
        by_type.setdefault(item.type, []).append(span)
    for span_type in preferred_types:
        spans = sorted(set(by_type.get(span_type, [])))
        if spans:
            return spans
    return []


def _split_long_range(
    text: str,
    begin: int,
    end: int,
    max_chars: int,
    overlap_chars: int,
    source_type: str,
) -> Iterator[TextWindow]:
    cursor = begin
    while cursor < end:
        hard_end = min(end, cursor + max_chars)
        if hard_end < end:
            split_at = max(
                text.rfind("\n", cursor, hard_end),
                text.rfind(" ", cursor, hard_end),
            )
            if split_at > cursor + max_chars // 2:
                hard_end = split_at
        chunk = text[cursor:hard_end]
        if chunk.strip():
            yield TextWindow(cursor, hard_end, chunk, source_type)
        if hard_end >= end:
            break
        cursor = max(cursor + 1, hard_end - overlap_chars)


def _windows(
    text: str,
    spans: list[tuple[int, int, str]],
    max_chars: int,
    overlap_chars: int,
    merge_spans: bool,
) -> list[TextWindow]:
    if not merge_spans:
        out: list[TextWindow] = []
        for begin, end, source_type in spans:
            if end - begin > max_chars:
                out.extend(_split_long_range(text, begin, end, max_chars, overlap_chars, source_type))
                continue
            chunk = text[begin:end]
            if chunk.strip():
                out.append(TextWindow(begin, end, chunk, source_type))
        return out

    out: list[TextWindow] = []
    current_begin: int | None = None
    current_end: int | None = None
    current_type = ""
    for begin, end, source_type in spans:
        if current_begin is None or current_end is None:
            current_begin, current_end, current_type = begin, end, source_type
            continue
        if end - current_begin <= max_chars:
            current_end = end
            current_type = f"{current_type}+{source_type}" if source_type not in current_type else current_type
            continue
        out.append(TextWindow(current_begin, current_end, text[current_begin:current_end], current_type))
        current_begin, current_end, current_type = begin, end, source_type
    if current_begin is not None and current_end is not None:
        out.append(TextWindow(current_begin, current_end, text[current_begin:current_end], current_type))
    split: list[TextWindow] = []
    for window in out:
        if window.end - window.begin > max_chars:
            split.extend(_split_long_range(text, window.begin, window.end, max_chars, overlap_chars, window.source_type))
        elif window.text.strip():
            split.append(window)
    return split


def _run_whole_document(
    text: str,
    model: str,
    linker: str | None,
    threshold: float,
    exclude: tuple[str, ...],
    prefer_gpu: bool,
    neighbours: int,
    ann_ef_search: int,
    linker_strategy: str,
    link_cache: bool,
    sparql_endpoint: str | None,
    sparql_batch_size: int,
    sparql_concurrency: int,
    sparql_timeout: float,
) -> StrategyResult:
    load_started = time()
    taxonerd = _load_taxonerd_ner_only(model, exclude, prefer_gpu)
    load_ms = (time() - load_started) * 1000.0
    ner_started = time()
    doc = taxonerd.ner(text)
    ner_ms = (time() - ner_started) * 1000.0
    mentions_started = time()
    mentions = _mentions_from_doc(doc)
    mentions_ms = (time() - mentions_started) * 1000.0
    taxons, linker_metrics = _taxons_from_mentions(
        mentions,
        linker,
        neighbours,
        threshold,
        ann_ef_search,
        linker_strategy,
        link_cache,
        sparql_endpoint,
        sparql_batch_size,
        sparql_concurrency,
        sparql_timeout,
    )
    return StrategyResult(
        taxons,
        windows=1,
        mentions=len(mentions),
        metrics={
            "taxonerd_load_ms": load_ms,
            "taxonerd_ner_ms": ner_ms,
            "taxonerd_mentions_ms": mentions_ms,
            **linker_metrics,
        },
    )


def _run_legacy_procedure(
    text: str,
    model: str,
    linker: str | None,
    threshold: float,
    exclude: tuple[str, ...],
    prefer_gpu: bool,
    sparql_endpoint: str | None,
    sparql_batch_size: int,
    sparql_concurrency: int,
    sparql_timeout: float,
) -> StrategyResult:
    taxonerd = _load_taxonerd(model, linker, threshold, exclude, prefer_gpu)
    _configure_taxonerd_fuseki_linker(
        taxonerd,
        sparql_endpoint,
        sparql_batch_size,
        sparql_concurrency,
        sparql_timeout,
    )
    try:
        rows = taxonerd.find_in_text(text).values.tolist()
    except Exception as exc:
        bad_gateway(
            "TaxoNERD legacy-procedure processing failed.",
            exception=type(exc).__name__,
            detail=str(exc),
        )
    taxons = _dedupe_taxons(_taxon_from_legacy_row(row, text) for row in rows)
    return StrategyResult(
        taxons,
        windows=1,
        mentions=len(taxons),
        metrics=_taxonerd_linker_metrics(taxonerd),
    )


def _run_legacy_compatible_whole_document(
    text: str,
    model: str,
    linker: str | None,
    threshold: float,
    exclude: tuple[str, ...],
    prefer_gpu: bool,
    neighbours: int,
    ann_ef_search: int,
    linker_strategy: str,
    link_cache: bool,
    sparql_endpoint: str | None,
    sparql_batch_size: int,
    sparql_concurrency: int,
    sparql_timeout: float,
) -> StrategyResult:
    load_started = time()
    taxonerd = _load_taxonerd_legacy_components(model, exclude, prefer_gpu)
    load_ms = (time() - load_started) * 1000.0
    ner_started = time()
    doc = taxonerd.ner(text)
    ner_ms = (time() - ner_started) * 1000.0
    mentions_started = time()
    mentions = _mentions_from_doc(doc)
    mentions_ms = (time() - mentions_started) * 1000.0
    taxons, linker_metrics = _taxons_from_mentions(
        mentions,
        linker,
        neighbours,
        threshold,
        ann_ef_search,
        linker_strategy,
        link_cache,
        sparql_endpoint,
        sparql_batch_size,
        sparql_concurrency,
        sparql_timeout,
    )
    return StrategyResult(
        taxons,
        windows=1,
        mentions=len(mentions),
        metrics={
            "taxonerd_load_ms": load_ms,
            "taxonerd_ner_ms": ner_ms,
            "taxonerd_mentions_ms": mentions_ms,
            **linker_metrics,
        },
    )


def _run_span_windows(
    text: str,
    fs_items: list[FeatureStructure],
    model: str,
    linker: str | None,
    threshold: float,
    exclude: tuple[str, ...],
    prefer_gpu: bool,
    span_types: tuple[str, ...],
    max_window_chars: int,
    overlap_chars: int,
    merge_spans: bool,
    batch_size: int,
    n_process: int,
    neighbours: int,
    ann_ef_search: int,
    linker_strategy: str,
    link_cache: bool,
    sparql_endpoint: str | None,
    sparql_batch_size: int,
    sparql_concurrency: int,
    sparql_timeout: float,
) -> StrategyResult:
    spans = _select_spans(fs_items, len(text), span_types)
    if not spans:
        unprocessable(
            "TaxoNERD span-window strategy requires span annotations in the input CAS.",
            span_types=list(span_types),
        )
    windows = _windows(text, spans, max_window_chars, overlap_chars, merge_spans)
    if not windows:
        unprocessable("TaxoNERD span-window strategy found no non-empty windows.")
    taxonerd = _load_taxonerd_ner_only(model, exclude, prefer_gpu)
    mentions: list[Mention] = []
    pipe_texts = _require_taxonerd_method(taxonerd, "pipe_texts")
    docs = pipe_texts((window.text for window in windows), batch_size=batch_size, n_process=n_process)
    for window, spacy_doc in zip(windows, docs, strict=False):
        mentions.extend(_mentions_from_doc(spacy_doc, window.begin))
    taxons, linker_metrics = _taxons_from_mentions(
        mentions,
        linker,
        neighbours,
        threshold,
        ann_ef_search,
        linker_strategy,
        link_cache,
        sparql_endpoint,
        sparql_batch_size,
        sparql_concurrency,
        sparql_timeout,
    )
    return StrategyResult(
        taxons,
        windows=len(windows),
        mentions=len(mentions),
        metrics=linker_metrics,
    )


def _run_strategy(
    strategy: str,
    text: str,
    fs_items: list[FeatureStructure],
    model: str,
    linker: str | None,
    threshold: float,
    exclude: tuple[str, ...],
    prefer_gpu: bool,
    span_types: tuple[str, ...],
    max_window_chars: int,
    overlap_chars: int,
    merge_spans: bool,
    batch_size: int,
    n_process: int,
    neighbours: int,
    ann_ef_search: int,
    linker_strategy: str,
    link_cache: bool,
    sparql_endpoint: str | None,
    sparql_batch_size: int,
    sparql_concurrency: int,
    sparql_timeout: float,
) -> StrategyResult:
    if strategy == "whole-document":
        return _run_whole_document(
            text,
            model,
            linker,
            threshold,
            exclude,
            prefer_gpu,
            neighbours,
            ann_ef_search,
            linker_strategy,
            link_cache,
            sparql_endpoint,
            sparql_batch_size,
            sparql_concurrency,
            sparql_timeout,
        )
    if strategy == "legacy-procedure":
        return _run_legacy_procedure(
            text,
            model,
            linker,
            threshold,
            exclude,
            prefer_gpu,
            sparql_endpoint,
            sparql_batch_size,
            sparql_concurrency,
            sparql_timeout,
        )
    if strategy == "legacy-compatible":
        return _run_legacy_compatible_whole_document(
            text,
            model,
            linker,
            threshold,
            exclude,
            prefer_gpu,
            neighbours,
            ann_ef_search,
            linker_strategy,
            link_cache,
            sparql_endpoint,
            sparql_batch_size,
            sparql_concurrency,
            sparql_timeout,
        )
    if strategy == "span-window":
        return _run_span_windows(
            text,
            fs_items,
            model,
            linker,
            threshold,
            exclude,
            prefer_gpu,
            span_types,
            max_window_chars,
            overlap_chars,
            merge_spans,
            batch_size,
            n_process,
            neighbours,
            ann_ef_search,
            linker_strategy,
            link_cache,
            sparql_endpoint,
            sparql_batch_size,
            sparql_concurrency,
            sparql_timeout,
        )
    raise ValueError(f"unhandled strategy: {strategy}")


class TaxoNERDAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "TTLab-UIMA/taxoNERD migration"}),
        descriptor=AnnotatorDescriptor(
            name="taxonerd-msgpack-lua",
            version="1.2.0",
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
                    "Taxon": [TAXON_TYPE],
                    "AnnotationComment": [ANNOTATION_COMMENT_TYPE],
                },
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemTaxoNERD.xml",
        parameters_schema={
            "input_strategy": {
                "type": "string",
                "default": "whole-document",
                "enum": [
                    "whole-document",
                    "legacy-procedure",
                    "legacy-compatible",
                    "span-window",
                ],
                "description": "Generic TaxoNERD input strategy selected by the DUUI pipeline.",
            },
            "model": {
                "type": "string",
                "default": "en_ner_eco_md",
                "description": "TaxoNERD model alias or installed spaCy model package. The model must expose an NER pipe with label LIVB.",
            },
            "model_name": {
                "type": "string",
                "description": "Legacy parameter alias for model.",
            },
            "linking": {
                "type": "string",
                "default": "gbif_backbone",
                "description": "TaxoNERD linker alias. Use gbif_fuseki to resolve ANN candidate aliases against the UCE BioFID Fuseki GBIF graph.",
            },
            "linker_name": {
                "type": "string",
                "description": "Legacy parameter alias for linking.",
            },
            "linker_strategy": {
                "type": "string",
                "default": "exact-first-batched",
                "enum": [
                    "exact-first-batched",
                    "exact-first-original",
                    "ann-batched",
                    "ann-original",
                    "exact-only",
                ],
                "description": "TaxoNERD linker procedure. exact-first-batched keeps the same logical candidate generator but batches alias-to-concept SQL resolution across all ANN neighbors.",
            },
            "linking_strategy": {
                "type": "string",
                "description": "Alias for linker_strategy.",
            },
            "link_cache": {
                "type": "boolean",
                "default": True,
                "description": "Cache linked mention strings across documents in this runtime process.",
            },
            "span_types": {
                "type": "string",
                "default": "sentence",
                "description": "Comma-separated required input span types for span-window strategy.",
            },
            "max_window_chars": {"type": "integer", "default": 2500},
            "overlap_chars": {"type": "integer", "default": 160},
            "merge_spans": {"type": "boolean", "default": False},
            "batch_size": {"type": "integer", "default": 8},
            "n_process": {
                "type": "integer",
                "default": 1,
                "description": "spaCy n_process for TaxoNERD span-window pipe execution.",
            },
            "neighbours": {"type": "integer", "default": 10},
            "ann_ef_search": {
                "type": "integer",
                "default": 80,
                "description": "HNSW ef_search used by the generic TaxoNERD ANN candidate generator.",
            },
            "sparql_endpoint": {
                "type": "string",
                "default": DEFAULT_SPARQL_ENDPOINT,
                "description": "UCE Fuseki SPARQL endpoint used by the gbif_fuseki linker.",
            },
            "sparql_batch_size": {
                "type": "integer",
                "default": 64,
                "description": "Number of normalized mention strings per SPARQL VALUES query.",
            },
            "sparql_concurrency": {
                "type": "integer",
                "default": 8,
                "description": "Maximum concurrent SPARQL chunk requests.",
            },
            "sparql_timeout": {
                "type": "number",
                "default": 20.0,
                "description": "Fuseki HTTP request timeout in seconds.",
            },
            "prefer_gpu": {
                "type": "boolean",
                "default": False,
                "description": "Passed to TaxoNERD.",
            },
            "threshold": {
                "type": "number",
                "default": 0.7,
                "description": "TaxoNERD GBIF linking threshold.",
            },
            "exclude": {
                "type": "string",
                "description": "Comma-separated spaCy/TaxoNERD pipeline components to exclude.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        parameters = doc.parameters
        strategy = _strategy(parameters.get("input_strategy") or parameters.get("strategy"))
        model = _model_name(parameters.get("model") or parameters.get("model_name"))
        linker = _linker_name(parameters.get("linking") or parameters.get("linker_name"))
        linker_strategy = _linker_strategy(
            parameters.get("linker_strategy") or parameters.get("linking_strategy")
        )
        link_cache = _bool(parameters.get("link_cache"), True)
        if linker is None and not _bool(parameters.get("allow_unlinked"), False):
            unprocessable("TaxoNERD runtime evaluation requires GBIF linking.")
        prefer_gpu = _bool(parameters.get("prefer_gpu"), False)
        threshold = _float(parameters.get("threshold"), 0.7)
        exclude = _exclude(parameters.get("exclude"))
        span_types = _aliased_types(parameters.get("span_types"), DEFAULT_SPAN_PRIORITY, SPAN_TYPE_ALIASES)
        max_window_chars = _int(parameters.get("max_window_chars"), 2500, minimum=128)
        overlap_chars = _int(parameters.get("overlap_chars"), 160, minimum=0)
        merge_spans = _bool(parameters.get("merge_spans"), False)
        batch_size = _int(parameters.get("batch_size"), 8, minimum=1)
        n_process = _int(parameters.get("n_process"), 1, minimum=1)
        neighbours = _int(parameters.get("neighbours"), 10, minimum=1)
        ann_ef_search = _int(parameters.get("ann_ef_search"), 80, minimum=10)
        sparql_endpoint = _string(
            parameters.get("sparql_endpoint"),
            DEFAULT_SPARQL_ENDPOINT,
        )
        sparql_batch_size = _int(parameters.get("sparql_batch_size"), 64, minimum=1)
        sparql_concurrency = _int(parameters.get("sparql_concurrency"), 8, minimum=1)
        sparql_timeout = _float(parameters.get("sparql_timeout"), 20.0)

        _emit_telemetry(telemetry.trace(
            "TaxoNERD process request configured",
            model=model,
            linker=linker,
            strategy=strategy,
            linker_strategy=linker_strategy,
            link_cache=link_cache,
            threshold=threshold,
            exclude=list(exclude),
            text_length=len(text),
            fs_count=len(doc.fs),
            span_types=list(span_types),
            batch_size=batch_size,
            n_process=n_process,
            neighbours=neighbours,
            ann_ef_search=ann_ef_search,
            sparql_endpoint=sparql_endpoint if linker == "gbif_fuseki" else "",
            sparql_batch_size=sparql_batch_size,
            sparql_concurrency=sparql_concurrency,
            sparql_timeout=sparql_timeout,
        ))

        async def run_taxonerd_strategy() -> StrategyResult:
            strategy_started = time()
            try:
                return await asyncio.to_thread(
                    _run_strategy,
                    strategy,
                    text,
                    list(doc.fs),
                    model,
                    linker,
                    threshold,
                    exclude,
                    prefer_gpu,
                    span_types,
                    max_window_chars,
                    overlap_chars,
                    merge_spans,
                    batch_size,
                    n_process,
                    neighbours,
                    ann_ef_search,
                    linker_strategy,
                    link_cache,
                    sparql_endpoint,
                    sparql_batch_size,
                    sparql_concurrency,
                    sparql_timeout,
                )
            finally:
                _emit_telemetry(
                    telemetry.timing(
                        "taxonerd_strategy_ms",
                        (time() - strategy_started) * 1000,
                        annotator="taxonerd",
                        strategy=strategy,
                    )
                )

        try:
            result = await run_taxonerd_strategy()
        except Exception as exc:
            await telemetry.error(
                "TaxoNERD strategy failed",
                strategy=strategy,
                exception=type(exc).__name__,
                detail=str(exc),
            )
            raise

        elapsed_ms = int((time() - started) * 1000)
        _emit_telemetry(
            telemetry.timing(
                "taxonerd_processing_ms",
                elapsed_ms,
                annotator="taxonerd",
                strategy=strategy,
            )
        )
        linker_metric_tags = {
            f"taxonerd_{name}": f"{float(value):.6f}"
            for name, value in result.metrics.items()
        }
        _emit_telemetry(telemetry.count(
            "taxonerd_taxon_matches",
            len(result.taxons),
            linking=linker or "none",
            model=model,
            strategy=strategy,
            **linker_metric_tags,
        ))
        _emit_telemetry(telemetry.count("taxonerd_input_windows", result.windows, strategy=strategy))
        _emit_telemetry(telemetry.count("taxonerd_input_mentions", result.mentions, strategy=strategy))
        metric_attrs = {
            "linking": linker or "none",
            "model": model,
            "strategy": strategy,
            "linker_strategy": linker_strategy,
        }
        for metric_name, metric_value in result.metrics.items():
            if metric_name.endswith("_ms"):
                _emit_telemetry(telemetry.timing(f"taxonerd_{metric_name}", metric_value, **metric_attrs))
            else:
                _emit_telemetry(telemetry.gauge(f"taxonerd_{metric_name}", float(metric_value), "count", **metric_attrs))
        _emit_telemetry(telemetry.debug(
            "TaxoNERD processing completed",
            matches=len(result.taxons),
            annotation_comments=len(result.taxons) * 4,
            elapsed_ms=elapsed_ms,
            effective_linker=linker or "none",
            strategy=strategy,
            linker_strategy=linker_strategy,
            link_cache=link_cache,
            windows=result.windows,
            mentions=result.mentions,
            linker_metrics=result.metrics,
        ))
        comments = _legacy_annotation_comments(result.taxons)
        comment_parts = [
            f"{self.config.descriptor.name}",
            f"strategy={strategy}",
            f"model={model}",
            f"linker={linker or 'none'}",
        ]
        yield DuuiResult.model_construct(
            annotations=result.taxons,
            feature_structures=comments,
            meta=AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName=model,
                modelVersion="1.2.0",
            ),
            modification_meta=DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=" ".join(comment_parts),
            ),
            errors=[],
            sofa=None,
        )


app = create_app(TaxoNERDAnnotator, request_adapter=AsyncChunkedRequestAdapter())


def _preload_runtime() -> None:
    model = _model_name(None)
    linker_values = _csv("gbif_backbone", ("gbif_backbone",))
    linkers = tuple(
        linker
        for value in linker_values
        for linker in [_linker_name(value)]
        if linker is not None
    )
    exclude = _exclude(None)
    prefer_gpu = False
    ann_ef_search = 80
    threshold = 0.7
    _load_taxonerd_legacy_components(model, exclude, prefer_gpu)
    for linker in linkers:
        _load_taxonerd(model, linker, threshold, exclude, prefer_gpu)
        _load_exact_linker(linker)
        _candidate_generator(linker, ann_ef_search)


@app.on_event("startup")
async def preload_runtime_on_startup() -> None:
    started = time()
    try:
        await asyncio.to_thread(_preload_runtime)
    except Exception as exc:
        await telemetry.error(
            "TaxoNERD runtime preload failed",
            exception=type(exc).__name__,
            detail=str(exc),
        )
        raise
    await telemetry.info(
        "TaxoNERD runtime preloaded",
        elapsed_ms=int((time() - started) * 1000),
    )
