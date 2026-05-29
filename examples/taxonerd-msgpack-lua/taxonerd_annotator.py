from __future__ import annotations

import asyncio
import os
from collections import OrderedDict
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from functools import lru_cache
from threading import Lock
from time import time
from typing import Any

from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import bad_gateway, unavailable, unprocessable
from duui_py.logging.core import get_configured_event_logger
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    AnnotatorMetaData,
    DocumentModification,
    Domain,
    DomainSpec,
    DuuiError,
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

# ---------------------------------------------------------------------------
# UIMA type constants
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Feature name constants
# ---------------------------------------------------------------------------
LINK_ID_FEATURE = "_taxonerd_link_id"
LINK_VALUE_FEATURE = "_taxonerd_link_value"
LINK_SCORE_FEATURE = "_taxonerd_link_score"
NER_LABEL_FEATURE = "_taxonerd_ner_label"

# ---------------------------------------------------------------------------
# Module-level caches & shared state
# ---------------------------------------------------------------------------
DEFAULT_SPARQL_ENDPOINT = "http://host.containers.internal:8098/biofid-search/sparql"
LINK_CACHE_MAX = 20000
_LINK_CACHE: OrderedDict[tuple[object, ...], list[dict[str, object]]] = OrderedDict()
_LINK_CACHE_LOCK = Lock()
_CANDIDATE_GENERATOR_LOCK = Lock()

SPAN_TYPE_ALIASES: dict[str, str] = {
    "sentence": SENTENCE_TYPE, "sentences": SENTENCE_TYPE,
    "paragraph": PARAGRAPH_TYPE, "paragraphs": PARAGRAPH_TYPE,
    "div": DIV_TYPE, "dkpro-div": DIV_TYPE,
    "hucompute-div": HUCOMPUTE_DIV_TYPE,
    "section": SECTION_TYPE, "sections": SECTION_TYPE,
    "title": TITLE_TYPE, "titles": TITLE_TYPE,
    "ocr-paragraph": OCR_PARAGRAPH_TYPE, "ocr_paragraph": OCR_PARAGRAPH_TYPE,
    "abbyy-paragraph": ABBYY_PARAGRAPH_TYPE, "abbyy_paragraph": ABBYY_PARAGRAPH_TYPE,
}
DEFAULT_SPAN_PRIORITY = (
    SENTENCE_TYPE, PARAGRAPH_TYPE, DIV_TYPE, HUCOMPUTE_DIV_TYPE,
    SECTION_TYPE, TITLE_TYPE, OCR_PARAGRAPH_TYPE, ABBYY_PARAGRAPH_TYPE,
)

# ---------------------------------------------------------------------------
# Domain data classes
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# GPU detection
# ---------------------------------------------------------------------------
def _gpu_available() -> bool:
    for env_var in ("CUDA_VISIBLE_DEVICES", "CUDA_DEVICE_ORDER"):
        if os.environ.get(env_var, "").strip():
            return True
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        pass
    try:
        import spacy
        if spacy.prefer_gpu():
            return True
    except Exception:
        pass
    return False


def _resolve_prefer_gpu(parameter_value: object | None) -> bool:
    if parameter_value is not None:
        if isinstance(parameter_value, bool):
            return parameter_value
        return str(parameter_value).strip().lower() in {"1", "true", "yes", "y", "on"}
    return _gpu_available()


