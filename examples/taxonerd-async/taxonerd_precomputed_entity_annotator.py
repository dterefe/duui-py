from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from functools import lru_cache
from time import time

from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import unavailable, unprocessable
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
from duui_py.models.uima import FeatureStructure, sofa_text_value
from duui_py.models.uima_typesystem.texttechnologylab.annotation.type.types import Taxon
from duui_py.telemetry import telemetry

TAXONERD_LINKERS = {
    "gbif": "gbif_backbone",
    "gbif_backbone": "gbif_backbone",
    "taxref": "taxref",
    "ncbi": "ncbi_taxonomy",
    "ncbi_taxonomy": "ncbi_taxonomy",
    "ncbi_lite": "ncbi_taxonomy_lite",
    "ncbi_taxonomy_lite": "ncbi_taxonomy_lite",
    "none": None,
    "": None,
}
DEFAULT_ENTITY_TYPES = (
    "org.texttechnologylab.annotation.NamedEntity",
    "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity",
    "org.texttechnologylab.annotation.type.Taxon",
    "org.texttechnologylab.annotation.type.TexttechnologyNamedEntity",
)


@dataclass(frozen=True)
class Mention:
    begin: int
    end: int
    text: str
    source_type: str
    source_ref: int | None
    source_label: str | None


def _parameter(
    parameters: dict[str, object], *names: str, default: object = None
) -> object:
    for name in names:
        value = parameters.get(name)
        if value is not None:
            return value
    return default


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


def _int(value: object, default: int, minimum: int = 1) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, parsed)


def _float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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


def _label(fs: FeatureStructure) -> str | None:
    for key in ("value", "identifier", "label", "entityType", "nerValue", "category"):
        value = fs.features.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _valid_mention(
    fs: FeatureStructure,
    text: str,
    accepted_types: set[str],
    accepted_labels: set[str],
) -> Mention | None:
    if fs.type not in accepted_types or fs.begin is None or fs.end is None:
        return None
    begin = max(0, int(fs.begin))
    end = min(len(text), int(fs.end))
    if begin >= end:
        return None
    covered = text[begin:end].strip()
    if not covered:
        return None
    label = _label(fs)
    if accepted_labels and label not in accepted_labels:
        return None
    return Mention(
        begin=begin,
        end=end,
        text=text[begin:end].replace("\n", " "),
        source_type=fs.type,
        source_ref=fs.ref,
        source_label=label,
    )


def _mentions(
    items: list[FeatureStructure],
    text: str,
    entity_types: tuple[str, ...],
    entity_labels: tuple[str, ...],
) -> list[Mention]:
    accepted_types = set(entity_types)
    accepted_labels = set(entity_labels)
    seen: set[tuple[int, int, str]] = set()
    out: list[Mention] = []
    for item in items:
        mention = _valid_mention(item, text, accepted_types, accepted_labels)
        if mention is None:
            continue
        key = (mention.begin, mention.end, mention.text)
        if key in seen:
            continue
        seen.add(key)
        out.append(mention)
    return out


@lru_cache(maxsize=4)
def _candidate_generator(linker: str):
    try:
        from taxonerd.linking.candidate_generation import CandidateGenerator
    except Exception as exc:
        unavailable(
            "TaxoNERD linker runtime is not available.",
            exception=type(exc).__name__,
        )
    return CandidateGenerator(name_or_path=linker)


def _link_mentions(
    mentions: list[Mention],
    linker: str | None,
    neighbours: int,
    threshold: float,
) -> dict[str, list[dict[str, object]]]:
    if linker is None:
        return {}
    names = sorted({mention.text.lower() for mention in mentions})
    if not names:
        return {}
    generator = _candidate_generator(linker)
    raw_links: dict[str, list[tuple[object, object, float]]] = {}
    for name, candidates in zip(names, generator(names, neighbours), strict=False):
        predicted = []
        for candidate in candidates:
            score = max(candidate.similarities) if candidate.similarities else 0.0
            if score > threshold:
                predicted.append((candidate.concept_id, candidate.aliases[0], score))
        sorted_predicted = sorted(predicted, reverse=True, key=lambda item: item[2])
        if sorted_predicted:
            max_score = sorted_predicted[0][2]
            raw_links[name] = [
                item for item in sorted_predicted[:5] if item[2] == max_score
            ]
        else:
            raw_links[name] = []
    return {
        name: [
            {"id": str(concept_id), "value": str(alias), "probability": float(score)}
            for concept_id, alias, score in raw_links.get(name, [])
        ]
        for name in names
    }


def _link_mentions_with_fallback(
    mentions: list[Mention],
    linker: str | None,
    neighbours: int,
    threshold: float,
) -> tuple[dict[str, list[dict[str, object]]], str | None, bool, str | None]:
    try:
        return _link_mentions(mentions, linker, neighbours, threshold), linker, False, None
    except Exception as exc:
        if linker is not None:
            unavailable(
                "TaxoNERD GBIF backbone linking failed.",
                linker=linker,
                exception=type(exc).__name__,
                detail=str(exc),
            )
        raise


