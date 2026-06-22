from __future__ import annotations

import asyncio
import json
from time import time
from typing import Any

from pydantic import BaseModel, Field

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.lua_custom import LuaCustomCodec
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    Domain,
    DomainSpec,
    IODescriptor,
)
from duui_py.utils.params import resolve_prefer_gpu

from spacy_annotator import _activate_gpu_runtime, _load_spacy, _preload_model_name, _spacy_version


UIMA_TYPE_SENTENCE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
UIMA_TYPE_TOKEN = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"
UIMA_TYPE_LEMMA = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma"
UIMA_TYPE_POS = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"
UIMA_TYPE_MORPH = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.MorphologicalFeatures"
UIMA_TYPE_DEPENDENCY = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency"
UIMA_TYPE_NAMED_ENTITY = "de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity"

SPACY_MODELS: dict[str, dict[str, str]] = {
    "efficiency": {"de": "de_core_news_sm", "en": "en_core_web_sm", "fr": "fr_core_news_sm"},
    "accuracy": {"de": "de_dep_news_trf", "en": "en_core_web_trf", "fr": "fr_dep_news_trf"},
    "sm": {"de": "de_core_news_sm", "en": "en_core_web_sm", "fr": "fr_core_news_sm"},
    "trf": {"de": "de_dep_news_trf", "en": "en_core_web_trf", "fr": "fr_dep_news_trf"},
}
LANGUAGE_MAPPINGS = {"x-unspecified": "xx"}
TEXTIMAGER_OUTPUT_TYPES = {
    UIMA_TYPE_SENTENCE,
    UIMA_TYPE_TOKEN,
    UIMA_TYPE_LEMMA,
    UIMA_TYPE_POS,
    UIMA_TYPE_MORPH,
    UIMA_TYPE_DEPENDENCY,
    UIMA_TYPE_NAMED_ENTITY,
}
MORPH_KEYS: dict[str, str] = {
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
    "Negative": "negative",
    "Polarity": "negative",
    "NumType": "numType",
    "Possessive": "possessive",
    "Poss": "possessive",
    "PronType": "pronType",
    "Reflex": "reflex",
    "Transitivity": "transitivity",
    "VerbType": "transitivity",
}