# ===================================================================
# TaxoNERD Annotator
# ===================================================================
class TaxoNERDAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    """DUUI annotator wrapping TaxoNERD taxonomic NER + linking pipeline."""

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
                "enum": ["whole-document", "legacy-procedure", "span-window"],
                "description": "TaxoNERD input strategy. whole-document is optimal latency default.",
            },
            "model": {
                "type": "string",
                "default": "en_ner_eco_md",
                "description": "TaxoNERD model alias or installed spaCy model package.",
            },
            "linking": {
                "type": "string",
                "default": "gbif_backbone",
                "description": "TaxoNERD linker alias.",
            },
            "linker_strategy": {
                "type": "string",
                "default": "exact-first-batched",
                "enum": ["exact-first-batched", "exact-only"],
                "description": "TaxoNERD linker procedure.",
            },
            "link_cache": {
                "type": "boolean",
                "default": True,
                "description": "Cache linked mention strings across documents.",
            },
            "span_types": {
                "type": "string",
                "default": "sentence",
                "description": "Comma-separated span types for span-window strategy.",
            },
            "max_window_chars": {"type": "integer", "default": 2500},
            "overlap_chars": {"type": "integer", "default": 160},
            "merge_spans": {"type": "boolean", "default": False},
            "batch_size": {"type": "integer", "default": 8},
            "n_process": {"type": "integer", "default": 1},
            "neighbours": {"type": "integer", "default": 10},
            "ann_ef_search": {"type": "integer", "default": 80},
            "sparql_endpoint": {
                "type": "string",
                "default": DEFAULT_SPARQL_ENDPOINT,
            },
            "sparql_batch_size": {"type": "integer", "default": 64},
            "sparql_concurrency": {"type": "integer", "default": 8},
            "sparql_timeout": {"type": "number", "default": 20.0},
            "prefer_gpu": {
                "type": "boolean",
                "default": False,
                "description": "Auto-detected if not set.",
            },
            "threshold": {"type": "number", "default": 0.7},
            "exclude": {"type": "string"},
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    # ==================================================================
    # Shared helpers (called from ≥2 places)
    # ==================================================================

    @staticmethod
    def _dedupe_taxons(taxons: Iterator[Taxon]) -> list[Taxon]:
        seen: set[tuple[int, int, str, str | None]] = set()
        out: list[Taxon] = []
        for taxon in taxons:
            key = (taxon.begin, taxon.end, taxon.value or "", taxon.identifier)
            if key not in seen:
                seen.add(key)
                out.append(taxon)
        return out

    @staticmethod
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
            comments.extend([
                AnnotationComment(reference=reference, key="link", value=link_id),
                AnnotationComment(reference=reference, key="identified_as", value=link_value),
                AnnotationComment(reference=reference, key="similarity", value=link_score),
                AnnotationComment(reference=reference, key="unknown", value=ner_label),
            ])
        return comments

    @staticmethod
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
            mentions.append(Mention(
                base_offset + int(ent.start_char),
                base_offset + int(ent.end_char),
                ent.text.replace("\n", " "),
                "taxonerd-livb",
                str(ent.label_ or "LIVB"),
                link_text or None,
            ))
        return mentions

    @staticmethod
    def _link_text_key(value: object) -> str:
        return " ".join(str(value or "").strip().lower().split())

    @staticmethod
    def _link_key(mention: Mention) -> str:
        return TaxoNERDAnnotator._link_text_key(mention.link_text or mention.text)

    @staticmethod
    def _alias_variants(value: str) -> tuple[str, ...]:
        stripped = " ".join(value.strip().split())
        if not stripped:
            return ()
        return tuple(dict.fromkeys([stripped, stripped.lower(), stripped.capitalize()]))

    # ==================================================================
    # Link cache
    # ==================================================================

    @staticmethod
    def _link_cache_get(key: tuple[object, ...]) -> list[dict[str, object]] | None:
        if LINK_CACHE_MAX <= 0:
            return None
        with _LINK_CACHE_LOCK:
            value = _LINK_CACHE.get(key)
            if value is None:
                return None
            _LINK_CACHE.move_to_end(key)
            return [dict(item) for item in value]

    @staticmethod
    def _link_cache_put(key: tuple[object, ...], value: list[dict[str, object]]) -> None:
        if LINK_CACHE_MAX <= 0:
            return
        with _LINK_CACHE_LOCK:
            _LINK_CACHE[key] = [dict(item) for item in value]
            _LINK_CACHE.move_to_end(key)
            while len(_LINK_CACHE) > LINK_CACHE_MAX:
                _LINK_CACHE.popitem(last=False)

    # ==================================================================
    # Model loading
    # ==================================================================

    @staticmethod
    @lru_cache(maxsize=8)
    def _load_taxonerd(
        model: str, linker: str | None, threshold: float,
        exclude: tuple[str, ...], prefer_gpu: bool,
    ):
        try:
            from taxonerd import TaxoNERD
        except Exception as exc:
            unavailable(
                "TaxoNERD is not installed in this runtime.",
                exception=type(exc).__name__,
            )
        ner = TaxoNERD(prefer_gpu=prefer_gpu)
        ner.load(model=model, exclude=list(exclude), linker=linker, threshold=threshold)
        nlp = getattr(ner, "nlp", None)
        if nlp is None or "ner" not in getattr(nlp, "pipe_names", []):
            unprocessable("TaxoNERD requires a spaCy NER model with a LIVB label.", model=model)
        labels = tuple(getattr(nlp.get_pipe("ner"), "labels", ()))
        if labels and "LIVB" not in labels:
            unprocessable(
                "Configured model is not a TaxoNERD taxonomic NER model.",
                model=model, labels=list(labels), required_label="LIVB",
            )
        return ner

    @staticmethod
    def _load_taxonerd_ner_only(model: str, exclude: tuple[str, ...], prefer_gpu: bool):
        optimized = set(exclude)
        optimized.update({"taxon_linker", "lemmatizer", "attribute_ruler"})
        return TaxoNERDAnnotator._load_taxonerd(model, None, 0.0, tuple(sorted(optimized)), prefer_gpu)

    @staticmethod
    def _load_taxonerd_legacy_components(model: str, exclude: tuple[str, ...], prefer_gpu: bool):
        return TaxoNERDAnnotator._load_taxonerd(model, None, 0.0, exclude, prefer_gpu)

    @staticmethod
    def _configure_taxonerd_fuseki_linker(
        taxonerd: object, endpoint: str | None,
        batch_size: int, concurrency: int, timeout: float,
    ) -> None:
        nlp = getattr(taxonerd, "nlp", None)
        if nlp is None or "taxon_linker" not in getattr(nlp, "pipe_names", ()):
            return
        linker_pipe = nlp.get_pipe("taxon_linker")
        generator = getattr(linker_pipe, "candidate_generator", None)
        kb = getattr(generator, "kb", None)
        configure = getattr(kb, "configure", None)
        if callable(configure):
            configure(endpoint=endpoint, batch_size=batch_size, concurrency=concurrency, timeout=timeout)

    @staticmethod
    @lru_cache(maxsize=4)
    def _load_exact_linker(linker: str):
        try:
            from taxonerd.linking.linking_utils import KnowledgeBaseFactory
        except Exception as exc:
            unavailable(
                "TaxoNERD linker utilities are not installed.",
                exception=type(exc).__name__,
            )
        kb = KnowledgeBaseFactory().get_kb(linker)
        try:
            kb.conn.execute("CREATE INDEX IF NOT EXISTS idx_alias_to_cuis_alias ON alias_to_cuis(alias)")
            kb.conn.commit()
        except Exception:
            pass
        return kb

    @staticmethod
    @lru_cache(maxsize=4)
    def _load_candidate_generator(linker: str):
        try:
            from taxonerd.linking.candidate_generation import CandidateGenerator
            from taxonerd.linking.linking_utils import KnowledgeBaseFactory
        except Exception as exc:
            unavailable(
                "TaxoNERD ANN candidate generator is not installed.",
                exception=type(exc).__name__,
            )
        if linker == "gbif_fuseki":
            base = TaxoNERDAnnotator._load_candidate_generator("gbif_backbone")
            return CandidateGenerator(
                ann_index=base.ann_index,
                tfidf_vectorizer=base.vectorizer,
                ann_concept_aliases_list=base.ann_concept_aliases_list,
                kb=KnowledgeBaseFactory().get_kb("gbif_fuseki"),
            )
        return CandidateGenerator(name_or_path=linker)

    @staticmethod
    def _candidate_generator(
        linker: str, ef_search: int,
        sparql_endpoint: str | None = None,
        sparql_batch_size: int = 64, sparql_concurrency: int = 8,
        sparql_timeout: float = 20.0,
    ):
        generator = TaxoNERDAnnotator._load_candidate_generator(linker)
        kb = getattr(generator, "kb", None)
        configure = getattr(kb, "configure", None)
        if callable(configure):
            configure(endpoint=sparql_endpoint, batch_size=sparql_batch_size,
                      concurrency=sparql_concurrency, timeout=sparql_timeout)
        try:
            generator.ann_index.setQueryTimeParams({"efSearch": ef_search})
        except Exception:
            pass
        return generator

    @staticmethod
    def _require_taxonerd_method(taxonerd: Any, method: str):
        fn = getattr(taxonerd, method, None)
        if fn is None:
            unavailable(
                "Local abrami TaxoNERD fork is not active.",
                expected_method=method,
                loaded_class=taxonerd.__class__.__module__,
            )
        return fn

    # ==================================================================
    # Exact linker
    # ==================================================================

    @staticmethod
    def _exact_links(
        mentions: list[Mention], linker: str,
    ) -> tuple[dict[str, list[dict[str, object]]], list[Mention]]:
        kb = TaxoNERDAnnotator._load_exact_linker(linker)
        alias_to_mentions: dict[str, list[Mention]] = {}
        for mention in mentions:
            for alias in TaxoNERDAnnotator._alias_variants(mention.link_text or mention.text):
                alias_to_mentions.setdefault(alias, []).append(mention)
        if not alias_to_mentions:
            return {}, mentions
        matches = kb.get_cuis_from_aliases(list(alias_to_mentions))
        linked: dict[str, list[dict[str, object]]] = {}
        matched_mentions: set[tuple[int, int, str]] = set()
        for alias, concept_ids in matches.items():
            links = [{"id": cid, "value": alias, "probability": 1.0} for cid in concept_ids]
            if not links:
                continue
            for mention in alias_to_mentions.get(alias, []):
                key = TaxoNERDAnnotator._link_key(mention)
                linked.setdefault(key, links)
                matched_mentions.add((mention.begin, mention.end, mention.text))
        missed = [m for m in mentions if (m.begin, m.end, m.text) not in matched_mentions]
        return linked, missed

    # ==================================================================
    # ANN candidate linker (batched — optimal latency)
    # ==================================================================

    @staticmethod
    def _candidate_links_batched(
        mention_strings: list[str], linker: str, neighbours: int,
        threshold: float, ann_ef_search: int,
        sparql_endpoint: str | None = None,
        sparql_batch_size: int = 64, sparql_concurrency: int = 8,
        sparql_timeout: float = 20.0,
    ) -> dict[str, list[dict[str, object]]]:
        if not mention_strings:
            return {}

        with _CANDIDATE_GENERATOR_LOCK:
            generator = TaxoNERDAnnotator._candidate_generator(
                linker, ann_ef_search,
                sparql_endpoint, sparql_batch_size, sparql_concurrency, sparql_timeout,
            )
            tfidfs = generator.vectorizer.transform(mention_strings)
            batch_neighbors, batch_distances = generator.nmslib_knn_with_zero_vectors(tfidfs, neighbours)
            alias_list = generator.ann_concept_aliases_list
            mention_alias_scores: list[dict[str, float] | None] = []
            all_aliases: set[str] = set()
            for neighbors, distances in zip(batch_neighbors, batch_distances, strict=False):
                alias_scores: dict[str, float] = {}
                if neighbors is not None and distances is not None:
                    for ni, dist in zip(neighbors, distances, strict=False):
                        if ni is None:
                            continue
                        alias = alias_list[int(ni)]
                        similarity = 1.0 - float(dist)
                        prev = alias_scores.get(alias)
                        if prev is None or similarity > prev:
                            alias_scores[alias] = similarity
                if alias_scores:
                    mention_alias_scores.append(alias_scores)
                    all_aliases.update(alias_scores)
                else:
                    mention_alias_scores.append(None)
            aliases_to_concepts = generator.kb.get_cuis_from_aliases(list(all_aliases)) if all_aliases else {}
            out: dict[str, list[dict[str, object]]] = {}
            for mention_string, alias_scores in zip(mention_strings, mention_alias_scores, strict=False):
                if not alias_scores:
                    out[mention_string] = []
                    continue
                concept_best_alias: dict[str, str] = {}
                concept_best_score: dict[str, float] = {}
                for alias, similarity in alias_scores.items():
                    for concept_id in aliases_to_concepts.get(alias, ()):
                        prev = concept_best_score.get(concept_id)
                        if prev is None or similarity > prev:
                            concept_best_score[concept_id] = similarity
                            concept_best_alias[concept_id] = alias
                predicted: list[dict[str, object]] = []
                for concept_id, score in concept_best_score.items():
                    if score <= threshold:
                        continue
                    predicted.append({"id": concept_id, "value": concept_best_alias[concept_id], "probability": score})
                predicted.sort(key=lambda item: float(item.get("probability", 0.0)), reverse=True)
                if predicted:
                    best = predicted[0]["probability"]
                    out[mention_string] = [item for item in predicted if item.get("probability") == best]
                else:
                    out[mention_string] = []
        return out

    # ==================================================================
    # Mention batch linker
    # ==================================================================

    @staticmethod
    def _link_mention_batch(
        mentions: list[Mention], linker: str, neighbours: int,
        threshold: float, ann_ef_search: int = 80,
        linker_strategy: str = "exact-first-batched",
        use_cache: bool = True,
        sparql_endpoint: str | None = None,
        sparql_batch_size: int = 64, sparql_concurrency: int = 8,
        sparql_timeout: float = 20.0,
    ) -> tuple[dict[str, list[dict[str, object]]], dict[str, float]]:
        started = time()
        exact: dict[str, list[dict[str, object]]] = {}
        missed = mentions
        if linker_strategy in {"exact-first-batched", "exact-only"}:
            exact, missed = TaxoNERDAnnotator._exact_links(mentions, linker)
        exact_ms = (time() - started) * 1000.0
        if linker_strategy == "exact-only":
            return exact, {"linker_exact_ms": exact_ms, "linker_ann_ms": 0.0,
                           "linker_exact_matches": float(len(exact)),
                           "linker_ann_mentions": 0.0,
                           "linker_cache_hits": 0.0, "linker_cache_misses": 0.0}

        mention_source = missed
        mention_strings = list(dict.fromkeys(
            TaxoNERDAnnotator._link_key(m) for m in mention_source
            if TaxoNERDAnnotator._link_key(m)
        ))
        cached: dict[str, list[dict[str, object]]] = {}
        pending: list[str] = []
        cache_hits = 0
        for mention_string in mention_strings:
            cache_key = (linker, linker_strategy, neighbours, round(threshold, 6), ann_ef_search, mention_string)
            cached_val = TaxoNERDAnnotator._link_cache_get(cache_key) if use_cache else None
            if cached_val is None:
                pending.append(mention_string)
            else:
                cached[mention_string] = cached_val
                cache_hits += 1

        ann_started = time()
        ann = TaxoNERDAnnotator._candidate_links_batched(
            pending, linker, neighbours, threshold, ann_ef_search,
            sparql_endpoint, sparql_batch_size, sparql_concurrency, sparql_timeout,
        )
        ann_ms = (time() - ann_started) * 1000.0

        if use_cache:
            for mention_string, links in ann.items():
                cache_key = (linker, linker_strategy, neighbours, round(threshold, 6), ann_ef_search, mention_string)
                TaxoNERDAnnotator._link_cache_put(cache_key, links)

        out = dict(exact)
        out.update(cached)
        out.update(ann)
        return out, {
            "linker_exact_ms": exact_ms, "linker_ann_ms": ann_ms,
            "linker_exact_matches": float(len(exact)),
            "linker_ann_mentions": float(len(pending)),
            "linker_cache_hits": float(cache_hits),
            "linker_cache_misses": float(len(pending)),
        }

    # ==================================================================
    # Taxon from mention (unified builder)
    # ==================================================================

    @staticmethod
    def _taxon_from_mention(
        mention: Mention, links: list[dict[str, object]], linker: str | None,
    ) -> Taxon | None:
        if linker and not links:
            return None
        identifier = links[0]["id"] if links else None
        return Taxon(
            begin=mention.begin, end=mention.end, value=mention.text,
            identifier=str(identifier) if identifier is not None else None,
            features={
                LINK_ID_FEATURE: str(identifier) if identifier is not None else "",
                LINK_VALUE_FEATURE: str(links[0].get("value")) if links and links[0].get("value") else "",
                LINK_SCORE_FEATURE: str(links[0].get("probability")) if links and links[0].get("probability") else "",
                NER_LABEL_FEATURE: str(mention.label or "LIVB"),
            },
        )

    @staticmethod
    def _taxons_from_mentions(
        mentions: list[Mention], linker: str | None, neighbours: int,
        threshold: float, ann_ef_search: int,
        linker_strategy: str = "exact-first-batched",
        link_cache: bool = True,
        sparql_endpoint: str | None = None,
        sparql_batch_size: int = 64, sparql_concurrency: int = 8,
        sparql_timeout: float = 20.0,
    ) -> tuple[list[Taxon], dict[str, float]]:
        if linker is None:
            return (
                TaxoNERDAnnotator._dedupe_taxons(
                    taxon for mention in mentions
                    for taxon in [TaxoNERDAnnotator._taxon_from_mention(mention, [], linker)]
                    if taxon is not None
                ),
                {},
            )
        linked, metrics = TaxoNERDAnnotator._link_mention_batch(
            mentions, linker, neighbours, threshold,
            ann_ef_search=ann_ef_search, linker_strategy=linker_strategy,
            use_cache=link_cache,
            sparql_endpoint=sparql_endpoint, sparql_batch_size=sparql_batch_size,
            sparql_concurrency=sparql_concurrency, sparql_timeout=sparql_timeout,
        )
        return (
            TaxoNERDAnnotator._dedupe_taxons(
                taxon for mention in mentions
                for taxon in [TaxoNERDAnnotator._taxon_from_mention(
                    mention,
                    TaxoNERDAnnotator._links_from_mention_key(linked, mention),
                    linker,
                )]
                if taxon is not None
            ),
            metrics,
        )

    @staticmethod
    def _links_from_mention_key(
        linked: dict[str, list[dict[str, object]]], mention: Mention,
    ) -> list[dict[str, object]]:
        """Extract links dict for a mention from the linker result map."""
        key = TaxoNERDAnnotator._link_key(mention)
        value = linked.get(key)
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return [value]
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            item: dict[str, object] = {"id": str(value[0]), "value": str(value[1])}
            if len(value) >= 3:
                try:
                    item["probability"] = float(value[2])
                except (TypeError, ValueError):
                    item["probability"] = value[2]
            return [item]
        return []

    # ==================================================================
    # Span / window helpers
    # ==================================================================

    @staticmethod
    def _select_spans(
        items: list[FeatureStructure], text_len: int,
        preferred_types: tuple[str, ...],
    ) -> list[tuple[int, int, str]]:
        by_type: dict[str, list[tuple[int, int, str]]] = {}
        accepted = set(preferred_types)
        for item in items:
            if item.type not in accepted or item.begin is None or item.end is None:
                continue
            begin = max(0, int(item.begin))
            end = min(text_len, int(item.end))
            if begin >= end:
                continue
            by_type.setdefault(item.type, []).append((begin, end, item.type))
        for span_type in preferred_types:
            spans = sorted(set(by_type.get(span_type, [])))
            if spans:
                return spans
        return []

    @staticmethod
    def _split_long_range(
        text: str, begin: int, end: int, max_chars: int,
        overlap_chars: int, source_type: str,
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

    @staticmethod
    def _windows(
        text: str, spans: list[tuple[int, int, str]],
        max_chars: int, overlap_chars: int, merge_spans: bool,
    ) -> list[TextWindow]:
        if not merge_spans:
            out: list[TextWindow] = []
            for begin, end, source_type in spans:
                if end - begin > max_chars:
                    out.extend(TaxoNERDAnnotator._split_long_range(
                        text, begin, end, max_chars, overlap_chars, source_type,
                    ))
                    continue
                chunk = text[begin:end]
                if chunk.strip():
                    out.append(TextWindow(begin, end, chunk, source_type))
            return out

        out: list[TextWindow] = []
        cur_begin: int | None = None
        cur_end: int | None = None
        cur_type = ""
        for begin, end, source_type in spans:
            if cur_begin is None or cur_end is None:
                cur_begin, cur_end, cur_type = begin, end, source_type
                continue
            if end - cur_begin <= max_chars:
                cur_end = end
                cur_type = f"{cur_type}+{source_type}" if source_type not in cur_type else cur_type
                continue
            out.append(TextWindow(cur_begin, cur_end, text[cur_begin:cur_end], cur_type))
            cur_begin, cur_end, cur_type = begin, end, source_type
        if cur_begin is not None and cur_end is not None:
            out.append(TextWindow(cur_begin, cur_end, text[cur_begin:cur_end], cur_type))
        split: list[TextWindow] = []
        for window in out:
            if window.end - window.begin > max_chars:
                split.extend(TaxoNERDAnnotator._split_long_range(
                    text, window.begin, window.end, max_chars, overlap_chars, window.source_type,
                ))
            elif window.text.strip():
                split.append(window)
        return split

    # ==================================================================
    # Strategy runners
    # ==================================================================

    @staticmethod
    def _run_whole_document(
        text: str, model: str, linker: str | None, threshold: float,
        exclude: tuple[str, ...], prefer_gpu: bool,
        neighbours: int, ann_ef_search: int, linker_strategy: str,
        link_cache: bool,
        sparql_endpoint: str | None, sparql_batch_size: int,
        sparql_concurrency: int, sparql_timeout: float,
    ) -> StrategyResult:
        load_started = time()
        taxonerd = TaxoNERDAnnotator._load_taxonerd_ner_only(model, exclude, prefer_gpu)
        load_ms = (time() - load_started) * 1000.0

        ner_started = time()
        doc = taxonerd.ner(text)
        ner_ms = (time() - ner_started) * 1000.0

        mentions_started = time()
        mentions = TaxoNERDAnnotator._mentions_from_doc(doc)
        mentions_ms = (time() - mentions_started) * 1000.0

        taxons, linker_metrics = TaxoNERDAnnotator._taxons_from_mentions(
            mentions, linker, neighbours, threshold, ann_ef_search,
            linker_strategy, link_cache,
            sparql_endpoint, sparql_batch_size, sparql_concurrency, sparql_timeout,
        )
        return StrategyResult(taxons, windows=1, mentions=len(mentions), metrics={
            "taxonerd_load_ms": load_ms, "taxonerd_ner_ms": ner_ms,
            "taxonerd_mentions_ms": mentions_ms, **linker_metrics,
        })

    @staticmethod
    def _run_legacy_procedure(
        text: str, model: str, linker: str | None, threshold: float,
        exclude: tuple[str, ...], prefer_gpu: bool,
        sparql_endpoint: str | None, sparql_batch_size: int,
        sparql_concurrency: int, sparql_timeout: float,
    ) -> StrategyResult:
        taxonerd = TaxoNERDAnnotator._load_taxonerd(model, linker, threshold, exclude, prefer_gpu)
        TaxoNERDAnnotator._configure_taxonerd_fuseki_linker(
            taxonerd, sparql_endpoint, sparql_batch_size, sparql_concurrency, sparql_timeout,
        )
        try:
            rows = taxonerd.find_in_text(text).values.tolist()
        except Exception as exc:
            bad_gateway(
                "TaxoNERD legacy-procedure processing failed.",
                exception=type(exc).__name__, detail=str(exc),
            )

        def _taxon_from_legacy_row(row: list[object]) -> Taxon:
            if len(row) < 2:
                bad_gateway("TaxoNERD returned a malformed row.", row=str(row))
            marker = str(row[0]).split()
            if len(marker) < 3:
                bad_gateway("TaxoNERD returned a malformed span marker.", marker=str(row[0]))
            begin = int(marker[1])
            end = int(marker[2])
            mention = str(row[1])
            raw_links = row[2] if len(row) > 2 else []
            links_list = raw_links if isinstance(raw_links, list) else [raw_links]
            links: list[dict[str, object]] = []
            for val in links_list:
                if isinstance(val, dict):
                    links.append(val)
                elif isinstance(val, (list, tuple)) and len(val) >= 2:
                    item: dict[str, object] = {"id": str(val[0]), "value": str(val[1])}
                    if len(val) >= 3:
                        try:
                            item["probability"] = float(val[2])
                        except (TypeError, ValueError):
                            item["probability"] = val[2]
                    links.append(item)
            identifier = links[0]["id"] if links else None
            value = text[begin:end] if text and 0 <= begin <= end <= len(text) else mention
            return Taxon(
                begin=begin, end=end, value=value,
                identifier=str(identifier) if identifier is not None else None,
                features={
                    LINK_ID_FEATURE: str(identifier) if identifier is not None else "",
                    LINK_VALUE_FEATURE: str(links[0].get("value")) if links and links[0].get("value") else "",
                    LINK_SCORE_FEATURE: str(links[0].get("probability")) if links and links[0].get("probability") else "",
                    NER_LABEL_FEATURE: marker[0] if marker else "LIVB",
                },
            )

        taxons = TaxoNERDAnnotator._dedupe_taxons(
            _taxon_from_legacy_row(row) for row in rows
        )

        nlp = getattr(taxonerd, "nlp", None)
        linker_metrics: dict[str, float] = {}
        if nlp is not None and "taxon_linker" in getattr(nlp, "pipe_names", ()):
            try:
                linker_pipe = nlp.get_pipe("taxon_linker")
                gen = getattr(linker_pipe, "candidate_generator", None)
                kb = getattr(gen, "kb", None)
                linker_metrics = {
                    f"linker_{name}": float(value)
                    for name, value in dict(getattr(kb, "last_stats", None) or {}).items()
                }
            except Exception:
                pass

        return StrategyResult(taxons, windows=1, mentions=len(taxons), metrics=linker_metrics)

    @staticmethod
    def _run_span_windows(
        text: str, fs_items: list[FeatureStructure],
        model: str, linker: str | None, threshold: float,
        exclude: tuple[str, ...], prefer_gpu: bool,
        span_types: tuple[str, ...],
        max_window_chars: int, overlap_chars: int, merge_spans: bool,
        batch_size: int, n_process: int,
        neighbours: int, ann_ef_search: int,
        linker_strategy: str, link_cache: bool,
        sparql_endpoint: str | None, sparql_batch_size: int,
        sparql_concurrency: int, sparql_timeout: float,
    ) -> StrategyResult:
        spans = TaxoNERDAnnotator._select_spans(fs_items, len(text), span_types)
        if not spans:
            unprocessable(
                "TaxoNERD span-window strategy requires span annotations in the input CAS.",
                span_types=list(span_types),
            )
        windows = TaxoNERDAnnotator._windows(text, spans, max_window_chars, overlap_chars, merge_spans)
        if not windows:
            unprocessable("TaxoNERD span-window strategy found no non-empty windows.")

        taxonerd = TaxoNERDAnnotator._load_taxonerd_ner_only(model, exclude, prefer_gpu)
        mentions: list[Mention] = []
        pipe_texts = TaxoNERDAnnotator._require_taxonerd_method(taxonerd, "pipe_texts")
        docs = pipe_texts(
            (window.text for window in windows),
            batch_size=batch_size, n_process=n_process,
        )
        for window, spacy_doc in zip(windows, docs, strict=False):
            mentions.extend(TaxoNERDAnnotator._mentions_from_doc(spacy_doc, window.begin))

        taxons, linker_metrics = TaxoNERDAnnotator._taxons_from_mentions(
            mentions, linker, neighbours, threshold, ann_ef_search,
            linker_strategy, link_cache,
            sparql_endpoint, sparql_batch_size, sparql_concurrency, sparql_timeout,
        )
        return StrategyResult(taxons, windows=len(windows), mentions=len(mentions), metrics=linker_metrics)

    @staticmethod
    def _run_strategy(
        strategy: str, text: str, fs_items: list[FeatureStructure],
        model: str, linker: str | None, threshold: float,
        exclude: tuple[str, ...], prefer_gpu: bool,
        span_types: tuple[str, ...],
        max_window_chars: int, overlap_chars: int, merge_spans: bool,
        batch_size: int, n_process: int,
        neighbours: int, ann_ef_search: int,
        linker_strategy: str, link_cache: bool,
        sparql_endpoint: str | None, sparql_batch_size: int,
        sparql_concurrency: int, sparql_timeout: float,
    ) -> StrategyResult:
        if strategy == "legacy-procedure":
            return TaxoNERDAnnotator._run_legacy_procedure(
                text, model, linker, threshold, exclude, prefer_gpu,
                sparql_endpoint, sparql_batch_size, sparql_concurrency, sparql_timeout,
            )
        if strategy == "span-window":
            return TaxoNERDAnnotator._run_span_windows(
                text, fs_items, model, linker, threshold, exclude, prefer_gpu,
                span_types, max_window_chars, overlap_chars, merge_spans,
                batch_size, n_process, neighbours, ann_ef_search,
                linker_strategy, link_cache,
                sparql_endpoint, sparql_batch_size, sparql_concurrency, sparql_timeout,
            )
        # default: whole-document
        return TaxoNERDAnnotator._run_whole_document(
            text, model, linker, threshold, exclude, prefer_gpu,
            neighbours, ann_ef_search, linker_strategy, link_cache,
            sparql_endpoint, sparql_batch_size, sparql_concurrency, sparql_timeout,
        )

    # ==================================================================
    # process() — single entry point
    # ==================================================================

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        logger = get_configured_event_logger()
        started = time()

        # -- inline parameter resolution ----------------------------------------
        def _param_str(key: str, default: str = "") -> str:
            val = doc.parameters.get(key)
            return str(val).strip() if val is not None else default

        def _param_bool(key: str, default: bool = False) -> bool:
            val = doc.parameters.get(key)
            if val is None:
                return default
            if isinstance(val, bool):
                return val
            return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}

        def _param_float(key: str, default: float) -> float:
            val = doc.parameters.get(key)
            if val is None:
                return default
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        def _param_int(key: str, default: int, minimum: int = 1) -> int:
            try:
                return max(minimum, int(doc.parameters.get(key, default)))
            except (TypeError, ValueError):
                return default

        def _param_csv(key: str, default: tuple[str, ...]) -> tuple[str, ...]:
            val = doc.parameters.get(key)
            if val is None:
                return default
            if isinstance(val, str):
                raw = [item.strip() for item in val.split(",")]
            elif isinstance(val, (list, tuple, set)):
                raw = [str(item).strip() for item in val]
            else:
                raw = [str(val).strip()]
            return tuple(item for item in raw if item) or default

        def _param_aliased_types(key: str) -> tuple[str, ...]:
            items = _param_csv(key, DEFAULT_SPAN_PRIORITY)
            out: list[str] = []
            for item in items:
                norm = item.lower().replace("_", "-")
                out.append(SPAN_TYPE_ALIASES.get(norm, item))
            return tuple(dict.fromkeys(out))

        def _param_exclude() -> tuple[str, ...]:
            val = doc.parameters.get("exclude")
            if val is None:
                return ("tagger", "parser", "taxo_abbrev_detector", "taxon_linker", "pysbd_sentencizer")
            if isinstance(val, (list, tuple, set)):
                return tuple(str(item) for item in val)
            text = str(val).strip()
            if not text or text == "[]":
                return ()
            return tuple(
                item.strip().strip("'\"")
                for item in text.strip("[]").split(",")
                if item.strip()
            )

        def _emit_telemetry(coro: object) -> None:
            try:
                asyncio.create_task(coro)  # type: ignore[arg-type]
            except RuntimeError:
                pass

        # -- resolve parameters ------------------------------------------------
        text = sofa_text_value(doc.sofa) or ""

        strategy_raw = _param_str("input_strategy") or _param_str("strategy") or "whole-document"
        strategy = strategy_raw.strip().lower().replace("_", "-")
        if strategy not in {"whole-document", "legacy-procedure", "span-window"}:
            strategy = "whole-document"

        model_raw = _param_str("model") or _param_str("model_name") or "en_ner_eco_md"
        model = {"biobert": "en_ner_eco_biobert", "biobert_weak": "en_ner_eco_biobert_weak",
                 "md": "en_ner_eco_md", "md_weak": "en_ner_eco_md_weak"}.get(model_raw, model_raw)

        linker_raw = _param_str("linking") or _param_str("linker_name") or "gbif_backbone"
        linker_map = {"gbif": "gbif_backbone", "gbif_backbone": "gbif_backbone",
                      "fuseki": "gbif_fuseki", "gbif_fuseki": "gbif_fuseki",
                      "biofid_fuseki": "gbif_fuseki", "sparql": "gbif_fuseki",
                      "taxref": "taxref", "ncbi": "ncbi_taxonomy", "ncbi_taxonomy": "ncbi_taxonomy",
                      "ncbi_lite": "ncbi_taxonomy_lite", "ncbi_taxonomy_lite": "ncbi_taxonomy_lite",
                      "none": None, "": None}
        if linker_raw not in linker_map:
            unprocessable("Unsupported TaxoNERD linker.", linker=linker_raw, supported=sorted(linker_map))
        linker = linker_map[linker_raw]

        ls_raw = _param_str("linker_strategy") or _param_str("linking_strategy") or "exact-first-batched"
        ls_norm = ls_raw.strip().lower().replace("_", "-")
        linker_strategy = "exact-first-batched" if ls_norm not in {"exact-first-batched", "exact-only"} else ls_norm

        link_cache = _param_bool("link_cache", True)
        prefer_gpu = _resolve_prefer_gpu(doc.parameters.get("prefer_gpu"))
        threshold = _param_float("threshold", 0.7)
        exclude = _param_exclude()
        span_types = _param_aliased_types("span_types")
        max_window_chars = _param_int("max_window_chars", 2500, minimum=128)
        overlap_chars = _param_int("overlap_chars", 160, minimum=0)
        merge_spans = _param_bool("merge_spans", False)
        batch_size = _param_int("batch_size", 8)
        n_process = _param_int("n_process", os.cpu_count() or 1)
        neighbours = _param_int("neighbours", 10)
        ann_ef_search = _param_int("ann_ef_search", 80, minimum=10)
        sparql_endpoint = _param_str("sparql_endpoint", DEFAULT_SPARQL_ENDPOINT)
        sparql_batch_size = _param_int("sparql_batch_size", 64)
        sparql_concurrency = _param_int("sparql_concurrency", 8)
        sparql_timeout = _param_float("sparql_timeout", 20.0)

        if logger is not None:
            await logger.trace(
                f"TaxoNERD process() entry: len={len(text)} fs={len(doc.fs)} "
                f"strategy={strategy} model={model} linker={linker} linker_strategy={linker_strategy}"
            )
            await logger.info(
                f"TaxoNERD process started: strategy={strategy} model={model} "
                f"linker={linker} text_length={len(text)}"
            )

        if linker is None and not _param_bool("allow_unlinked", False):
            if logger is not None:
                await logger.error("TaxoNERD: linker is None and allow_unlinked is False")
            unprocessable("TaxoNERD runtime evaluation requires GBIF linking.")

        # -- telemetry: request configured --------------------------------------
        _emit_telemetry(telemetry.trace(
            "TaxoNERD process request configured",
            model=model, linker=linker, strategy=strategy,
            linker_strategy=linker_strategy, link_cache=link_cache,
            threshold=threshold, exclude=list(exclude),
            text_length=len(text), fs_count=len(doc.fs),
            span_types=list(span_types), batch_size=batch_size,
            n_process=n_process, neighbours=neighbours,
            ann_ef_search=ann_ef_search,
            sparql_endpoint=sparql_endpoint if linker == "gbif_fuseki" else "",
        ))

        # -- run strategy in thread ---------------------------------------------
        async def run_taxonerd_strategy() -> StrategyResult:
            strategy_started = time()
            if logger is not None:
                await logger.info(f"TaxoNERD strategy execution starting: {strategy}")
            try:
                return await asyncio.to_thread(
                    self._run_strategy,
                    strategy, text, list(doc.fs),
                    model, linker, threshold, exclude, prefer_gpu,
                    span_types, max_window_chars, overlap_chars, merge_spans,
                    batch_size, n_process, neighbours, ann_ef_search,
                    linker_strategy, link_cache,
                    sparql_endpoint, sparql_batch_size,
                    sparql_concurrency, sparql_timeout,
                )
            finally:
                elapsed = (time() - strategy_started) * 1000
                if logger is not None:
                    await logger.info(f"TaxoNERD strategy execution completed in {elapsed:.1f} ms")
                _emit_telemetry(telemetry.timing(
                    "taxonerd_strategy_ms", elapsed,
                    annotator="taxonerd", strategy=strategy,
                ))

        try:
            result = await run_taxonerd_strategy()
        except Exception as exc:
            if logger is not None:
                await logger.error(
                    f"TaxoNERD strategy failed: strategy={strategy} "
                    f"exception={type(exc).__name__} detail={str(exc)}",
                )
            await telemetry.error(
                "TaxoNERD strategy failed",
                strategy=strategy, exception=type(exc).__name__, detail=str(exc),
            )
            yield DuuiResult.model_construct(
                annotations=[], feature_structures=[], meta=None,
                modification_meta=None,
                errors=[DuuiError(message=str(exc), title="TaxoNERD Processing Error", status=500, retryable=False)],
            )
            return

        # -- metrics ------------------------------------------------------------
        elapsed_ms = int((time() - started) * 1000)
        if logger is not None:
            await logger.info(
                f"TaxoNERD processing completed in {elapsed_ms} ms: "
                f"{len(result.taxons)} taxons, {result.windows} windows, {result.mentions} mentions",
            )

        _emit_telemetry(telemetry.timing("taxonerd_processing_ms", elapsed_ms, annotator="taxonerd", strategy=strategy))
        linker_metric_tags = {f"taxonerd_{name}": f"{float(value):.6f}" for name, value in result.metrics.items()}
        _emit_telemetry(telemetry.count(
            "taxonerd_taxon_matches", len(result.taxons),
            linking=linker or "none", model=model, strategy=strategy,
            **linker_metric_tags,
        ))
        _emit_telemetry(telemetry.count("taxonerd_input_windows", result.windows, strategy=strategy))
        _emit_telemetry(telemetry.count("taxonerd_input_mentions", result.mentions, strategy=strategy))

        metric_attrs = {"linking": linker or "none", "model": model, "strategy": strategy, "linker_strategy": linker_strategy}
        for metric_name, metric_value in result.metrics.items():
            if metric_name.endswith("_ms"):
                _emit_telemetry(telemetry.timing(f"taxonerd_{metric_name}", metric_value, **metric_attrs))
            else:
                _emit_telemetry(telemetry.gauge(f"taxonerd_{metric_name}", float(metric_value), "count", **metric_attrs))

        # -- build result -------------------------------------------------------
        comments = self._legacy_annotation_comments(result.taxons)
        comment_parts = [
            f"{self.config.descriptor.name}",
            f"strategy={strategy}", f"model={model}", f"linker={linker or 'none'}",
        ]
        yield DuuiResult.model_construct(
            annotations=result.taxons,
            feature_structures=comments,
            meta=AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName=model, modelVersion="1.2.0",
            ),
            modification_meta=DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=" ".join(comment_parts),
            ),
            errors=[], sofa=None,
        )
        if logger is not None:
            await logger.trace(f"TaxoNERD process() exit: {len(result.taxons)} taxons, {elapsed_ms} ms")