def _taxon(mention: Mention, linker: str | None, links: list[dict[str, object]]) -> Taxon:
    identifier = links[0]["id"] if links else None
    return Taxon(
        begin=mention.begin,
        end=mention.end,
        value=mention.text,
        identifier=str(identifier) if identifier is not None else None,
    )


class TaxoNERDPrecomputedEntityAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(
            meta={
                "source": "TTLab-UIMA/taxoNERD precomputed entity linker prototype"
            }
        ),
        descriptor=AnnotatorDescriptor(
            name="taxonerd-precomputed-entity-linker-msgpack-lua",
            version="0.1.0",
            input=IODescriptor(
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
                types={"NamedEntity": list(DEFAULT_ENTITY_TYPES)},
            ),
            output=IODescriptor(
                types={"Taxon": ["org.texttechnologylab.annotation.type.Taxon"]},
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
            "linking": {"type": "string", "default": "gbif_backbone"},
            "linker_name": {"type": "string"},
            "threshold": {"type": "number", "default": 0.7},
            "neighbours": {"type": "integer", "default": 10},
            "entity_types": {
                "type": "array",
                "description": "UIMA entity types to reuse as candidate taxon mentions.",
            },
            "entity_labels": {
                "type": "array",
                "description": "Optional accepted label/value names. Empty means accept all configured entity types.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @telemetry.timed("taxonerd_precomputed_entity_processing_ms", annotator="taxonerd-precomputed-entity")
    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        if not text:
            unprocessable("TaxoNERD precomputed-entity linker requires text input.")

        linker = _linker_name(_parameter(doc.parameters, "linking", "linker_name"))
        threshold = _float(_parameter(doc.parameters, "threshold", default=0.7), 0.7)
        neighbours = _int(doc.parameters.get("neighbours"), 10)
        entity_types = _csv(doc.parameters.get("entity_types"), DEFAULT_ENTITY_TYPES)
        entity_labels = _csv(doc.parameters.get("entity_labels"), ())
        mentions = _mentions(doc.fs, text, entity_types, entity_labels)
        await telemetry.trace(
            "TaxoNERD precomputed-entity linking started",
            linker=linker,
            threshold=threshold,
            neighbours=neighbours,
            entity_types=list(entity_types),
            entity_labels=list(entity_labels),
            candidate_mentions=len(mentions),
        )

        links_by_name, effective_linker, linker_fallback, linker_error = (
            await asyncio.to_thread(
                _link_mentions_with_fallback, mentions, linker, neighbours, threshold
            )
        )
        if linker_fallback:
            await telemetry.warning(
                "TaxoNERD precomputed-entity linker unavailable; emitting candidate mentions without links",
                requested_linker=linker or "none",
                effective_linker=effective_linker or "none",
                error=linker_error or "",
                candidate_mentions=len(mentions),
            )
        emitted = 0
        linked_mentions = 0
        batch = []
        for mention in mentions:
            links = links_by_name.get(mention.text.lower(), [])
            if effective_linker and not links:
                continue
            emitted += 1
            if links:
                linked_mentions += 1
            batch.append(_taxon(mention, effective_linker, links))
            if len(batch) >= 512:
                yield batch
                batch = []
        if batch:
            yield batch

        elapsed_ms = int((time() - started) * 1000)
        await telemetry.count(
            "taxonerd_precomputed_entity_candidates",
            len(mentions),
            linking=effective_linker or "none",
            fallback=str(linker_fallback).lower(),
        )
        await telemetry.count(
            "taxonerd_precomputed_entity_taxon_matches",
            emitted,
            linking=effective_linker or "none",
            fallback=str(linker_fallback).lower(),
        )
        await telemetry.count(
            "taxonerd_precomputed_entity_linked_mentions",
            linked_mentions,
            linking=effective_linker or "none",
            fallback=str(linker_fallback).lower(),
        )
        await telemetry.debug(
            "TaxoNERD precomputed-entity linking completed",
            candidate_mentions=len(mentions),
            emitted=emitted,
            linked_mentions=linked_mentions,
            elapsed_ms=elapsed_ms,
            linker_fallback=linker_fallback,
            effective_linker=effective_linker or "none",
        )
        yield AnnotatorMetaData(
            name=self.config.descriptor.name,
            version=self.config.descriptor.version,
            modelName=effective_linker or "none",
            modelVersion="precomputed-entity-linker",
        )
        yield DocumentModification(
            user=self.config.descriptor.name,
            timestamp=int(time()),
            comment=f"{self.config.descriptor.name} linker={effective_linker or 'none'} candidates={len(mentions)} emitted={emitted} fallback={linker_fallback}",
        )


app = create_app(
    TaxoNERDPrecomputedEntityAnnotator, request_adapter=AsyncChunkedRequestAdapter()
)
