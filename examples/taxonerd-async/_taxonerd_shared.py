"""Shared TaxoNERD runtime for the two DUUI-Py TaxoNERD annotators.

Only the Abrami TaxoNERD fork is accepted. Both annotators run the same
``find_in_text`` TaxoNERD procedure so DUUI-core evaluation compares the old
Lua/JSON transport against the msgpack-Lua transport without changing the model
or linker semantics.
"""

from __future__ import annotations

import functools
import os
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from duui_py.models.uima import Annotation
from duui_py.models.uima_typesystem.texttechnologylab.annotation.type.types import Taxon

_ABRAMI_SOURCE_ROOT = Path(
    os.environ.get(
        "DUUI_TAXONERD_SOURCE_ROOT",
        "/storage/projects/BIOfid/code/dterefe/taxonerd-abrami",
    )
).resolve()

LINK_ID_FEATURE = "_taxonerd_link_id"
LINK_VALUE_FEATURE = "_taxonerd_link_value"
LINK_SCORE_FEATURE = "_taxonerd_link_score"
NER_LABEL_FEATURE = "_taxonerd_ner_label"

TAXON_TYPE = "org.texttechnologylab.annotation.type.Taxon"
ANNOTATION_COMMENT_TYPE = "org.texttechnologylab.annotation.AnnotationComment"

_MODEL_REGISTRY: dict[tuple[object, ...], tuple[Any, float]] = {}
_MODEL_REGISTRY_LOCK = threading.Lock()


@dataclass(frozen=True)
class StrategyResult:
    taxons: list[Taxon]
    windows: int = 0
    mentions: int = 0
    metrics: dict[str, float] = field(default_factory=dict)


def assert_abrami_taxonerd_source() -> Path:
    """Require the runtime TaxoNERD package to come from the Abrami fork clone."""
    try:
        import taxonerd  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "TaxoNERD is not installed. Install the Abrami fork into the dterefe venv."
        ) from exc
    source = Path(getattr(taxonerd, "__file__", "")).resolve()
    if not source.is_relative_to(_ABRAMI_SOURCE_ROOT):
        raise RuntimeError(
            "TaxoNERD must be imported from the Abrami fork clone "
            f"at {_ABRAMI_SOURCE_ROOT}; imported {source}."
        )
    return source


@functools.lru_cache(maxsize=4)
def load_taxonerd(
    model: str,
    linker: str | None,
    threshold: float,
    exclude: tuple[str, ...],
    prefer_gpu: bool,
) -> Any:
    """Load one Abrami TaxoNERD runtime and keep it in memory for the process."""
    assert_abrami_taxonerd_source()
    cache_key = (model, linker, round(float(threshold), 6), tuple(sorted(exclude)), prefer_gpu)
    with _MODEL_REGISTRY_LOCK:
        existing = _MODEL_REGISTRY.get(cache_key)
        if existing is not None:
            return existing[0]

    from taxonerd import TaxoNERD  # type: ignore[import-untyped]

    ner = TaxoNERD(prefer_gpu=prefer_gpu)
    ner.load(model=model, exclude=list(exclude), linker=linker, threshold=threshold)
    nlp = getattr(ner, "nlp", None)
    if nlp is None or "ner" not in getattr(nlp, "pipe_names", []):
        raise RuntimeError(f"TaxoNERD requires a spaCy NER model with a LIVB label (model={model}).")

    with _MODEL_REGISTRY_LOCK:
        _MODEL_REGISTRY[cache_key] = (ner, time.time())
    return ner


def dedupe_taxons(taxons: Iterator[Taxon]) -> list[Taxon]:
    seen: set[tuple[int, int, str, str | None]] = set()
    out: list[Taxon] = []
    for taxon in taxons:
        key = (taxon.begin, taxon.end, taxon.value or "", taxon.identifier)
        if key not in seen:
            seen.add(key)
            out.append(taxon)
    return out


def legacy_surface_taxons_and_comments(taxons: list[Taxon]) -> tuple[list[Annotation], list[Any]]:
    """Build the same CAS-visible Taxon/AnnotationComment surface as legacy Lua."""
    from duui_py.models.uima_typesystem.texttechnologylab.annotation.types import (
        AnnotationComment,
    )

    annotations: list[Annotation] = []
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
        reference = {"$ref": int(taxon.ref)}
        annotations.append(Annotation(
            type=TAXON_TYPE,
            ref=taxon.ref,
            begin=taxon.begin,
            end=taxon.end,
            features={},
        ))
        comments.extend([
            AnnotationComment(reference=reference, key="link", value=link_id),
            AnnotationComment(reference=reference, key="identified_as", value=link_value),
            AnnotationComment(reference=reference, key="similarity", value=link_score),
            AnnotationComment(reference=reference, key="unknown", value=ner_label),
        ])
    return annotations, comments


def legacy_annotation_comments(taxons: list[Taxon]) -> list[Any]:
    """Build AnnotationComment list preserving legacy reference links."""
    _, comments = legacy_surface_taxons_and_comments(taxons)
    return comments


def run_legacy_procedure(
    text: str,
    model: str,
    linker: str | None,
    threshold: float,
    exclude: tuple[str, ...],
    prefer_gpu: bool,
) -> StrategyResult:
    """Run Abrami TaxoNERD ``find_in_text`` and convert rows to UIMA Taxon FSs."""
    load_started = time.time()
    taxonerd = load_taxonerd(model, linker, threshold, exclude, prefer_gpu)
    load_ms = (time.time() - load_started) * 1000.0

    ner_started = time.time()
    try:
        rows = taxonerd.find_in_text(text).values.tolist()
    except Exception as exc:
        raise RuntimeError(f"TaxoNERD legacy procedure failed: {exc}") from exc
    ner_ms = (time.time() - ner_started) * 1000.0

    taxons = dedupe_taxons(_taxon_from_legacy_row(row, text) for row in rows)
    linker_metrics: dict[str, float] = {}
    nlp = getattr(taxonerd, "nlp", None)
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

    return StrategyResult(taxons, windows=1, mentions=len(taxons), metrics={
        "model_load_ms": load_ms,
        "ner_ms": ner_ms,
        **linker_metrics,
    })


def _taxon_from_legacy_row(row: list[object], text: str) -> Taxon:
    if len(row) < 2:
        raise ValueError(f"TaxoNERD returned a malformed row: {row}")
    marker = str(row[0]).split()
    if len(marker) < 3:
        raise ValueError(f"TaxoNERD returned a malformed span marker: {row[0]}")

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
        begin=begin,
        end=end,
        value=value,
        identifier=str(identifier) if identifier is not None else None,
        features={
            LINK_ID_FEATURE: str(identifier) if identifier is not None else "",
            LINK_VALUE_FEATURE: str(links[0].get("value")) if links and links[0].get("value") else "",
            LINK_SCORE_FEATURE: str(links[0].get("probability")) if links and links[0].get("probability") else "",
            NER_LABEL_FEATURE: marker[0] if marker else "LIVB",
        },
    )
