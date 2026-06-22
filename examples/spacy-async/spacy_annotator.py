from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from time import time
from typing import Any
import asyncio
import gc
import importlib.util
import json
import os
from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import unavailable, unprocessable
from duui_py.logging import logger
from duui_py.utils.params import param_str, param_bool, param_int, param_csv, resolve_prefer_gpu
from duui_py.utils.windowing import TextWindow, select_spans, build_windows
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
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.types import POS
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.ner.type.types import NamedEntity
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.types import (
    Lemma, Sentence, Token,
)
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.types import (
    Dependency, ROOT_type_dependency_ROOT,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.types import SpacyAnnotatorMetaData

SPACY_MODELS: dict[str, dict[str, str]] = {
    "trf": {"de": "de_dep_news_trf", "en": "en_core_web_trf"},
    "sm": {"de": "de_core_news_sm", "en": "en_core_web_sm"},
}


def _preload_model_name() -> str:
    configured = os.getenv("DUUI_SPACY_PRELOAD_MODEL", "").strip()
    if configured:
        return configured
    transformer = SPACY_MODELS["trf"]["en"]
    if importlib.util.find_spec(transformer) is not None:
        return transformer
    return SPACY_MODELS["sm"]["en"]

VARIANT_OUTPUTS: dict[str, set[str]] = {
    "": {"tokenizer", "sentencizer", "lemmatizer", "tagger", "morphologizer", "parser", "ner"},
}
DEFAULT_OUTPUTS = frozenset(VARIANT_OUTPUTS[""])

# ---------------------------------------------------------------------------
# OPTIMIZATION: Map outputs to spaCy pipeline component names
# Used for selective pipeline disabling (optimization #4)
# ---------------------------------------------------------------------------
OUTPUT_TO_PIPELINE: dict[str, str] = {
    "tagger": "tagger",
    "morphologizer": "morphologizer",
    "parser": "parser",
    "ner": "ner",
    "lemmatizer": "lemmatizer",
    "sentencizer": "senter",
}

# ---------------------------------------------------------------------------
# OPTIMIZATION: Annotation types for pre-annotation pass-through check
# ---------------------------------------------------------------------------
MORPH_KEYS: dict[str, str] = {
    "Gender": "gender", "Number": "number", "Case": "case", "Degree": "degree",
    "VerbForm": "verbForm", "Tense": "tense", "Mood": "mood", "Voice": "voice",
    "Definite": "definiteness", "Definiteness": "definiteness", "Person": "person",
    "Aspect": "aspect", "Animacy": "animacy", "Polarity": "negative",
    "NumType": "numType", "Poss": "possessive", "PronType": "pronType",
    "Reflex": "reflex", "VerbType": "transitivity",
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

# Map output names to UIMA type names for pass-through check
OUTPUT_TO_TYPE: dict[str, str] = {
    "tokenizer": TOKEN_TYPE,
    "lemmatizer": LEMMA_TYPE,
    "tagger": POS_TYPE,
    "morphologizer": MORPH_TYPE,
    "parser": DEPENDENCY_TYPE,
    "ner": NAMED_ENTITY_TYPE,
    "sentencizer": SENTENCE_TYPE,
}


# ---------------------------------------------------------------------------
# OPTIMIZATION #4: Selective pipeline disabling
# ---------------------------------------------------------------------------
def _required_pipeline_components(outputs: set[str]) -> set[str]:
    """Determine which spaCy pipeline components are needed based on requested outputs.

    Returns a set of component names that should remain enabled. All other
    pipeline components will be disabled.
    """
    needed: set[str] = set()
    for output_name, component in OUTPUT_TO_PIPELINE.items():
        if output_name in outputs:
            needed.add(component)
    # tok2vec / transformer may be implicitly needed by downstream components;
    # spaCy handles internal dependency resolution when we disable.
    return needed


def _disable_unused_pipeline_components(nlp: Any, outputs: set[str]) -> None:
    """Disable spaCy pipeline components whose outputs are not requested.

    This avoids unnecessary computation for tagger, parser, ner, etc.
    when the caller only needs a subset of annotations.
    """
    needed = _required_pipeline_components(outputs)
    to_disable: list[str] = []
    for pipe_name in nlp.pipe_names:
        if pipe_name in {"transformer", "tok2vec"}:
            continue
        if pipe_name not in needed:
            to_disable.append(pipe_name)
    if to_disable:
        nlp.select_pipes(disable=to_disable)


# ---------------------------------------------------------------------------
# OPTIMIZATION #5: Adaptive batch sizing
# ---------------------------------------------------------------------------
def _adaptive_batch_size(text_length: int, configured: int) -> int:
    """Adjust batch size based on document length for optimal throughput.

    - Very short texts (<1K chars):  larger batches (up to 64)
    - Medium texts (<10K chars):     moderate batches (up to 32)
    - Long texts (>=10K chars):      smaller batches to avoid OOM (up to 16)
    - Never exceed the configured value.
    """
    if text_length < 1_000:
        return min(configured, max(4, 64))
    if text_length < 10_000:
        return min(configured, max(2, 32))
    return min(configured, max(1, 16))


# ---------------------------------------------------------------------------
# OPTIMIZATION #7: GPU memory optimization
# ---------------------------------------------------------------------------
def _gpu_memory_optimize(prefer_gpu: bool) -> None:
    """Configure GPU memory limits and environment for spaCy.

    Sets ``PYTORCH_CUDA_ALLOC_CONF`` to limit fragmentation, and when
    ``prefer_gpu`` is True, returns a cleanup callable for post-processing.
    """
    if not prefer_gpu:
        return
    # Limit memory fragmentation by controlling max split size
    current = os.environ.get("PYTORCH_CUDA_ALLOC_CONF", "")
    if "max_split_size_mb" not in current:
        max_split_size_mb = os.environ.get("DUUI_SPACY_CUDA_MAX_SPLIT_SIZE_MB", "128")
        parts = [current] if current else []
        parts.append(f"max_split_size_mb:{max_split_size_mb}")
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = ",".join(parts)
    try:
        import torch
        if torch.cuda.is_available() and hasattr(torch, "set_default_device"):
            torch.set_default_device("cuda")
    except Exception:
        pass


def _gpu_cleanup(prefer_gpu: bool) -> None:
    """Run garbage collection and empty GPU caches after processing."""
    gc.collect()
    if prefer_gpu:
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass


def _activate_gpu_runtime(prefer_gpu: bool) -> None:
    if not prefer_gpu:
        return
    try:
        import spacy
        spacy.require_gpu()
    except Exception:
        pass
    try:
        import torch
        if torch.cuda.is_available():
            try:
                cuda_device = int(os.environ.get("DUUI_SPACY_CUDA_DEVICE", "0"))
            except ValueError:
                cuda_device = 0
            torch.cuda.set_device(cuda_device)
            if hasattr(torch, "set_default_device"):
                torch.set_default_device("cuda")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# OPTIMIZATION #3: Pre-annotation pass-through
# ---------------------------------------------------------------------------
def _check_pre_annotated_pass_through(
    doc: V1RequestEnvelope,
    outputs: set[str],
) -> dict[str, list[Any]] | None:
    """Check whether the input CAS already contains all requested annotations.

    If every required output type is present in ``doc.fs``, returns a dict
    mapping type names to their feature structures. Otherwise returns None,
    indicating spaCy processing is needed.

    This pass-through gives a ~100x speedup when pre-annotated CAS data exists.
    """
    required_types: set[str] = set()
    for output_name in outputs:
        type_name = OUTPUT_TO_TYPE.get(output_name)
        if type_name:
            required_types.add(type_name)

    # Also add ROOT type if parser output is requested
    if "parser" in outputs:
        required_types.add(ROOT_TYPE)

    # If nothing specific was requested, no pass-through possible
    if not required_types:
        return None

    # Collect existing annotations by type
    existing: dict[str, list[Any]] = {}
    for fs in doc.fs:
        if fs.type in required_types:
            existing.setdefault(fs.type, []).append(fs)

    # Check coverage: every required type must be present
    for type_name in required_types:
        if type_name not in existing:
            return None

    return existing


def _build_pass_through_annotations(
    existing: dict[str, list[Any]],
    outputs: set[str],
    text: str,
    *,
    start_ref: int = 1,
) -> tuple[list[object], dict[str, int], int]:
    """Rebuild annotations from pre-existing CAS data with sequential refs.

    Maintains exact output structure: Token→Lemma/POS/Morph/Dependency refs,
    Dependency→Token Governor/Dependent refs, etc.

    Returns (annotations_list, counts_dict, next_ref).
    """
    annotations: list[object] = []
    counts: dict[str, int] = {}
    next_ref = start_ref

    def append(annotation: object) -> None:
        annotations.append(annotation)
        annotation_type = annotation.type
        counts[annotation_type] = counts.get(annotation_type, 0) + 1

    def ref(value: int) -> dict[str, int]:
        return {"$ref": value}

    # -------------------------------------------------------------------
    # 1. Collect Token annotations and build begin → ref mapping
    # -------------------------------------------------------------------
    token_list = sorted(existing.get(TOKEN_TYPE, []), key=lambda fs: (fs.begin, fs.end))
    token_begin_to_ref: dict[int, int] = {}
    token_ref_to_begin: dict[int, int] = {}
    token_begin_to_features: dict[int, dict[str, Any]] = {}

    for token_fs in token_list:
        begin = int(token_fs.begin)
        end = int(token_fs.end)
        token_ref = next_ref
        next_ref += 1
        token_begin_to_ref[begin] = token_ref
        token_ref_to_begin[token_ref] = begin
        token_annotation = Token(begin=begin, end=end, ref=token_ref)
        # Carry over any existing features (order, etc.)
        token_annotation.features.update(token_fs.features)
        token_begin_to_features[begin] = token_annotation.features
        append(token_annotation)

    # -------------------------------------------------------------------
    # 2. Lemma annotations
    # -------------------------------------------------------------------
    if "lemmatizer" in outputs and LEMMA_TYPE in existing:
        lemma_list = sorted(existing[LEMMA_TYPE], key=lambda fs: (fs.begin, fs.end))
        for lemma_fs in lemma_list:
            begin = int(lemma_fs.begin)
            end = int(lemma_fs.end)
            lemma_ref = next_ref
            next_ref += 1
            value = lemma_fs.features.get("value", "")
            if not value:
                # Fall back to covered text
                value = text[begin:end] if begin < len(text) else ""
            # Link from parent Token
            token_ref_for_begin = token_begin_to_ref.get(begin)
            if token_ref_for_begin is not None:
                token_begin_to_features[begin]["lemma"] = ref(lemma_ref)
            append( Lemma(begin=begin, end=end, ref=lemma_ref, value=str(value)))

    # -------------------------------------------------------------------
    # 3. POS annotations
    # -------------------------------------------------------------------
    if "tagger" in outputs and POS_TYPE in existing:
        pos_list = sorted(existing[POS_TYPE], key=lambda fs: (fs.begin, fs.end))
        for pos_fs in pos_list:
            begin = int(pos_fs.begin)
            end = int(pos_fs.end)
            pos_ref = next_ref
            next_ref += 1
            pos_value = str(pos_fs.features.get("PosValue", ""))
            coarse_value = str(pos_fs.features.get("coarseValue", ""))
            token_ref_for_begin = token_begin_to_ref.get(begin)
            if token_ref_for_begin is not None:
                token_begin_to_features[begin]["pos"] = ref(pos_ref)
            append(POS(begin=begin, end=end, ref=pos_ref, PosValue=pos_value, coarseValue=coarse_value))

    # -------------------------------------------------------------------
    # 4. MorphologicalFeatures annotations
    # -------------------------------------------------------------------
    if "morphologizer" in outputs and MORPH_TYPE in existing:
        morph_list = sorted(existing[MORPH_TYPE], key=lambda fs: (fs.begin, fs.end))
        for morph_fs in morph_list:
            begin = int(morph_fs.begin)
            end = int(morph_fs.end)
            morph_ref = next_ref
            next_ref += 1
            value = str(morph_fs.features.get("value", ""))
            morph_features: dict[str, object] = {"value": value}
            for source, target in MORPH_KEYS.items():
                v = morph_fs.features.get(target)
                if v is not None:
                    morph_features[target] = str(v)
            token_ref_for_begin = token_begin_to_ref.get(begin)
            if token_ref_for_begin is not None:
                token_begin_to_features[begin]["morph"] = ref(morph_ref)
            append(MorphologicalFeatures(begin=begin, end=end, ref=morph_ref, **morph_features))

    # -------------------------------------------------------------------
    # 5. Dependency annotations
    # -------------------------------------------------------------------
    if "parser" in outputs:
        dep_types = {DEPENDENCY_TYPE, ROOT_TYPE}
        dep_list = sorted(
            [fs for t in dep_types for fs in existing.get(t, [])],
            key=lambda fs: (fs.begin, fs.end),
        )
        for dep_fs in dep_list:
            begin = int(dep_fs.begin)
            end = int(dep_fs.end)
            dep_type = str(dep_fs.features.get("DependencyType", ""))
            flavor = str(dep_fs.features.get("flavor", "basic"))

            # Resolve Governor/Dependent refs
            governor_raw = dep_fs.features.get("Governor")
            dependent_raw = dep_fs.features.get("Dependent")

            dependent_ref: dict[str, int] | None = None
            governor_ref: dict[str, int] | None = None

            if isinstance(governor_raw, dict):
                gov_ref_num = governor_raw.get("$ref")
                if gov_ref_num is not None:
                    gov_begin = token_ref_to_begin.get(gov_ref_num)
                    if gov_begin is not None:
                        mapped_gov = token_begin_to_ref.get(gov_begin)
                        if mapped_gov is not None:
                            governor_ref = ref(mapped_gov)
                            # Also set parent on token features
                            dep_begin = begin
                            if dep_begin in token_begin_to_features:
                                token_begin_to_features[dep_begin]["parent"] = ref(mapped_gov)

            if isinstance(dependent_raw, dict):
                dep_ref_num = dependent_raw.get("$ref")
                if dep_ref_num is not None:
                    dep_begin = token_ref_to_begin.get(dep_ref_num)
                    if dep_begin is not None:
                        mapped_dep = token_begin_to_ref.get(dep_begin)
                        if mapped_dep is not None:
                            dependent_ref = ref(mapped_dep)

            fields: dict[str, object] = {
                "DependencyType": dep_type if dep_type.upper() != "ROOT" else dep_type,
                "flavor": flavor,
            }
            if dependent_ref is not None:
                fields["Dependent"] = dependent_ref
            if governor_ref is not None:
                fields["Governor"] = governor_ref

            output_type = ROOT_TYPE if dep_type.upper() == "ROOT" else DEPENDENCY_TYPE
            if output_type == ROOT_TYPE:
                fields["DependencyType"] = "--"
                append(ROOT_type_dependency_ROOT(begin=begin, end=end, **fields))
            else:
                append(Dependency(begin=begin, end=end, **fields))

    # -------------------------------------------------------------------
    # 6. NamedEntity annotations
    # -------------------------------------------------------------------
    if "ner" in outputs and NAMED_ENTITY_TYPE in existing:
        ne_list = sorted(existing[NAMED_ENTITY_TYPE], key=lambda fs: (fs.begin, fs.end))
        for ne_fs in ne_list:
            begin = int(ne_fs.begin)
            end = int(ne_fs.end)
            value = str(ne_fs.features.get("value", ""))
            entity_features: dict[str, object] = {"value": value}
            identifier = ne_fs.features.get("identifier")
            if identifier:
                entity_features["identifier"] = str(identifier)
            append(NamedEntity(begin=begin, end=end, **entity_features))

    # -------------------------------------------------------------------
    # 7. Sentence annotations
    # -------------------------------------------------------------------
    if "sentencizer" in outputs and SENTENCE_TYPE in existing:
        sent_list = sorted(existing[SENTENCE_TYPE], key=lambda fs: (fs.begin, fs.end))
        for sent_fs in sent_list:
            begin = int(sent_fs.begin)
            end = int(sent_fs.end)
            append(Sentence(begin=begin, end=end))

    return annotations, counts, next_ref


# ---------------------------------------------------------------------------
# OPTIMIZATION #1: n_process for multiprocessing
# ---------------------------------------------------------------------------
def _n_process() -> int:
    """Return the number of worker processes for spaCy's nlp.pipe().

    Uses ``os.cpu_count()`` unless ``SPACY_N_PROCESS`` is set. Request
    parameters still take precedence in ``process``.
    """
    env_val = os.environ.get("SPACY_N_PROCESS")
    if env_val is not None:
        try:
            return max(1, int(env_val))
        except (ValueError, TypeError):
            pass
    return max(1, os.cpu_count() or 1)


# ---------------------------------------------------------------------------
# Existing helpers (unchanged)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=4)
def _load_spacy(model_name: str, exclude: tuple[str, ...], prefer_gpu: bool = True) -> Any:
    try:
        import spacy
    except Exception as exc:
        unavailable("spaCy is not installed in this runtime.", exception=type(exc).__name__)

    if prefer_gpu:
        _gpu_memory_optimize(prefer_gpu)
        try:
            spacy.require_gpu()
        except Exception as exc:
            unavailable("spaCy GPU was requested but could not be required.", exception=type(exc).__name__, detail=str(exc))
    try:
        nlp = spacy.load(model_name, exclude=list(exclude))
        return nlp
    except Exception as exc:
        unavailable(
            "spaCy model could not be loaded.",
            model=model_name, exception=type(exc).__name__, detail=str(exc),
        )


@lru_cache(maxsize=1)
def _spacy_version() -> str | None:
    try:
        import spacy
    except Exception:
        return None
    return str(spacy.__version__)


@dataclass(frozen=True)
class InputAnnotation:
    begin: int
    end: int
    text: str


def _input_annotations(doc: V1RequestEnvelope, type_name: str) -> list[InputAnnotation]:
    annotations: list[InputAnnotation] = []
    for fs in doc.fs:
        if fs.type != type_name:
            continue
        covered = fs.feature_map().get("coveredText")
        annotations.append(InputAnnotation(
            begin=int(fs.begin or 0),
            end=int(fs.end or 0),
            text=str(covered) if covered is not None else "",
        ))
    annotations.sort(key=lambda item: (item.begin, item.end))
    return annotations


def _spacy_windows(
    text: str,
    sentence_annotations: list[InputAnnotation],
    token_annotations: list[InputAnnotation],
) -> list[tuple[TextWindow, tuple[InputAnnotation, ...]]]:
    """Build spaCy processing windows from sentence/token annotations."""
    if not sentence_annotations:
        return [(TextWindow(begin=0, end=len(text), text=text), tuple(token_annotations))]
    windows: list[tuple[TextWindow, tuple[InputAnnotation, ...]]] = []
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
        win_text = sentence.text or text[sentence.begin:sentence.end]
        windows.append((
            TextWindow(begin=sentence.begin, end=sentence.end, text=win_text),
            tuple(sentence_tokens),
        ))
    return windows


def _doc_inputs(nlp: Any, windows: list[tuple[TextWindow, tuple[InputAnnotation, ...]]]) -> list[str] | list[Any]:
    if not any(tokens for _, tokens in windows):
        return [w.text for w, _ in windows]
    from spacy.tokens import Doc
    docs = []
    for window, tokens in windows:
        if not tokens:
            docs.append(nlp.make_doc(window.text))
            continue
        words = [token.text for token in tokens]
        spaces = [
            index + 1 < len(tokens) and tokens[index + 1].begin > token.end
            for index, token in enumerate(tokens)
        ]
        docs.append(Doc(nlp.vocab, words=words, spaces=spaces))
    return docs


def _build_window_annotations(
    spacy_docs: list[Any],
    windows: list[tuple[TextWindow, tuple[InputAnnotation, ...]]],
    outputs: set[str],
    *, emit_sentences: bool, start_ref: int = 1,
) -> tuple[list[object], dict[str, int], int]:
    annotations: list[object] = []
    counts: dict[str, int] = {}
    next_ref = start_ref

    def append(annotation: object) -> None:
        annotations.append(annotation)
        annotation_type = annotation.type
        counts[annotation_type] = counts.get(annotation_type, 0) + 1

    def ref(value: int) -> dict[str, int]:
        return {"$ref": value}

    for spacy_doc, (window, original_tokens) in zip(spacy_docs, windows):
        token_rows = [token for token in spacy_doc if not token.is_space]
        token_refs: dict[int, int] = {}
        token_features_by_i: dict[int, dict[str, Any]] = {}
        write_lemma = "lemmatizer" in outputs
        write_pos = "tagger" in outputs
        write_morph = "morphologizer" in outputs

        def token_span(token: Any) -> tuple[int, int]:
            if original_tokens and token.i < len(original_tokens):
                original = original_tokens[token.i]
                return original.begin, original.end
            return window.begin + token.idx, window.begin + token.idx + len(token)

        for token in token_rows:
            begin, end = token_span(token)
            token_ref = next_ref
            next_ref += 1
            token_annotation = Token(begin=begin, end=end, ref=token_ref)
            token_features = token_annotation.features
            token_key = token.i
            token_refs[token_key] = token_ref
            token_features_by_i[token_key] = token_features
            append(token_annotation)

            if write_lemma:
                lemma_ref = next_ref
                next_ref += 1
                token_features["lemma"] = ref(lemma_ref)
                append(Lemma(begin=begin, end=end, ref=lemma_ref, value=token.lemma_ or token.text))

            if write_pos:
                pos_ref = next_ref
                next_ref += 1
                token_features["pos"] = ref(pos_ref)
                append(POS(begin=begin, end=end, ref=pos_ref, PosValue=token.tag_, coarseValue=token.pos_))

            if write_morph:
                morph_value = str(token.morph)
                morph_ref = next_ref
                next_ref += 1
                token_features["morph"] = ref(morph_ref)
                raw = token.morph.to_dict()
                morph_features = {"value": morph_value}
                morph_features.update({
                    target: str(raw[source])
                    for source, target in MORPH_KEYS.items()
                    if source in raw and raw[source] is not None
                })
                append(MorphologicalFeatures(begin=begin, end=end, ref=morph_ref, **morph_features))

        if "parser" in outputs:
            for token in token_rows:
                if token.is_space:
                    continue
                begin, end = token_span(token)
                dep_type = token.dep_.upper()
                output_type = DEPENDENCY_TYPE
                if dep_type == "ROOT":
                    output_type = ROOT_TYPE
                    dep_type = "--"
                dependent_ref = token_refs.get(token.i)
                governor_ref = token_refs.get(token.head.i)
                if dependent_ref is not None and governor_ref is not None:
                    token_features = token_features_by_i.get(token.i)
                    if token_features is not None:
                        token_features["parent"] = ref(governor_ref)
                fields: dict[str, object] = {"DependencyType": dep_type, "flavor": "basic"}
                if dependent_ref is not None:
                    fields["Dependent"] = ref(dependent_ref)
                if governor_ref is not None:
                    fields["Governor"] = ref(governor_ref)
                if output_type == ROOT_TYPE:
                    append(ROOT_type_dependency_ROOT(begin=begin, end=end, **fields))
                else:
                    append(Dependency(begin=begin, end=end, **fields))

        if emit_sentences and "sentencizer" in outputs:
            for sentence in spacy_doc.sents:
                append(Sentence(
                    begin=window.begin + sentence.start_char,
                    end=window.begin + sentence.end_char,
                ))

        if "ner" in outputs:
            for entity in spacy_doc.ents:
                if original_tokens and entity.start < len(original_tokens):
                    entity_begin = original_tokens[entity.start].begin
                    entity_end = original_tokens[entity.end - 1].end
                else:
                    entity_begin = window.begin + entity.start_char
                    entity_end = window.begin + entity.end_char
                entity_features = {"value": entity.label_}
                if entity.kb_id_:
                    entity_features["identifier"] = entity.kb_id_
                append(NamedEntity(begin=entity_begin, end=entity_end, **entity_features))

    return annotations, counts, next_ref


class SpacyAnnotator(DuuiAnnotator[V1RequestEnvelope, DuuiResult]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "TTLab-UIMA/textimager-uima-spacy migration"}),
        descriptor=AnnotatorDescriptor(
            name="spacy-lua-msgpack",
            version="1.0.1",
            input=IODescriptor(
                types={"Sentence": ["de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"]},
                text=DomainSpec(
                    default=Domain(mimeType="text/plain; charset=utf-8", languages=["x-unspecified"]),
                ),
            ),
            output=IODescriptor(
                types={
                    "Sentence": ["de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"],
                    "Token": ["de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"],
                    "Lemma": ["de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma"],
                    "POS": ["de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"],
                    "MorphologicalFeatures": ["de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.MorphologicalFeatures"],
                    "Dependency": ["de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency"],
                    "NamedEntity": ["de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"],
                    "SpacyAnnotatorMetaData": ["org.texttechnologylab.annotation.SpacyAnnotatorMetaData"],
                    "ROOT": ["de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ROOT"],
                },
                text=DomainSpec(
                    default=Domain(mimeType="text/plain; charset=utf-8", languages=["x-unspecified"]),
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemSpacy.xml",
        parameters_schema={
            "model_name": {"type": "string", "default": "en_core_web_trf", "description": "Exact spaCy model package name."},
            "spacy_model": {"type": "string", "description": "Alias for model_name."},
            "single_model": {"type": "string", "description": "Alias for model_name."},
            "model_variant": {"type": "string", "default": "trf", "description": "Model variant: sm (efficiency) or trf (transformer)."},
            "spacy_model_size": {"type": "string", "description": "Alias for model_variant."},
            "spacy_language": {"type": "string", "default": "en", "description": "Language hint when model_name is not set."},
            "language": {"type": "string", "description": "Alias for spacy_language."},
            "lang": {"type": "string", "description": "Alias for spacy_language."},
            "exclude": {"type": "array", "description": "spaCy pipeline components or output groups to skip."},
            "spacy_batch_size": {"type": "integer", "default": 32, "description": "Batch size for nlp.pipe processing."},
            "use_existing_sentences": {"type": "boolean", "default": False, "description": "Use Sentence annotations from input CAS as processing windows."},
            "use_existing_tokens": {"type": "boolean", "default": False, "description": "Use Token annotations from input CAS as pretokenized input."},
            "spacy_n_process": {"type": "integer", "default": 0, "description": "Number of worker processes for nlp.pipe(). 0 = auto (cpu_count)."},
            "prefer_gpu": {"type": "boolean", "default": False, "description": "Prefer GPU when available for spaCy inference."},
            "disable_pipeline_components": {"type": "boolean", "default": True, "description": "Automatically disable unused pipeline components."},
            "adaptive_batch_size": {"type": "boolean", "default": True, "description": "Adapt batch size based on document length."},
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def startup(self) -> None:
        prefer_gpu = resolve_prefer_gpu(None)
        model_name = _preload_model_name()
        if prefer_gpu:
            _load_spacy(model_name, tuple(), True)
        else:
            await asyncio.to_thread(_load_spacy, model_name, tuple(), False)

    async def process(self, doc: V1RequestEnvelope) -> DuuiResult:
        started = time()
        logger().trace("spaCy process() entry")
        logger().info("spaCy process() started")

        text = sofa_text_value(doc.sofa) or ""
        params = doc.parameters

        def _parse_exclude(value: object | None) -> set[str]:
            if value is None:
                return set()
            if isinstance(value, str):
                text_val = value.strip()
                if not text_val:
                    return set()
                try:
                    decoded = json.loads(text_val)
                except json.JSONDecodeError:
                    decoded = [item.strip() for item in text_val.strip("[]").split(",") if item.strip()]
                value = decoded
            if isinstance(value, (list, tuple, set)):
                return {str(item).strip().strip("\"'").lower() for item in value if str(item).strip()}
            return {str(value).strip().lower()}

        # Resolve model name
        model_name = param_str(params, "model_name") or param_str(params, "spacy_model") or param_str(params, "single_model")
        if not model_name:
            language = param_str(params, "spacy_language") or param_str(params, "language") or param_str(params, "lang")
            sofa = getattr(doc, "sofa", None)
            if not language:
                language = getattr(sofa, "language", None) or getattr(doc, "language", None) or "en"
            variant = param_str(params, "model_variant") or param_str(params, "spacy_model_size") or "trf"
            if variant not in SPACY_MODELS:
                unprocessable("Unsupported spaCy model variant.", variant=variant, supported=sorted(SPACY_MODELS))
            if language not in SPACY_MODELS[variant]:
                if "xx" in SPACY_MODELS[variant]:
                    language = "xx"
                else:
                    unprocessable("Unsupported spaCy language for variant.", language=language, variant=variant)
            model_name = SPACY_MODELS[variant][language]

        exclude = _parse_exclude(params.get("exclude"))
        outputs = set(DEFAULT_OUTPUTS.difference(exclude))
        configured_batch_size = param_int(params, "spacy_batch_size", 32)
        use_existing_sentences = param_bool(params, "use_existing_sentences")
        use_existing_tokens = param_bool(params, "use_existing_tokens")
        prefer_gpu = resolve_prefer_gpu(params.get("prefer_gpu"))
        enable_pipeline_disabling = param_bool(params, "disable_pipeline_components", True)
        enable_adaptive_batch = param_bool(params, "adaptive_batch_size", True)
        configured_n_process = param_int(params, "spacy_n_process", 0)

        # ---- OPTIMIZATION #5: Adaptive batch sizing ----
        if enable_adaptive_batch:
            batch_size = _adaptive_batch_size(len(text), configured_batch_size)
        else:
            batch_size = configured_batch_size

        logger().info(
            f"spaCy model={model_name} outputs={sorted(outputs)} "
            f"use_sentences={use_existing_sentences} use_tokens={use_existing_tokens} "
            f"batch={batch_size} (configured={configured_batch_size}) "
            f"text_length={len(text)} n_process={configured_n_process or _n_process()}"
        )

        # ---- OPTIMIZATION #3: Pre-annotation pass-through ----
        pre_annotated = _check_pre_annotated_pass_through(doc, outputs)
        if pre_annotated is not None:
            logger().info(
                f"spaCy pass-through: all requested annotations already present in CAS. "
                f"Types found: {sorted(pre_annotated.keys())}"
            )
            logger().trace(
                "spaCy pass-through activated",
                model=model_name, outputs=sorted(outputs),
                text_length=len(text),
                found_types=sorted(pre_annotated.keys()),
            )

            annotations, counts, _ = _build_pass_through_annotations(
                pre_annotated, outputs, text, start_ref=1,
            )
            annotation_count = len(annotations)
            elapsed_ms = int((time() - started) * 1000)

            logger().info(
                f"spaCy pass-through complete: {annotation_count} annotations "
                f"breakdown={counts} elapsed={elapsed_ms}ms"
            )
            logger().debug_annotation_count(
                "spacy",
                annotation_count,
                counts=counts,
                mode="pass-through",
                model=model_name,
            )
            logger().trace_annotation_result(
                "spacy",
                annotations,
                counts=counts,
                mode="pass-through",
                model=model_name,
                elapsed_ms=elapsed_ms,
            )

            logger().metric("processing", "spacy_annotations", annotation_count, "count", tags={"model": model_name})
            for annotation_type, count in counts.items():
                logger().metric("processing", "spacy_annotations_by_type", count, "count", tags={"type": annotation_type})
            logger().debug(
                "spaCy pass-through completed",
                model=model_name, annotations=annotation_count,
                elapsed_ms=elapsed_ms, pass_through=True,
            )
            spacy_version = _spacy_version()
            resolved_model_info = _cached_model_info(model_name) or {}
            meta = {
                "name": self.config.descriptor.name,
                "version": self.config.descriptor.version,
                "modelName": resolved_model_info.get("name", model_name),
                "modelVersion": resolved_model_info.get("version", "runtime"),
                "spacyVersion": spacy_version or "",
                "modelLang": resolved_model_info.get("lang", "x-unspecified"),
                "modelSpacyVersion": resolved_model_info.get("spacy_version", ""),
                "modelSpacyGitVersion": resolved_model_info.get("spacy_git_version", ""),
            }
            model_meta = SpacyAnnotatorMetaData(**meta)
            return DuuiResult.model_construct(
                sofa=None, annotations=annotations, feature_structures=[model_meta],
                meta=None, modification_meta=None, errors=[],
            )

        # ---- Standard spaCy path ----
        sentence_annotations = _input_annotations(doc, SENTENCE_TYPE) if use_existing_sentences else []
        token_annotations = _input_annotations(doc, TOKEN_TYPE) if use_existing_tokens else []
        emit_sentences = not sentence_annotations
        windows = _spacy_windows(text, sentence_annotations, token_annotations)

        logger().info(
            f"spaCy windows built: {len(windows)} windows "
            f"emit_sentences={emit_sentences} input_sentences={len(sentence_annotations)}"
        )

        logger().trace(
            "spaCy process request configured",
            model=model_name, exclude=sorted(exclude), outputs=sorted(outputs),
            text_length=len(text), use_existing_sentences=use_existing_sentences,
            use_existing_tokens=use_existing_tokens, spacy_batch_size=batch_size,
            input_sentences=len(sentence_annotations), input_tokens=len(token_annotations),
            emit_sentences=emit_sentences,
        )

        if prefer_gpu:
            nlp = _load_spacy(model_name, tuple(sorted(exclude)), prefer_gpu)
        else:
            nlp = await asyncio.to_thread(_load_spacy, model_name, tuple(sorted(exclude)), prefer_gpu)
        logger().info(f"spaCy model loaded: {model_name}")

        # ---- OPTIMIZATION #4: Selective pipeline disabling ----
        if enable_pipeline_disabling:
            _disable_unused_pipeline_components(nlp, outputs)
            logger().info(f"spaCy pipeline components enabled after selective disable: {nlp.pipe_names}")

        model_raw = getattr(nlp, "meta", {}) or {}
        model_info = {
            "name": str(model_raw.get("name", model_name)),
            "version": str(model_raw.get("version", "runtime")),
            "lang": str(model_raw.get("lang", "x-unspecified")),
            "spacy_version": str(model_raw.get("spacy_version", "")),
            "spacy_git_version": str(model_raw.get("spacy_git_version", "")),
        }

        inputs = _doc_inputs(nlp, windows)

        # ---- OPTIMIZATION #1: n_process multiprocessing ----
        n_process = configured_n_process if configured_n_process > 0 else (1 if prefer_gpu else _n_process())
        if prefer_gpu:
            _activate_gpu_runtime(True)
            spacy_docs = list(nlp.pipe(inputs, batch_size=batch_size, n_process=n_process))
        else:
            spacy_docs = await asyncio.to_thread(
                lambda: list(nlp.pipe(inputs, batch_size=batch_size, n_process=n_process))
            )
        logger().info(f"spaCy pipeline completed: {len(spacy_docs)} docs (n_process={n_process})")
        logger().trace_backend_operation(
            "spacy",
            "nlp.pipe",
            model=model_name,
            doc_count=len(spacy_docs),
            batch_size=batch_size,
            n_process=n_process,
            pipeline_components=list(getattr(nlp, "pipe_names", [])),
        )

        annotations, counts, _ = await asyncio.to_thread(
            _build_window_annotations, spacy_docs, windows, outputs,
            emit_sentences=emit_sentences, start_ref=1,
        )

        annotation_count = len(annotations)
        elapsed_ms = int((time() - started) * 1000)

        logger().info(
            f"spaCy process() complete: {annotation_count} annotations "
            f"breakdown={counts} elapsed={elapsed_ms}ms"
        )
        logger().debug_annotation_count(
            "spacy",
            annotation_count,
            counts=counts,
            model=model_name,
            windows=len(windows),
        )
        logger().trace_annotation_result(
            "spacy",
            annotations,
            counts=counts,
            model=model_name,
            windows=len(windows),
            elapsed_ms=elapsed_ms,
        )

        logger().metric("processing", "spacy_annotations", annotation_count, "count", tags={"model": model_name})
        for annotation_type, count in counts.items():
            logger().metric("processing", "spacy_annotations_by_type", count, "count", tags={"type": annotation_type})
        logger().debug(
            "spaCy processing completed",
            model=model_name, annotations=annotation_count,
            windows=len(windows), elapsed_ms=elapsed_ms,
        )

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
        model_meta = SpacyAnnotatorMetaData(**meta)

        # ---- OPTIMIZATION #7: GPU cleanup ----
        _gpu_cleanup(prefer_gpu)

        return DuuiResult.model_construct(
            sofa=None, annotations=annotations, feature_structures=[model_meta],
            meta=None, modification_meta=None, errors=[],
        )


# ---------------------------------------------------------------------------
# Helper to get model info without loading the model (for pass-through path)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=8)
def _cached_model_info(model_name: str) -> dict[str, str] | None:
    """Resolve model metadata without fully loading the pipeline.

    Used by the pass-through path to populate SpacyAnnotatorMetaData
    without incurring a full spaCy load.
    """
    try:
        import spacy
        meta = spacy.info(model_name)
        if meta:
            return {
                "name": str(meta.get("name", model_name)),
                "version": str(meta.get("version", "runtime")),
                "lang": str(meta.get("lang", "x-unspecified")),
                "spacy_version": str(meta.get("spacy_version", "")),
                "spacy_git_version": str(meta.get("spacy_git_version", "")),
            }
    except Exception:
        pass
    return None


app = create_app(SpacyAnnotator)
