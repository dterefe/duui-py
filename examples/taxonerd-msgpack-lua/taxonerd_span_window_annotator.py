from __future__ import annotations

import asyncio
import queue
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from functools import lru_cache
from time import time
from typing import Any

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
from duui_py.models.uima import FeatureStructure, sofa_kind, sofa_text_value
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.types import (
    Div,
    Paragraph,
    Sentence,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.ocr.types import (
    OCRParagraph,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.ocr.abbyy.types import (
    Paragraph_ocr_abbyy_Paragraph,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.paper.types import (
    Section,
    Title,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.type.types import Taxon
from duui_py.telemetry import telemetry

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
    "taxref": "taxref",
    "ncbi": "ncbi_taxonomy",
    "ncbi_taxonomy": "ncbi_taxonomy",
    "ncbi_lite": "ncbi_taxonomy_lite",
    "ncbi_taxonomy_lite": "ncbi_taxonomy_lite",
    "none": None,
    "": None,
}
SENTENCE_TYPE = Sentence.model_fields["type"].default
PARAGRAPH_TYPE = Paragraph.model_fields["type"].default
DIV_TYPE = Div.model_fields["type"].default
SECTION_TYPE = Section.model_fields["type"].default
TITLE_TYPE = Title.model_fields["type"].default
OCR_PARAGRAPH_TYPE = OCRParagraph.model_fields["type"].default
ABBYY_PARAGRAPH_TYPE = Paragraph_ocr_abbyy_Paragraph.model_fields["type"].default
SPAN_TYPE_ALIASES = {
    "sentence": SENTENCE_TYPE,
    "paragraph": PARAGRAPH_TYPE,
    "div": DIV_TYPE,
    "section": SECTION_TYPE,
    "title": TITLE_TYPE,
    "ocr_paragraph": OCR_PARAGRAPH_TYPE,
    "ocrparagraph": OCR_PARAGRAPH_TYPE,
    "abbyy_paragraph": ABBYY_PARAGRAPH_TYPE,
    "abbyyparagraph": ABBYY_PARAGRAPH_TYPE,
}
DEFAULT_SPAN_PRIORITY = (
    SENTENCE_TYPE,
    PARAGRAPH_TYPE,
    OCR_PARAGRAPH_TYPE,
    ABBYY_PARAGRAPH_TYPE,
    DIV_TYPE,
    SECTION_TYPE,
    TITLE_TYPE,
)


@dataclass(frozen=True)
class TextWindow:
    begin: int
    end: int
    text: str
    source_type: str
    source_count: int


def _parameter(
    parameters: dict[str, object], *names: str, default: object = None
) -> object:
    for name in names:
        value = parameters.get(name)
        if value is not None:
            return value
    return default


def _model_name(value: object | None) -> str:
    configured = str(value or "en_ner_eco_md")
    model = TAXONERD_MODELS.get(configured)
    if model is None:
        unprocessable(
            "Unsupported TaxoNERD model.",
            model=configured,
            supported=sorted(TAXONERD_MODELS),
        )
    return model


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
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _span_types(value: object | None) -> tuple[str, ...]:
    if value is None:
        return DEFAULT_SPAN_PRIORITY
    if isinstance(value, str):
        raw = [item.strip() for item in value.split(",")]
    elif isinstance(value, (list, tuple, set)):
        raw = [str(item).strip() for item in value]
    else:
        raw = [str(value).strip()]
    out: list[str] = []
    for item in raw:
        if not item:
            continue
        out.append(SPAN_TYPE_ALIASES.get(item.lower(), item))
    return tuple(dict.fromkeys(out)) or DEFAULT_SPAN_PRIORITY


def _valid_span(fs: FeatureStructure, text_len: int) -> tuple[int, int, str] | None:
    if fs.begin is None or fs.end is None:
        return None
    begin = max(0, int(fs.begin))
    end = min(text_len, int(fs.end))
    if begin >= end:
        return None
    return (begin, end, fs.type)


def _select_spans(
    items: list[FeatureStructure], text_len: int, preferred_types: tuple[str, ...]
) -> list[tuple[int, int, str]]:
    by_type: dict[str, list[tuple[int, int, str]]] = {}
    preferred = set(preferred_types)
    for item in items:
        if item.type not in preferred:
            continue
        span = _valid_span(item, text_len)
        if span is None:
            continue
        by_type.setdefault(item.type, []).append(span)

    for span_type in preferred_types:
        spans = sorted(set(by_type.get(span_type, [])))
        if spans:
            return spans
    return [(0, text_len, "document")] if text_len else []


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
                text.rfind("\n", cursor, hard_end), text.rfind(" ", cursor, hard_end)
            )
            if split_at > cursor + max_chars // 2:
                hard_end = split_at
        chunk = text[cursor:hard_end]
        if chunk.strip():
            yield TextWindow(cursor, hard_end, chunk, source_type, 1)
        if hard_end >= end:
            break
        cursor = max(cursor + 1, hard_end - overlap_chars)


def _feature_windows(
    items: list[FeatureStructure],
    preferred_types: tuple[str, ...],
    max_chars: int,
    overlap_chars: int,
) -> Iterator[TextWindow]:
    preferred = set(preferred_types)
    selected = [
        item
        for item in items
        if item.type in preferred
        and item.begin is not None
        and item.end is not None
        and item.end > item.begin
    ]
    by_type: dict[str, list[FeatureStructure]] = {}
    for item in selected:
        by_type.setdefault(item.type, []).append(item)

    spans: list[FeatureStructure] = []
    for span_type in preferred_types:
        spans = sorted(
            by_type.get(span_type, []),
            key=lambda item: (item.begin or 0, item.end or 0),
        )
        if spans:
            break

    for item in spans:
        covered = item.features.get("coveredText")
        if not isinstance(covered, str):
            continue
        base = int(item.begin or 0)
        cursor = 0
        covered_len = len(covered)
        while cursor < covered_len:
            hard_end = min(covered_len, cursor + max_chars)
            if hard_end < covered_len:
                split_at = max(
                    covered.rfind("\n", cursor, hard_end),
                    covered.rfind(" ", cursor, hard_end),
                )
                if split_at > cursor + max_chars // 2:
                    hard_end = split_at
            chunk = covered[cursor:hard_end]
            if chunk.strip():
                yield TextWindow(
                    base + cursor,
                    base + hard_end,
                    chunk,
                    item.type,
                    1,
                )
            if hard_end >= covered_len:
                break
            cursor = max(cursor + 1, hard_end - overlap_chars)


def _windows(
    text: str,
    spans: list[tuple[int, int, str]],
    max_chars: int,
    overlap_chars: int,
    merge_spans: bool,
) -> Iterator[TextWindow]:
    if not merge_spans:
        for begin, end, source_type in spans:
            if end - begin > max_chars:
                yield from _split_long_range(
                    text, begin, end, max_chars, overlap_chars, source_type
                )
                continue
            chunk = text[begin:end]
            if chunk.strip():
                yield TextWindow(begin, end, chunk, source_type, 1)
        return

    current_begin: int | None = None
    current_end: int | None = None
    current_type = ""
    current_count = 0

    for begin, end, source_type in spans:
        if end - begin > max_chars:
            if current_begin is not None and current_end is not None:
                yield TextWindow(
                    current_begin,
                    current_end,
                    text[current_begin:current_end],
                    current_type,
                    current_count,
                )
                current_begin = current_end = None
                current_count = 0
            yield from _split_long_range(
                text, begin, end, max_chars, overlap_chars, source_type
            )
            continue

        if current_begin is None or current_end is None:
            current_begin = begin
            current_end = end
            current_type = source_type
            current_count = 1
            continue

        if end - current_begin <= max_chars:
            current_end = max(current_end, end)
            current_count += 1
            if source_type != current_type:
                current_type = "mixed"
            continue

        yield TextWindow(
            current_begin,
            current_end,
            text[current_begin:current_end],
            current_type,
            current_count,
        )
        current_begin = begin
        current_end = end
        current_type = source_type
        current_count = 1

    if current_begin is not None and current_end is not None:
        yield TextWindow(
            current_begin,
            current_end,
            text[current_begin:current_end],
            current_type,
            current_count,
        )


@lru_cache(maxsize=4)
def _load_taxonerd_nlp(
    model: str,
    linker: str | None,
    prefer_gpu: bool,
    with_abbrev: bool,
    threshold: float,
    neighbours: int,
    ner_only: bool,
):
    try:
        from taxonerd import TaxoNERD
    except Exception as exc:
        unavailable(
            "TaxoNERD is not installed in this runtime.", exception=type(exc).__name__
        )

    exclude: list[str] = []
    if ner_only and linker is None:
        exclude.extend(["tagger", "attribute_ruler", "lemmatizer", "parser"])
        if not with_abbrev:
            exclude.extend(["pysbd_sentencizer", "taxo_abbrev_detector"])
    elif not with_abbrev:
        exclude.append("taxo_abbrev_detector")

    taxonerd = TaxoNERD(prefer_gpu=prefer_gpu, verbose=True)
    return taxonerd.load(
        model=model,
        exclude=exclude,
        linker=linker,
        neighbours=neighbours,
        threshold=threshold,
    )


def _load_taxonerd_nlp_with_fallback(
    model: str,
    linker: str | None,
    prefer_gpu: bool,
    with_abbrev: bool,
    threshold: float,
    neighbours: int,
    ner_only: bool,
) -> tuple[Any, str | None, bool, str | None]:
    try:
        return (
            _load_taxonerd_nlp(
                model,
                linker,
                prefer_gpu,
                with_abbrev,
                threshold,
                neighbours,
                ner_only,
            ),
            linker,
            False,
            None,
        )
    except Exception as exc:
        unavailable(
            "TaxoNERD model/linker could not be loaded.",
            model=model,
            linker=linker or "none",
            exception=type(exc).__name__,
            detail=str(exc),
        )


def _links_from_ent(ent: Any) -> list[dict[str, object]]:
    try:
        raw = ent._.kb_ents
    except Exception:
        raw = None
    if not raw:
        return []

    links: list[dict[str, object]] = []
    for value in raw:
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


def _taxon_from_ent(ent: Any, window: TextWindow, linker: str | None) -> Taxon | None:
    if ent.label_ != "LIVB":
        return None
    covered = window.text[ent.start_char : ent.end_char]
    if "\n" in covered.strip("\n"):
        return None
    links = _links_from_ent(ent)
    if linker and not links:
        return None
    begin = window.begin + int(ent.start_char)
    end = window.begin + int(ent.end_char)
    identifier = links[0]["id"] if links else None
    return Taxon(
        begin=begin,
        end=end,
        value=covered.replace("\n", " "),
        identifier=str(identifier) if identifier is not None else None,
    )


def _iter_taxa(
    nlp: Any,
    windows: list[TextWindow],
    linker: str | None,
    batch_size: int,
) -> Iterator[Taxon]:
    seen: set[tuple[int, int, str, str | None]] = set()
    docs = nlp.pipe((window.text for window in windows), batch_size=batch_size)
    for window, doc in zip(windows, docs, strict=False):
        for ent in doc.ents:
            taxon = _taxon_from_ent(ent, window, linker)
            if taxon is None:
                continue
            key = (taxon.begin, taxon.end, taxon.value or "", taxon.identifier)
            if key in seen:
                continue
            seen.add(key)
            yield taxon


async def _iter_taxa_threaded(
    nlp: Any,
    windows: list[TextWindow],
    linker: str | None,
    batch_size: int,
) -> AsyncIterator[Taxon]:
    out: queue.Queue[object] = queue.Queue(maxsize=128)
    sentinel = object()

    def run() -> None:
        try:
            for taxon in _iter_taxa(nlp, windows, linker, batch_size):
                out.put(taxon)
        except BaseException as exc:  # noqa: BLE001
            out.put(exc)
        finally:
            out.put(sentinel)

    worker = asyncio.create_task(asyncio.to_thread(run))
    try:
        while True:
            item = await asyncio.to_thread(out.get)
            if item is sentinel:
                break
            if isinstance(item, BaseException):
                raise item
            yield item
    finally:
        await worker


class TaxoNERDSpanWindowAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(
            meta={
                "source": "TTLab-UIMA/taxoNERD migration; span-window experimental variant"
            }
        ),
        descriptor=AnnotatorDescriptor(
            name="taxonerd-span-window-msgpack-lua",
            version="1.0.0",
            input=IODescriptor(
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    ),
                ),
                annotation=DomainSpec(
                    default=Domain(
                        mimeType="application/x-uima-annotation-spans",
                        languages=["x-unspecified"],
                        types={"Sentence": [SENTENCE_TYPE]},
                    ),
                    aliases={
                        "paragraph": Domain(
                            mimeType="application/x-uima-annotation-spans",
                            languages=["x-unspecified"],
                            types={"Paragraph": [PARAGRAPH_TYPE]},
                        ),
                        "ocr_paragraph": Domain(
                            mimeType="application/x-uima-annotation-spans",
                            languages=["x-unspecified"],
                            types={"OCRParagraph": [OCR_PARAGRAPH_TYPE]},
                        ),
                        "abbyy_paragraph": Domain(
                            mimeType="application/x-uima-annotation-spans",
                            languages=["x-unspecified"],
                            types={"AbbyyParagraph": [ABBYY_PARAGRAPH_TYPE]},
                        ),
                        "div": Domain(
                            mimeType="application/x-uima-annotation-spans",
                            languages=["x-unspecified"],
                            types={"Div": [DIV_TYPE]},
                        ),
                        "section": Domain(
                            mimeType="application/x-uima-annotation-spans",
                            languages=["x-unspecified"],
                            types={"Section": [SECTION_TYPE]},
                        ),
                        "title": Domain(
                            mimeType="application/x-uima-annotation-spans",
                            languages=["x-unspecified"],
                            types={"Title": [TITLE_TYPE]},
                        ),
                    },
                ),
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
            "model": {"type": "string", "default": "en_ner_eco_md"},
            "model_name": {"type": "string"},
            "linking": {"type": "string", "default": "gbif_backbone"},
            "linker_name": {"type": "string"},
            "prefer_gpu": {"type": "boolean", "default": False},
            "with_abbrev": {"type": "boolean", "default": True},
            "threshold": {"type": "number", "default": 0.7},
            "neighbours": {"type": "integer", "default": 10},
            "ner_only": {
                "type": "boolean",
                "default": False,
                "description": "Exclude non-NER pipeline components when no linker is active.",
            },
            "span_types": {
                "type": "array",
                "description": "Preferred UIMA span types or aliases. Defaults to sentence, then paragraph/div/section/title fallback.",
            },
            "max_window_chars": {"type": "integer", "default": 2500},
            "overlap_chars": {"type": "integer", "default": 160},
            "batch_size": {"type": "integer", "default": 8},
            "merge_spans": {
                "type": "boolean",
                "default": False,
                "description": "When false, each selected sentence/span annotation is one nlp.pipe input item.",
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @telemetry.timed("taxonerd_span_window_processing_ms", annotator="taxonerd-span-window")
    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        model = _model_name(_parameter(doc.parameters, "model", "model_name"))
        linker = _linker_name(_parameter(doc.parameters, "linking", "linker_name"))
        prefer_gpu = _bool(
            _parameter(doc.parameters, "prefer_gpu", default=False), False
        )
        with_abbrev = _bool(
            _parameter(doc.parameters, "with_abbrev", default=True), True
        )
        threshold = _float(doc.parameters.get("threshold"), 0.7)
        neighbours = _int(doc.parameters.get("neighbours"), 10)
        ner_only = _bool(doc.parameters.get("ner_only"), False)
        max_window_chars = _int(
            doc.parameters.get("max_window_chars"), 2500, minimum=256
        )
        overlap_chars = _int(doc.parameters.get("overlap_chars"), 160, minimum=0)
        batch_size = _int(doc.parameters.get("batch_size"), 8)
        merge_spans = _bool(doc.parameters.get("merge_spans"), False)

        text = sofa_text_value(doc.sofa) or ""
        preferred_span_types = _span_types(doc.parameters.get("span_types"))
        if sofa_kind(doc.sofa) == "annotation_spans":
            spans = []
            windows = list(
                _feature_windows(
                    doc.fs, preferred_span_types, max_window_chars, overlap_chars
                )
            )
        else:
            if not text:
                unprocessable("TaxoNERD span-window variant requires text input.")
            spans = _select_spans(doc.fs, len(text), preferred_span_types)
            windows = list(
                _windows(text, spans, max_window_chars, overlap_chars, merge_spans)
            )
        if not windows:
            unprocessable(
                "No usable TaxoNERD input windows were found for the selected input domain."
            )
        await telemetry.trace(
            "TaxoNERD span-window processing started",
            model=model,
            linker=linker,
            text_length=len(text),
            spans=len(spans),
            windows=len(windows),
            merge_spans=merge_spans,
            batch_size=batch_size,
            max_window_chars=max_window_chars,
        )

        nlp, effective_linker, linker_fallback, linker_error = await asyncio.to_thread(
            _load_taxonerd_nlp_with_fallback,
            model,
            linker,
            prefer_gpu,
            with_abbrev,
            threshold,
            neighbours,
            ner_only,
        )
        if linker_fallback:
            await telemetry.warning(
                "TaxoNERD span-window linker unavailable; continuing with NER-only output",
                requested_linker=linker or "none",
                effective_linker=effective_linker or "none",
                model=model,
                error=linker_error or "",
            )

        matches = 0
        batch = []
        async for taxon in _iter_taxa_threaded(
            nlp, windows, effective_linker, batch_size
        ):
            matches += 1
            batch.append(taxon)
            if len(batch) >= 512:
                yield batch
                batch = []
        if batch:
            yield batch

        elapsed_ms = int((time() - started) * 1000)
        await telemetry.count(
            "taxonerd_span_window_taxon_matches",
            matches,
            linking=effective_linker or "none",
            model=model,
            fallback=str(linker_fallback).lower(),
        )
        await telemetry.count("taxonerd_span_window_windows", len(windows), model=model)
        await telemetry.count(
            "taxonerd_span_window_source_spans", len(spans), model=model
        )
        await telemetry.debug(
            "TaxoNERD span-window processing completed",
            matches=matches,
            windows=len(windows),
            elapsed_ms=elapsed_ms,
            linker_fallback=linker_fallback,
            effective_linker=effective_linker or "none",
        )
        yield AnnotatorMetaData(
            name=self.config.descriptor.name,
            version=self.config.descriptor.version,
            modelName=model,
            modelVersion="span-window",
        )
        yield DocumentModification(
            user=self.config.descriptor.name,
            timestamp=int(time()),
            comment=f"{self.config.descriptor.name} TaxoNERD model={model} linker={effective_linker or 'none'} windows={len(windows)} fallback={linker_fallback}",
        )


app = create_app(
    TaxoNERDSpanWindowAnnotator, request_adapter=AsyncChunkedRequestAdapter()
)
