from __future__ import annotations
import asyncio
import queue
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from functools import lru_cache
from time import time
from typing import Any
import json
from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import unavailable, unprocessable
from duui_py.telemetry import telemetry
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
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.types import (
    MorphologicalFeatures,
)
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.types import (
    POS,
)
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.ner.type.types import (
    NamedEntity,
)
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.types import (
    Div,
    Lemma,
    Paragraph,
    Sentence,
    Token,
)
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.types import (
    Dependency,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.ocr.types import (
    OCRParagraph,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.paper.types import (
    Section,
    Title,
)

SPACY_MODELS = {
    "efficiency": {
        "de": "de_core_news_sm",
        "en": "en_core_web_sm",
        "xx": "xx_ent_wiki_sm",
    },
    "accuracy": {"de": "de_dep_news_trf", "en": "en_core_web_trf"},
    "trf": {"de": "de_dep_news_trf", "en": "en_core_web_trf"},
    "sm": {"de": "de_core_news_sm", "en": "en_core_web_sm"},
}
VARIANT_OUTPUTS = {
    "": {
        "tokenizer",
        "sentencizer",
        "lemmatizer",
        "tagger",
        "morphologizer",
        "parser",
        "ner",
    },
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
SENTENCE_TYPE = Sentence.model_fields["type"].default
PARAGRAPH_TYPE = Paragraph.model_fields["type"].default
DIV_TYPE = Div.model_fields["type"].default
SECTION_TYPE = Section.model_fields["type"].default
TITLE_TYPE = Title.model_fields["type"].default
OCR_PARAGRAPH_TYPE = OCRParagraph.model_fields["type"].default
SPAN_TYPE_ALIASES = {
    "sentence": SENTENCE_TYPE,
    "paragraph": PARAGRAPH_TYPE,
    "div": DIV_TYPE,
    "section": SECTION_TYPE,
    "title": TITLE_TYPE,
    "ocr_paragraph": OCR_PARAGRAPH_TYPE,
    "ocrparagraph": OCR_PARAGRAPH_TYPE,
}
DEFAULT_SPAN_PRIORITY = (
    SENTENCE_TYPE,
    PARAGRAPH_TYPE,
    OCR_PARAGRAPH_TYPE,
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
            decoded = [
                item.strip() for item in text.strip("[]").split(",") if item.strip()
            ]
        value = decoded
    if isinstance(value, (list, tuple, set)):
        return {
            str(item).strip().strip("\"'").lower()
            for item in value
            if str(item).strip()
        }
    return {str(value).strip().lower()}


def _language(doc: V1RequestEnvelope) -> str:
    for key in ("spacy_language", "language", "lang"):
        value = doc.parameters.get(key)
        if value:
            return str(value)
    return getattr(doc.sofa, "language", None) or "de"


def _model_name(doc: V1RequestEnvelope) -> str:
    for key in ("model_name", "spacy_model", "single_model"):
        value = doc.parameters.get(key)
        if value:
            return str(value)
    language = _language(doc)
    variant = str(
        doc.parameters.get("model_variant")
        or doc.parameters.get("spacy_model_size")
        or "efficiency"
    )
    if variant not in SPACY_MODELS:
        unprocessable(
            "Unsupported spaCy model variant.",
            variant=variant,
            supported=sorted(SPACY_MODELS),
        )
    if language not in SPACY_MODELS[variant]:
        if "xx" in SPACY_MODELS[variant]:
            language = "xx"
        else:
            unprocessable(
                "Unsupported spaCy language for variant.",
                language=language,
                variant=variant,
            )
    return SPACY_MODELS[variant][language]


def _outputs(parameters: dict[str, object]) -> set[str]:
    variant = str(
        parameters.get("variant") or ""
    )
    outputs = set(VARIANT_OUTPUTS.get(variant, VARIANT_OUTPUTS[""]))
    outputs.difference_update(_parse_exclude(parameters.get("exclude")))
    return outputs


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
        if item:
            out.append(SPAN_TYPE_ALIASES.get(item.lower(), item))
    return tuple(dict.fromkeys(out)) or DEFAULT_SPAN_PRIORITY


def _int(value: object, default: int, minimum: int = 1) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, parsed)


@lru_cache(maxsize=4)
def _load_spacy(model_name: str, exclude: tuple[str, ...]) -> Any:
    try:
        import spacy
    except Exception as exc:
        unavailable(
            "spaCy is not installed in this runtime.", exception=type(exc).__name__
        )
    try:
        return spacy.load(model_name, exclude=list(exclude))
    except Exception as exc:
        unavailable(
            "spaCy model could not be loaded.",
            model=model_name,
            exception=type(exc).__name__,
            detail=str(exc),
        )


def _select_spans(
    items: list[FeatureStructure], text_len: int, preferred_types: tuple[str, ...]
) -> list[tuple[int, int, str]]:
    preferred = set(preferred_types)
    by_type: dict[str, list[tuple[int, int, str]]] = {}
    for item in items:
        if item.type not in preferred or item.begin is None or item.end is None:
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
    by_type: dict[str, list[FeatureStructure]] = {}
    for item in items:
        if (
            item.type not in preferred
            or item.begin is None
            or item.end is None
            or item.end <= item.begin
        ):
            continue
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
                yield TextWindow(base + cursor, base + hard_end, chunk, item.type, 1)
            if hard_end >= covered_len:
                break
            cursor = max(cursor + 1, hard_end - overlap_chars)


def _windows(
    text: str,
    spans: list[tuple[int, int, str]],
    max_chars: int,
    overlap_chars: int,
) -> Iterator[TextWindow]:
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


def _iter_annotations(
    spacy_doc: Any,
    outputs: set[str],
    window_begin: int = 0,
    token_order_offset: int = 0,
) -> Iterator[object]:
    token_refs: dict[int, dict[str, int]] = {}
    if "tokenizer" in outputs:
        order = token_order_offset
        for token in spacy_doc:
            if token.is_space:
                continue
            begin = window_begin + token.idx
            end = begin + len(token)
            annotation = Token(begin=begin, end=end, order=order)
            yield annotation
            token_refs[token.i] = {"begin": begin, "end": end}
            order += 1
    if "lemmatizer" in outputs:
        for token in spacy_doc:
            if token.is_space:
                continue
            begin = window_begin + token.idx
            yield Lemma(
                begin=begin,
                end=begin + len(token),
                value=token.lemma_ or token.text,
            )
    if "tagger" in outputs:
        for token in spacy_doc:
            if token.is_space:
                continue
            begin = window_begin + token.idx
            yield POS(
                begin=begin,
                end=begin + len(token),
                PosValue=token.tag_,
                coarseValue=token.pos_,
            )
    if "morphologizer" in outputs:
        for token in spacy_doc:
            if token.is_space:
                continue
            begin = window_begin + token.idx
            yield MorphologicalFeatures(
                begin=begin, end=begin + len(token), value=str(token.morph)
            )
    if "sentencizer" in outputs:
        for sentence in spacy_doc.sents:
            yield Sentence(
                begin=window_begin + sentence.start_char,
                end=window_begin + sentence.end_char,
            )
    if "ner" in outputs:
        for entity in spacy_doc.ents:
            yield NamedEntity(
                begin=window_begin + entity.start_char,
                end=window_begin + entity.end_char,
                value=entity.label_,
            )
    if "parser" in outputs:
        for token in spacy_doc:
            if token.is_space:
                continue
            begin = window_begin + token.idx
            end = begin + len(token)
            dependent = token_refs.get(
                token.i,
                {"begin": begin, "end": end},
            )
            governor = token_refs.get(
                token.head.i,
                {
                    "begin": window_begin + token.head.idx,
                    "end": window_begin + token.head.idx + len(token.head),
                },
            )
            yield Dependency(
                begin=begin,
                end=end,
                DependencyType=token.dep_,
                Dependent=dependent,
                Governor=governor,
                flavor="basic",
            )


def _annotation_key(annotation: object) -> tuple[object, ...]:
    return (
        getattr(annotation, "type", type(annotation).__name__),
        getattr(annotation, "begin", None),
        getattr(annotation, "end", None),
        getattr(annotation, "value", None),
        getattr(annotation, "PosValue", None),
        getattr(annotation, "coarseValue", None),
        getattr(annotation, "DependencyType", None),
    )


def _iter_window_annotations(
    nlp: Any, windows: list[TextWindow], outputs: set[str], batch_size: int
) -> Iterator[object]:
    seen: set[tuple[object, ...]] = set()
    token_order_offset = 0
    docs = nlp.pipe((window.text for window in windows), batch_size=batch_size)
    for window, spacy_doc in zip(windows, docs, strict=False):
        for annotation in _iter_annotations(
            spacy_doc, outputs, window.begin, token_order_offset
        ):
            key = _annotation_key(annotation)
            if key in seen:
                continue
            seen.add(key)
            yield annotation
        token_order_offset += sum(1 for token in spacy_doc if not token.is_space)


async def _iter_window_annotations_threaded(
    nlp: Any, windows: list[TextWindow], outputs: set[str], batch_size: int
) -> AsyncIterator[object]:
    out: queue.Queue[object] = queue.Queue(maxsize=256)
    sentinel = object()

    def run() -> None:
        try:
            for annotation in _iter_window_annotations(
                nlp, windows, outputs, batch_size
            ):
                out.put(annotation)
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


class SpacySpanWindowAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(
            meta={
                "source": "TTLab-UIMA/textimager-uima-spacy migration; span-window experimental variant"
            }
        ),
        descriptor=AnnotatorDescriptor(
            name="spacy-span-window-lua-msgpack",
            version="1.0.0",
            input=IODescriptor(
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
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
                types={
                    "Sentence": [
                        "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
                    ],
                    "Token": [
                        "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"
                    ],
                    "Lemma": [
                        "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma"
                    ],
                    "POS": ["de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"],
                    "MorphologicalFeatures": [
                        "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.MorphologicalFeatures"
                    ],
                    "Dependency": [
                        "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency"
                    ],
                    "NamedEntity": [
                        "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"
                    ],
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
            "span_types": {
                "type": "array",
                "description": "Preferred UIMA span types or aliases. Defaults to sentence, then paragraph/div/section/title fallback.",
            },
            "max_window_chars": {"type": "integer", "default": 2500},
            "overlap_chars": {"type": "integer", "default": 160},
            "batch_size": {"type": "integer", "default": 8},
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @telemetry.timed("spacy_span_window_processing_ms", annotator="spacy-span-window")
    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        model_name = _model_name(doc)
        exclude = _parse_exclude(doc.parameters.get("exclude"))
        outputs = _outputs(doc.parameters)
        max_window_chars = _int(
            doc.parameters.get("max_window_chars"), 2500, minimum=256
        )
        overlap_chars = _int(doc.parameters.get("overlap_chars"), 160, minimum=0)
        batch_size = _int(doc.parameters.get("batch_size"), 8)
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
                unprocessable("spaCy span-window variant requires text input.")
            spans = _select_spans(doc.fs, len(text), preferred_span_types)
            windows = list(_windows(text, spans, max_window_chars, overlap_chars))
        if not windows:
            unprocessable("No usable spaCy input windows were found.")
        await telemetry.trace(
            "spaCy span-window processing started",
            model=model_name,
            exclude=sorted(exclude),
            outputs=sorted(outputs),
            text_length=len(text),
            spans=len(spans),
            windows=len(windows),
            max_window_chars=max_window_chars,
        )
        nlp = await asyncio.to_thread(_load_spacy, model_name, tuple(sorted(exclude)))
        model_meta = getattr(nlp, "meta", {}) or {}
        model_version = str(model_meta.get("version", "runtime"))
        model_lang = str(model_meta.get("lang", "x-unspecified"))
        counts: dict[str, int] = {}
        total = 0
        async for annotation in _iter_window_annotations_threaded(
            nlp, windows, outputs, batch_size
        ):
            counts[annotation.type] = counts.get(annotation.type, 0) + 1
            total += 1
            yield annotation
        elapsed_ms = int((time() - started) * 1000)
        await telemetry.count("spacy_span_window_annotations", total, model=model_name)
        await telemetry.count(
            "spacy_span_window_windows", len(windows), model=model_name
        )
        for annotation_type, count in counts.items():
            await telemetry.count(
                "spacy_span_window_annotations_by_type", count, type=annotation_type
            )
        await telemetry.debug(
            "spaCy span-window processing completed",
            model=model_name,
            annotations=total,
            windows=len(windows),
            elapsed_ms=elapsed_ms,
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
            comment=f"{self.config.descriptor.name} spaCy model={model_name} windows={len(windows)}",
        )


def _spacy_version() -> str | None:
    try:
        import spacy
    except Exception:
        return None
    return str(spacy.__version__)


app = create_app(SpacySpanWindowAnnotator, request_adapter=AsyncChunkedRequestAdapter())