LEGACY_LUA = r'''
StandardCharsets = luajava.bindClass("java.nio.charset.StandardCharsets")
JCasUtil = luajava.bindClass("org.apache.uima.fit.util.JCasUtil")
Token = luajava.bindClass("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token")
Sentence = luajava.bindClass("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence")

function serialize(inputCas, outputStream, parameters)
    parameters = parameters or {}
    local doc_text = inputCas:getDocumentText()
    local doc_lang = inputCas:getDocumentLanguage()
    local tokens = nil
    local spaces = nil
    local sent_starts = nil
    local use_existing_tokens = parameters["use_existing_tokens"] == "true"
    local use_existing_sentences = parameters["use_existing_sentences"] == "true"

    if use_existing_tokens then
        tokens = {}
        spaces = {}
        sent_starts = {}

        local tokens_count = 1
        local tokens_it = luajava.newInstance("java.util.ArrayList", JCasUtil:select(inputCas, Token)):listIterator()
        local sentences = luajava.newInstance("java.util.ArrayList", JCasUtil:select(inputCas, Sentence))
        while tokens_it:hasNext() do
            local token = tokens_it:next()
            tokens[tokens_count] = token:getCoveredText()
            local has_space = false
            if tokens_it:hasNext() then
                local next_token = tokens_it:next()
                has_space = next_token:getBegin() ~= token:getEnd()
                tokens_it:previous()
            end
            spaces[tokens_count] = has_space
            if use_existing_sentences then
                local sentences_it = sentences:listIterator()
                sent_starts[tokens_count] = false
                while sentences_it:hasNext() do
                    local sentence = sentences_it:next()
                    if sentence:getBegin() == token:getBegin() then
                        sent_starts[tokens_count] = true
                        break
                    elseif sentence:getBegin() > token:getBegin() then
                        break
                    end
                end
            end
            tokens_count = tokens_count + 1
        end
        doc_text = ""
    end

    outputStream:write(json.encode({
        text = doc_text,
        lang = doc_lang,
        parameters = parameters,
        tokens = tokens,
        spaces = spaces,
        sent_starts = sent_starts,
    }))
end

function add_spacy_meta(inputCas, reference, meta)
    local meta_anno = luajava.newInstance("org.texttechnologylab.annotation.SpacyAnnotatorMetaData", inputCas)
    meta_anno:setReference(reference)
    meta_anno:setName(meta["name"])
    meta_anno:setVersion(meta["version"])
    meta_anno:setModelName(meta["modelName"])
    meta_anno:setModelVersion(meta["modelVersion"])
    meta_anno:setSpacyVersion(meta["spacyVersion"])
    meta_anno:setModelLang(meta["modelLang"])
    meta_anno:setModelSpacyVersion(meta["modelSpacyVersion"])
    meta_anno:setModelSpacyGitVersion(meta["modelSpacyGitVersion"])
    meta_anno:addToIndexes()
end

function deserialize(inputCas, inputStream)
    local inputString = luajava.newInstance("java.lang.String", inputStream:readAllBytes(), StandardCharsets.UTF_8)
    local results = json.decode(inputString)
    local meta = results["meta"]
    local modification_meta = results["modification_meta"]

    if modification_meta ~= nil then
        local modification_anno = luajava.newInstance("org.texttechnologylab.annotation.DocumentModification", inputCas)
        modification_anno:setUser(modification_meta["user"])
        modification_anno:setTimestamp(modification_meta["timestamp"])
        modification_anno:setComment(modification_meta["comment"])
        modification_anno:addToIndexes()
    end

    for _, sent in ipairs(results["sentences"] or {}) do
        if sent["write_sentence"] then
            local sent_anno = luajava.newInstance("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence", inputCas)
            sent_anno:setBegin(sent["begin"])
            sent_anno:setEnd(sent["end"])
            sent_anno:addToIndexes()
            if meta ~= nil then add_spacy_meta(inputCas, sent_anno, meta) end
        end
    end

    local all_tokens = {}
    if results["is_pretokenized"] then
        local tokens_count = 0
        local tokens_it = JCasUtil:select(inputCas, Token):iterator()
        while tokens_it:hasNext() do
            local token = tokens_it:next()
            all_tokens[tokens_count] = token
            tokens_count = tokens_count + 1
        end
    end

    for i, token in ipairs(results["tokens"] or {}) do
        local token_anno = nil
        if results["is_pretokenized"] then
            token_anno = all_tokens[i - 1]
        elseif token["write_token"] then
            token_anno = luajava.newInstance("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token", inputCas)
            token_anno:setBegin(token["begin"])
            token_anno:setEnd(token["end"])
            token_anno:addToIndexes()
            all_tokens[i - 1] = token_anno
            if meta ~= nil then add_spacy_meta(inputCas, token_anno, meta) end
        end

        if token["write_lemma"] then
            local lemma_anno = luajava.newInstance("de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma", inputCas)
            lemma_anno:setBegin(token["begin"])
            lemma_anno:setEnd(token["end"])
            if token["lemma"] == nil or token["lemma"] == "" then
                if token_anno ~= nil then lemma_anno:setValue(token_anno:getCoveredText()) end
            else
                lemma_anno:setValue(token["lemma"])
            end
            lemma_anno:addToIndexes()
            if token_anno ~= nil then token_anno:setLemma(lemma_anno) end
            if meta ~= nil then add_spacy_meta(inputCas, lemma_anno, meta) end
        end

        if token["write_pos"] then
            local pos_anno = luajava.newInstance("de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS", inputCas)
            pos_anno:setBegin(token["begin"])
            pos_anno:setEnd(token["end"])
            pos_anno:setPosValue(token["pos"])
            pos_anno:setCoarseValue(token["pos_coarse"])
            pos_anno:addToIndexes()
            if token_anno ~= nil then token_anno:setPos(pos_anno) end
            if meta ~= nil then add_spacy_meta(inputCas, pos_anno, meta) end
        end

        if token["write_morph"] then
            local morph_anno = luajava.newInstance("de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.morph.MorphologicalFeatures", inputCas)
            morph_anno:setBegin(token["begin"])
            morph_anno:setEnd(token["end"])
            morph_anno:setValue(token["morph"])
            local details = token["morph_details"] or {}
            if details["gender"] ~= nil then morph_anno:setGender(details["gender"]) end
            if details["number"] ~= nil then morph_anno:setNumber(details["number"]) end
            if details["case"] ~= nil then morph_anno:setCase(details["case"]) end
            if details["degree"] ~= nil then morph_anno:setDegree(details["degree"]) end
            if details["verbForm"] ~= nil then morph_anno:setVerbForm(details["verbForm"]) end
            if details["tense"] ~= nil then morph_anno:setTense(details["tense"]) end
            if details["mood"] ~= nil then morph_anno:setMood(details["mood"]) end
            if details["voice"] ~= nil then morph_anno:setVoice(details["voice"]) end
            if details["definiteness"] ~= nil then morph_anno:setDefiniteness(details["definiteness"]) end
            if details["person"] ~= nil then morph_anno:setPerson(details["person"]) end
            if details["aspect"] ~= nil then morph_anno:setAspect(details["aspect"]) end
            if details["animacy"] ~= nil then morph_anno:setAnimacy(details["animacy"]) end
            if details["negative"] ~= nil then morph_anno:setNegative(details["negative"]) end
            if details["numType"] ~= nil then morph_anno:setNumType(details["numType"]) end
            if details["possessive"] ~= nil then morph_anno:setPossessive(details["possessive"]) end
            if details["pronType"] ~= nil then morph_anno:setPronType(details["pronType"]) end
            if details["reflex"] ~= nil then morph_anno:setReflex(details["reflex"]) end
            if details["transitivity"] ~= nil then morph_anno:setTransitivity(details["transitivity"]) end
            morph_anno:addToIndexes()
            if token_anno ~= nil then token_anno:setMorph(morph_anno) end
            if meta ~= nil then add_spacy_meta(inputCas, morph_anno, meta) end
        end
    end

    for _, dep in ipairs(results["dependencies"] or {}) do
        if dep["write_dep"] then
            local dep_anno = nil
            if dep["type"] == "ROOT" then
                dep_anno = luajava.newInstance("de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.ROOT", inputCas)
                dep_anno:setDependencyType("--")
            else
                dep_anno = luajava.newInstance("de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency", inputCas)
                dep_anno:setDependencyType(dep["type"])
            end
            dep_anno:setBegin(dep["begin"])
            dep_anno:setEnd(dep["end"])
            dep_anno:setFlavor(dep["flavor"])
            local governor_token = all_tokens[dep["governor_ind"]]
            if governor_token ~= nil then dep_anno:setGovernor(governor_token) end
            local dependent_token = all_tokens[dep["dependent_ind"]]
            if dependent_token ~= nil then dep_anno:setDependent(dependent_token) end
            if governor_token ~= nil and dependent_token ~= nil then dependent_token:setParent(governor_token) end
            dep_anno:addToIndexes()
            if meta ~= nil then add_spacy_meta(inputCas, dep_anno, meta) end
        end
    end

    for _, ent in ipairs(results["entities"] or {}) do
        if ent["write_entity"] then
            local ent_anno = luajava.newInstance("de.tudarmstadt.ukp.dkpro.core.api.ner.type.NamedEntity", inputCas)
            ent_anno:setBegin(ent["begin"])
            ent_anno:setEnd(ent["end"])
            ent_anno:setValue(ent["value"])
            ent_anno:addToIndexes()
            if meta ~= nil then add_spacy_meta(inputCas, ent_anno, meta) end
        end
    end
end
'''


