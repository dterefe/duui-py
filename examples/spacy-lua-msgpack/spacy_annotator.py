from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from time import time
from typing import Any
import json
from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import unavailable, unprocessable
from duui_py.telemetry import telemetry
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    Domain,
    DomainSpec,
    DuuiResult,
    IODescriptor,
    V1RequestEnvelope,
)
from duui_py.models.uima import sofa_text_value, uima_type_name
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
    Lemma,
    Sentence,
    Token,
)
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.types import (
    Dependency,
    ROOT_type_dependency_ROOT,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.types import (
    SpacyAnnotatorMetaData,
)

SPACY_MODELS = {
    "efficiency": {
        "de": "de_core_news_sm",
        "en": "en_core_web_sm",
        "xx": "xx_ent_wiki_sm",
    },
    "accuracy": {"de": "de_dep_news_trf", "en": "en_core_web_trf"},
    "trf": {"de": "de_dep_news_trf", "en": "en_core_web_trf"},
    "full": {"de": "de_dep_news_trf", "en": "en_core_web_trf"},
    "lg": {"de": "de_dep_news_trf", "en": "en_core_web_trf"},
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
    "Definiteness": "definiteness",
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
SENTENCE_TYPE = uima_type_name(Sentence)
TOKEN_TYPE = uima_type_name(Token)
LEMMA_TYPE = uima_type_name(Lemma)
POS_TYPE = uima_type_name(POS)
MORPH_TYPE = uima_type_name(MorphologicalFeatures)
DEPENDENCY_TYPE = uima_type_name(Dependency)
ROOT_TYPE = uima_type_name(ROOT_type_dependency_ROOT)
NAMED_ENTITY_TYPE = uima_type_name(NamedEntity)
SPACY_META_TYPE = uima_type_name(SpacyAnnotatorMetaData)



@dataclass(frozen=True)
class InputAnnotation:
    begin: int
    end: int
    text: str


@dataclass(frozen=True)
class SpacyWindow:
    text: str
    offset: int
    token_annotations: tuple[InputAnnotation, ...] = ()


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
    sofa = getattr(doc, "sofa", None)
    return getattr(sofa, "language", None) or getattr(doc, "language", None) or "de"


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
    variant = str(parameters.get("variant") or "")
    outputs = set(VARIANT_OUTPUTS.get(variant, VARIANT_OUTPUTS[""]))
    outputs.difference_update(_parse_exclude(parameters.get("exclude")))
    return outputs


def _bool(value: object | None, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _int(value: object | None, default: int, minimum: int = 1) -> int:
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


def _input_annotations(doc: V1RequestEnvelope, type_name: str) -> list[InputAnnotation]:
    annotations: list[InputAnnotation] = []
    for fs in doc.fs:
        if fs.type != type_name:
            continue
        covered = fs.feature_map().get("coveredText")
        annotations.append(
            InputAnnotation(
                begin=int(fs.begin or 0),
                end=int(fs.end or 0),
                text=str(covered) if covered is not None else "",
            )
        )
    annotations.sort(key=lambda item: (item.begin, item.end))
    return annotations


def _windows(
    text: str,
    sentence_annotations: list[InputAnnotation],
    token_annotations: list[InputAnnotation],
) -> list[SpacyWindow]:
    if not sentence_annotations:
        return [
            SpacyWindow(
                text=text,
                offset=0,
                token_annotations=tuple(token_annotations),
            )
        ]

    windows: list[SpacyWindow] = []
    token_index = 0
    for sentence in sentence_annotations:
        sentence_tokens: list[InputAnnotation] = []
        while token_index < len(token_annotations) and token_annotations[token_index].end <= sentence.begin:
            token_index += 1
        scan = token_index
        while scan < len(token_annotations):
            token = token_annotations[scan]
            if token.begin >= sentence.end:
                break
            if token.begin >= sentence.begin and token.end <= sentence.end:
                sentence_tokens.append(token)
            scan += 1
        windows.append(
            SpacyWindow(
                text=sentence.text or text[sentence.begin : sentence.end],
                offset=sentence.begin,
                token_annotations=tuple(sentence_tokens),
            )
        )
    return windows


def _doc_inputs(nlp: Any, windows: list[SpacyWindow]) -> list[str] | list[Any]:
    if not any(window.token_annotations for window in windows):
        return [window.text for window in windows]
    from spacy.tokens import Doc

    docs = []
    for window in windows:
        if not window.token_annotations:
            docs.append(nlp.make_doc(window.text))
            continue
        words = [token.text for token in window.token_annotations]
        spaces = [
            index + 1 < len(window.token_annotations)
            and window.token_annotations[index + 1].begin > token.end
            for index, token in enumerate(window.token_annotations)
        ]
        docs.append(Doc(nlp.vocab, words=words, spaces=spaces))
    return docs


def _morph_features(token: Any) -> dict[str, str]:
    raw = token.morph.to_dict()
    return {
        target: str(raw[source])
        for source, target in MORPH_KEYS.items()
        if source in raw and raw[source] is not None
    }


@telemetry.timed("spacy_batched_annotation_build_ms", annotator="spacy")
def _build_window_annotations(
    spacy_docs: list[Any],
    windows: list[SpacyWindow],
    outputs: set[str],
    *,
    emit_sentences: bool,
    start_ref: int = 1,
) -> tuple[list[object], int]:
    annotations: list[object] = []
    next_ref = start_ref
    for spacy_doc, window in zip(spacy_docs, windows):
        token_rows = [token for token in spacy_doc if not token.is_space]
        original_tokens = window.token_annotations
        token_refs: dict[int, dict[str, int]] = {}
        token_features_by_i: dict[int, dict[str, Any]] = {}
        write_lemma = "lemmatizer" in outputs
        write_pos = "tagger" in outputs
        write_morph = "morphologizer" in outputs

        def token_span(token: Any) -> tuple[int, int]:
            if original_tokens and token.i < len(original_tokens):
                original = original_tokens[token.i]
                return original.begin, original.end
            return window.offset + token.idx, window.offset + token.idx + len(token)

        for order, token in enumerate(token_rows):
            begin, end = token_span(token)
            token_ref = next_ref
            next_ref += 1
            token_annotation = Token(begin=begin, end=end, ref=token_ref)
            token_features = token_annotation.features
            token_key = order
            token_refs[token_key] = {"$ref": token_ref}
            token_features_by_i[token_key] = token_features
            annotations.append(token_annotation)

            if write_lemma:
                lemma_ref = next_ref
                next_ref += 1
                token_features["lemma"] = {"$ref": lemma_ref}
                annotations.append(
                    Lemma(begin=begin, end=end, ref=lemma_ref, value=token.lemma_ or token.text)
                )

            if write_pos:
                pos_ref = next_ref
                next_ref += 1
                token_features["pos"] = {"$ref": pos_ref}
                annotations.append(
                    POS(begin=begin, end=end, ref=pos_ref, PosValue=token.tag_, coarseValue=token.pos_)
                )

            if write_morph:
                morph_value = str(token.morph)
                morph_ref = next_ref
                next_ref += 1
                token_features["morph"] = {"$ref": morph_ref}
                morph_features = {"value": morph_value}
                morph_features.update(_morph_features(token))
                annotations.append(
                    MorphologicalFeatures(begin=begin, end=end, ref=morph_ref, **morph_features)
                )

        if "parser" in outputs:
            for token in token_rows:
                if token.is_space:
                    continue
                begin, end = token_span(token)
                dep_type = token.dep_
                output_type = DEPENDENCY_TYPE
                if dep_type == "ROOT":
                    output_type = ROOT_TYPE
                    dep_type = "--"
                dependent = token_refs.get(token.i)
                governor = token_refs.get(token.head.i)
                if dependent is not None and governor is not None:
                    token_features = token_features_by_i.get(token.i)
                    if token_features is not None:
                        token_features["parent"] = governor
                fields: dict[str, object] = {
                    "DependencyType": dep_type,
                    "flavor": "basic",
                }
                if dependent is not None:
                    fields["Dependent"] = dependent
                if governor is not None:
                    fields["Governor"] = governor
                if output_type == ROOT_TYPE:
                    annotations.append(ROOT_type_dependency_ROOT(begin=begin, end=end, **fields))
                else:
                    annotations.append(Dependency(begin=begin, end=end, **fields))

        if emit_sentences and "sentencizer" in outputs:
            for sentence in spacy_doc.sents:
                annotations.append(
                    Sentence(begin=window.offset + sentence.start_char, end=window.offset + sentence.end_char)
                )

        if "ner" in outputs:
            for entity in spacy_doc.ents:
                if original_tokens and entity.start < len(original_tokens):
                    begin = original_tokens[entity.start].begin
                    end = original_tokens[entity.end - 1].end
                else:
                    begin = window.offset + entity.start_char
                    end = window.offset + entity.end_char
                entity_features = {"value": entity.label_}
                if entity.kb_id_:
                    entity_features["identifier"] = entity.kb_id_
                annotations.append(NamedEntity(begin=begin, end=end, **entity_features))

    return annotations, next_ref


class SpacyAnnotator(DuuiAnnotator[V1RequestEnvelope, DuuiResult]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(
            meta={"source": "TTLab-UIMA/textimager-uima-spacy migration"},
        ),
        descriptor=AnnotatorDescriptor(
            name="spacy-lua-msgpack",
            version="1.0.0",
            input=IODescriptor(
                types={
                    "Sentence": [
                        "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
                    ],
                },
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                )
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
                    "SpacyAnnotatorMetaData": [
                        "org.texttechnologylab.annotation.SpacyAnnotatorMetaData"
                    ],
                    "ROOT": [
                        "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ROOT"
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
                "description": "Legacy variant alias: efficiency, accuracy/trf/full/lg, sm.",
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
            "spacy_batch_size": {
                "type": "integer",
                "description": "Batch size for sentence-window nlp.pipe processing.",
                "default": 32,
            },
            "use_existing_sentences": {
                "type": "boolean",
                "description": "Use Sentence annotations from the input CAS as processing windows.",
                "default": False,
            },
            "use_existing_tokens": {
                "type": "boolean",
                "description": "Use Token annotations from the input CAS as pretokenized input.",
                "default": False,
            },
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def process(self, doc: V1RequestEnvelope) -> DuuiResult:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        model_name = _model_name(doc)
        parameters = doc.parameters
        exclude = _parse_exclude(parameters.get("exclude"))
        outputs = _outputs(parameters)
        batch_size = _int(parameters.get("spacy_batch_size"), 32)
        use_existing_sentences = _bool(parameters.get("use_existing_sentences"))
        use_existing_tokens = _bool(parameters.get("use_existing_tokens"))
        sentence_annotations = (
            _input_annotations(doc, SENTENCE_TYPE) if use_existing_sentences else []
        )
        token_annotations = _input_annotations(doc, TOKEN_TYPE) if use_existing_tokens else []
        emit_sentences = not sentence_annotations
        windows = _windows(
            text,
            sentence_annotations,
            token_annotations,
        )
        await telemetry.trace(
            "spaCy process request configured",
            model=model_name,
            exclude=sorted(exclude),
            outputs=sorted(outputs),
            text_length=len(text),
            use_existing_sentences=use_existing_sentences,
            use_existing_tokens=use_existing_tokens,
            spacy_batch_size=batch_size,
            input_sentences=len(sentence_annotations),
            input_tokens=len(token_annotations),
            emit_sentences=emit_sentences,
        )
        nlp = _load_spacy(model_name, tuple(sorted(exclude)))
        model_raw = getattr(nlp, "meta", {}) or {}
        model_info = {
            "name": str(model_raw.get("name", model_name)),
            "version": str(model_raw.get("version", "runtime")),
            "lang": str(model_raw.get("lang", "x-unspecified")),
            "spacy_version": str(model_raw.get("spacy_version", "")),
            "spacy_git_version": str(model_raw.get("spacy_git_version", "")),
        }
        inputs = _doc_inputs(nlp, windows)
        spacy_docs = nlp.pipe(inputs, batch_size=batch_size)
        spacy_version = _spacy_version()
        meta = {
            "name": self.config.descriptor.name,
            "version": self.config.descriptor.version,
            "modelName": model_info["name"],
            "modelVersion": model_info["version"],
            "spacyVersion": spacy_version or "",
            "modelLang": model_info["lang"],
            "modelSpacyVersion": model_info["spacy_version"],
            "modelSpacyGitVersion": model_info["spacy_git_version"],
        }
        annotations, _ = _build_window_annotations(
            spacy_docs,
            windows,
            outputs,
            emit_sentences=emit_sentences,
            start_ref=1,
        )
        counts: dict[str, int] = {}
        for annotation in annotations:
            counts[annotation.type] = counts.get(annotation.type, 0) + 1
        annotation_count = len(annotations)
        elapsed_ms = int((time() - started) * 1000)
        await telemetry.count("spacy_annotations", annotation_count, model=model_name)
        for annotation_type, count in counts.items():
            await telemetry.count(
                "spacy_annotations_by_type", count, type=annotation_type
            )
        await telemetry.debug(
            "spaCy processing completed",
            model=model_name,
            annotations=annotation_count,
            windows=len(windows),
            elapsed_ms=elapsed_ms,
        )
        model_meta = SpacyAnnotatorMetaData(**meta)
        return DuuiResult.model_construct(
            sofa=None,
            annotations=annotations,
            feature_structures=[model_meta],
            meta=None,
            modification_meta=None,
            errors=[],
        )


@lru_cache(maxsize=1)
def _spacy_version() -> str | None:
    try:
        import spacy
    except Exception:
        return None
    return str(spacy.__version__)


app = create_app(SpacyAnnotator)