# ===================================================================
# App factory & startup
# ===================================================================

app = create_app(TaxoNERDAnnotator, request_adapter=AsyncChunkedRequestAdapter())


def _preload_runtime() -> None:
    """Pre-load TaxoNERD models and linkers at startup (called in thread)."""
    exclude = ("tagger", "parser", "taxo_abbrev_detector", "taxon_linker", "pysbd_sentencizer")
    prefer_gpu = _resolve_prefer_gpu(None)
    TaxoNERDAnnotator._load_taxonerd_legacy_components("en_ner_eco_md", exclude, prefer_gpu)
    TaxoNERDAnnotator._load_taxonerd("en_ner_eco_md", "gbif_backbone", 0.7, exclude, prefer_gpu)
    TaxoNERDAnnotator._load_exact_linker("gbif_backbone")
    TaxoNERDAnnotator._candidate_generator("gbif_backbone", 80)


@app.on_event("startup")
async def preload_runtime_on_startup() -> None:
    import sys
    import traceback
    logger = get_configured_event_logger()
    try:
        await asyncio.to_thread(_preload_runtime)
        if logger is not None:
            await logger.info("TaxoNERD runtime preloaded successfully")
    except Exception:
        traceback.print_exc(file=sys.stderr)
        if logger is not None:
            await logger.error("TaxoNERD preload failed", exc_info=True)