class TextImagerRequest(BaseModel):
    text: str = ""
    tokens: list[str] | None = None
    spaces: list[bool] | None = None
    sent_starts: list[bool] | None = None
    lang: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


def _resolve_model_name(lang: str | None, parameters: dict[str, Any]) -> tuple[str, str]:
    if parameters.get("model_name"):
        document_lang = (lang or "x-unspecified").split("-")[0].lower()
        return str(parameters["model_name"]), document_lang

    model_variant = str(parameters.get("model_variant") or parameters.get("spacy_model_size") or "efficiency").lower()
    if model_variant == "lg":
        model_variant = "accuracy"
    elif model_variant == "trf":
        model_variant = "accuracy"
    elif model_variant == "sm":
        model_variant = "efficiency"
    if model_variant not in SPACY_MODELS:
        raise ValueError(f'The specified spaCy model variant "{model_variant}" does not exist.')

    document_lang = (lang or "xx").split("-")[0].lower()
    document_lang = LANGUAGE_MAPPINGS.get(document_lang, document_lang)
    if document_lang not in SPACY_MODELS[model_variant]:
        strict = str(parameters.get("strict_language_check", "false")).lower() == "true"
        if strict:
            raise ValueError(f'Document language "{document_lang}" could not be mapped to spaCy model.')
        if "xx" in SPACY_MODELS[model_variant]:
            document_lang = "xx"
        elif "en" in SPACY_MODELS[model_variant]:
            document_lang = "en"
        else:
            document_lang = next(iter(SPACY_MODELS[model_variant]))
    return SPACY_MODELS[model_variant][document_lang], document_lang


def _write_types(parameters: dict[str, Any], *, is_pretokenized: bool, has_sentences: bool) -> set[str]:
    raw = parameters.get("write_types")
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = [item.strip() for item in raw.strip("[]").split(",") if item.strip()]
        raw = parsed
    if isinstance(raw, (list, tuple, set)) and raw:
        types = {str(item) for item in raw}
    else:
        types = set(TEXTIMAGER_OUTPUT_TYPES)
    if is_pretokenized:
        types.discard(UIMA_TYPE_TOKEN)
        if has_sentences:
            types.discard(UIMA_TYPE_SENTENCE)
    return types


def _morph_details(token: Any) -> dict[str, str]:
    details: dict[str, str] = {}
    for feature in token.morph:
        fields = feature.split("=", 1)
        if len(fields) != 2:
            continue
        target = MORPH_KEYS.get(fields[0].strip())
        if target:
            details[target] = fields[1].strip()
    return details


class SpacyLegacyAnnotator(DuuiAnnotator[TextImagerRequest, dict[str, Any]]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "duui-uima/duui-spacy textimager JSON baseline"}),
        descriptor=AnnotatorDescriptor(
            name="textimager-duui-spacy-legacy-json",
            version="0.4.0-compatible",
            input=IODescriptor(text=DomainSpec(default=Domain(mimeType="application/json"))),
            output=IODescriptor(text=DomainSpec(default=Domain(mimeType="application/json"))),
        ),
        typesystem_xml_path="TypeSystemSpacy.xml",
        parameters_schema={
            "model_variant": {"type": "string", "default": "efficiency", "enum": ["efficiency", "accuracy"]},
            "spacy_model_size": {"type": "string", "description": "Alias for model_variant."},
            "model_name": {"type": "string", "description": "Exact spaCy model package name."},
            "write_types": {"type": "array", "description": "UIMA output type names to deserialize."},
            "use_existing_tokens": {"type": "boolean", "default": False},
            "use_existing_sentences": {"type": "boolean", "default": False},
            "spacy_batch_size": {"type": "integer", "default": 32},
            "strict_language_check": {"type": "boolean", "default": False},
            "spacy_disable": {"type": "array", "default": [], "description": "spaCy pipeline components to disable during model load."},
            "prefer_gpu": {"type": "boolean", "default": False},
        },
    )

    def codec(self) -> LuaCustomCodec[TextImagerRequest, dict[str, Any]]:
        return LuaCustomCodec(
            LEGACY_LUA,
            request_media_type="application/json",
            response_media_type="application/json",
            decode_request=TextImagerRequest.model_validate_json,
            encode_response=lambda result: json.dumps(result, separators=(",", ":")).encode("utf-8"),
            name="textimager-duui-spacy-legacy-json",
        )

    async def startup(self) -> None:
        prefer_gpu = resolve_prefer_gpu(None)
        model_name = _preload_model_name()
        if prefer_gpu:
            _load_spacy(model_name, tuple(), True)
        else:
            await asyncio.to_thread(_load_spacy, model_name, tuple(), False)

    async def process(self, request: TextImagerRequest) -> dict[str, Any]:
        parameters = request.parameters or {}
        prefer_gpu = resolve_prefer_gpu(parameters.get("prefer_gpu"))
        model_name, model_lang = _resolve_model_name(request.lang, parameters)
        disable = tuple(str(item) for item in parameters.get("spacy_disable", []) if str(item))
        if prefer_gpu:
            nlp = _load_spacy(model_name, disable, True)
        else:
            nlp = await asyncio.to_thread(_load_spacy, model_name, disable, False)

        batch_size = int(parameters.get("spacy_batch_size") or 32)
        is_pretokenized = bool(request.tokens and request.spaces and len(request.tokens) == len(request.spaces))
        has_sentences = bool(request.sent_starts)
        write_types = _write_types(parameters, is_pretokenized=is_pretokenized, has_sentences=has_sentences)
        if is_pretokenized:
            from spacy.tokens import Doc

            sent_starts = request.sent_starts if has_sentences else None
            doc_input = Doc(nlp.vocab, words=request.tokens or [], spaces=request.spaces or [], sent_starts=sent_starts)
            inputs: list[Any] = [doc_input]
            offsets = [0]
        else:
            inputs = [request.text or ""]
            offsets = [0]

        if prefer_gpu:
            _activate_gpu_runtime(True)
            spacy_docs = list(nlp.pipe(inputs, batch_size=batch_size))
        else:
            spacy_docs = await asyncio.to_thread(lambda: list(nlp.pipe(inputs, batch_size=batch_size)))

        model_meta = getattr(nlp, "meta", {}) or {}
        tokens: list[dict[str, Any]] = []
        dependencies: list[dict[str, Any]] = []
        entities: list[dict[str, Any]] = []
        sentences: list[dict[str, Any]] = []

        for doc, offset in zip(spacy_docs, offsets, strict=False):
            try:
                for sent in doc.sents:
                    sentences.append({
                        "begin": offset + sent.start_char,
                        "end": offset + sent.end_char,
                        "write_sentence": UIMA_TYPE_SENTENCE in write_types,
                    })
            except Exception:
                pass

            token_index: dict[int, int] = {}
            span_index: dict[tuple[int, int], int] = {}
            for token in doc:
                if token.is_space:
                    continue
                begin = offset + token.idx
                end = begin + len(token.text)
                token_row = {
                    "begin": begin,
                    "end": end,
                    "ind": len(tokens),
                    "write_token": UIMA_TYPE_TOKEN in write_types,
                    "lemma": token.lemma_,
                    "write_lemma": UIMA_TYPE_LEMMA in write_types,
                    "pos": token.tag_,
                    "pos_coarse": token.pos_,
                    "write_pos": UIMA_TYPE_POS in write_types,
                    "morph": "|".join(token.morph),
                    "morph_details": _morph_details(token),
                    "write_morph": UIMA_TYPE_MORPH in write_types,
                    "parent_ind": None,
                    "write_dep": UIMA_TYPE_DEPENDENCY in write_types,
                }
                token_index[token.i] = len(tokens)
                span_index[(token.idx, token.idx + len(token.text))] = len(tokens)
                tokens.append(token_row)

            for token in doc:
                if token.is_space or token.head.is_space:
                    continue
                dep_i = token_index.get(token.i)
                gov_i = token_index.get(token.head.i)
                if dep_i is None or gov_i is None:
                    continue
                tokens[dep_i]["parent_ind"] = gov_i
                dependencies.append({
                    "begin": tokens[dep_i]["begin"],
                    "end": tokens[dep_i]["end"],
                    "type": token.dep_.upper(),
                    "flavor": "basic",
                    "dependent_ind": dep_i,
                    "governor_ind": gov_i,
                    "write_dep": UIMA_TYPE_DEPENDENCY in write_types,
                })

            try:
                for entity in doc.ents:
                    entities.append({
                        "begin": offset + entity.start_char,
                        "end": offset + entity.end_char,
                        "value": entity.label_,
                        "write_entity": UIMA_TYPE_NAMED_ENTITY in write_types,
                    })
            except Exception:
                pass

        spacy_version = _spacy_version() or ""
        meta = {
            "name": self.config.descriptor.name,
            "version": self.config.descriptor.version,
            "modelName": str(model_meta.get("name", model_name)),
            "modelVersion": str(model_meta.get("version", "")),
            "spacyVersion": spacy_version,
            "modelLang": str(model_meta.get("lang", model_lang)),
            "modelSpacyVersion": str(model_meta.get("spacy_version", "")),
            "modelSpacyGitVersion": str(model_meta.get("spacy_git_version", "")),
        }
        modification_meta = {
            "user": self.config.descriptor.name,
            "timestamp": int(time()),
            "comment": (
                f"{self.config.descriptor.name} ({self.config.descriptor.version}), "
                f"spaCy ({spacy_version}), {meta['modelLang']} {meta['modelName']} ({meta['modelVersion']})"
            ),
        }
        return {
            "sentences": sentences,
            "tokens": tokens,
            "dependencies": dependencies,
            "entities": entities,
            "meta": meta,
            "modification_meta": modification_meta,
            "is_pretokenized": is_pretokenized,
        }


app = create_app(SpacyLegacyAnnotator)
