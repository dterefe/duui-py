from __future__ import annotations

import logging
from functools import lru_cache
from threading import Lock
from time import time
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

import spacy
from pydantic import BaseModel, Field

from duui_py.annotator import DuuiAnnotator
from duui_py.codecs.lua_custom import LuaCustomCodec
from duui_py.models import DuuiDocument, DuuiResult, AnnotationMeta, DocumentModification
from duui_py.models.uima import Sentence as UimaSentence, Token as UimaToken, Lemma as UimaLemma, POS as UimaPOS, NamedEntity as UimaNamedEntity
from duui_py.logging import (
    configure_logger,
    StreamSink,
    ConsoleSink,
    configure_stream_manager,
    create_event_context_from_request,
    get_event_logger,
    configure_metric_collector,
)
from duui_py.logging.errors import log_errors


# Request model matching the Lua script's msgpack structure
class SpacyRequest(BaseModel):
    text: str
    lang: str = "x-unspecified"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    tokens: Optional[List[str]] = None
    spaces: Optional[List[bool]] = None
    sent_starts: Optional[List[bool]] = None


# Response models
class Span(BaseModel):
    begin: int
    end: int


class SpacyToken(BaseModel):
    begin: int
    end: int
    ind: int
    write_token: bool = True
    lemma: Optional[str] = None
    write_lemma: bool = True
    pos: Optional[str] = None
    pos_coarse: Optional[str] = None
    write_pos: bool = True
    morph: Optional[str] = None
    write_morph: bool = True
    parent_ind: Optional[int] = None
    write_dep: bool = True
    like_url: bool = False
    has_vector: bool = False
    like_num: bool = False
    is_stop: bool = False
    is_oov: bool = False
    is_currency: bool = False
    is_quote: bool = False
    is_bracket: bool = False
    is_sent_start: bool = False
    is_sent_end: bool = False
    is_left_punct: bool = False
    is_right_punct: bool = False
    is_punct: bool = False
    is_title: bool = False
    is_upper: bool = False
    is_lower: bool = False
    is_digit: bool = False
    is_ascii: bool = False
    is_alpha: bool = False


class SpacyDependency(BaseModel):
    begin: int
    end: int
    type: str
    flavor: str = "basic"
    dependent_ind: int
    governor_ind: int
    write_dep: bool = True


class SpacySentence(BaseModel):
    begin: int
    end: int
    write_sentence: bool = True


class SpacyEntity(BaseModel):
    begin: int
    end: int
    value: str
    write_entity: bool = True


class SpacyResponse(BaseModel):
    sentences: List[SpacySentence] = Field(default_factory=list)
    tokens: List[SpacyToken] = Field(default_factory=list)
    dependencies: List[SpacyDependency] = Field(default_factory=list)
    entities: List[SpacyEntity] = Field(default_factory=list)
    noun_chunks: List[Span] = Field(default_factory=list)
    meta: Optional[AnnotationMeta] = None
    modification_meta: Optional[DocumentModification] = None
    is_pretokenized: bool = False


# Load spaCy model with caching
@lru_cache(maxsize=2)
def load_spacy_model(model_name: str, variant: str = "") -> spacy.Language:
    """Load and cache spaCy model."""
    if variant == "-sentencizer":
        nlp = spacy.blank("en")
        nlp.add_pipe("sentencizer")
        return nlp
    
    enabled_tools = []
    if variant:
        enabled_tools = [variant[1:]]  # Remove leading '-'
    
    return spacy.load(model_name, enable=enabled_tools)


class SpacyAnnotator(DuuiAnnotator[SpacyRequest, SpacyResponse]):
    """spaCy annotator using duui-py framework with Lua + msgpack."""
    
    # Default configuration path
    config_path = "annotator_config.json"
    
    def __init__(self, config_path: str | None = None, config: dict | None = None):
        super().__init__(config_path, config)
        
        # Configure logging and event streaming
        stream_manager = configure_stream_manager(default_ttl_minutes=5)
        stream_sink = StreamSink(stream_manager)
        console_sink = ConsoleSink()
        
        configure_logger(
            sinks=[stream_sink, console_sink],
            default_context={"annotator": self.config.descriptor.name},
            annotator_descriptor=self.config.descriptor,
            start_background_worker=True,
        )
        
        # Configure metrics collection
        collector = configure_metric_collector(
            collection_interval_seconds=5,
            include_system_metrics=True,
            include_process_metrics=True,
            include_disk_metrics=True,
            include_network_metrics=True,
        )
        collector.start()
        
        self.logger = get_event_logger()
        
        # Model cache lock
        self._model_lock = Lock()
        
        # Supported models
        self.spacy_models = {
            "en": "en_core_web_sm",
            "de": "de_core_news_sm",
            "fr": "fr_core_news_sm",
            "xx": "xx_ent_wiki_sm",  # Multi-language
        }
        
        self.logger.info(f"SpacyAnnotator initialized: {self.config.descriptor.name} v{self.config.descriptor.version}")
    
    def codec(self) -> LuaCustomCodec[SpacyRequest, SpacyResponse]:
        """Return the Lua + msgpack codec."""
        # Read Lua communication script
        with open("spacy_communication.lua", "r", encoding="utf-8") as f:
            lua_script = f.read()
        
        # Define encode/decode functions for msgpack
        import msgpack
        
        def decode_request(body: bytes) -> SpacyRequest:
            """Decode msgpack request."""
            data = msgpack.unpackb(body, raw=False, strict_map_key=False)
            return SpacyRequest(**data)
        
        def encode_response(result: SpacyResponse) -> bytes:
            """Encode response to msgpack."""
            return msgpack.packb(result.model_dump(by_alias=True, exclude_none=True), use_bin_type=True)
        
        return LuaCustomCodec(
            communication_lua=lua_script,
            request_media_type="application/x-msgpack",
            response_media_type="application/x-msgpack",
            decode_request=decode_request,
            encode_response=encode_response,
            name="spacy-lua-msgpack",
        )
    
    @log_errors(log_level="ERROR", recovery_suggestion="Check input format and spaCy model availability")
    async def process(self, request: SpacyRequest) -> SpacyResponse:
        """Process a document with spaCy."""
        start_time = time()
        
        # Log start of processing
        await self.logger.info(f"Processing document, language: {request.lang}, text length: {len(request.text)}")
        
        # Get model name
        model_name = self._get_model_name(request.lang, request.parameters)
        
        # Load model (cached)
        with self._model_lock:
            nlp = load_spacy_model(model_name, self.config.descriptor.name)
        
        # Process document
        is_pretokenized = request.tokens is not None and len(request.tokens) > 0
        
        if is_pretokenized:
            # Use pre-tokenized input
            doc = self._process_pretokenized(nlp, request)
        else:
            # Process full text
            doc = nlp(request.text)
        
        # Extract annotations
        sentences = self._extract_sentences(doc)
        tokens = self._extract_tokens(doc)
        dependencies = self._extract_dependencies(doc, tokens)
        entities = self._extract_entities(doc)
        noun_chunks = self._extract_noun_chunks(doc)
        
        # Get spaCy model metadata
        spacy_meta = nlp.meta
        
        # Create metadata
        meta = AnnotationMeta(
            name=self.config.descriptor.name,
            version=self.config.descriptor.version,
            modelName=spacy_meta.get("name", model_name),
            modelVersion=spacy_meta.get("version", "unknown"),
        )
        
        # Create modification metadata
        modification_meta = DocumentModification(
            user=self.config.descriptor.name,
            timestamp=int(time()),
            comment=f"{self.config.descriptor.name} ({self.config.descriptor.version}), spaCy ({spacy.__version__}), {spacy_meta.get('lang', 'unknown')} {spacy_meta.get('name', model_name)} ({spacy_meta.get('version', 'unknown')})"
        )
        
        # Log completion
        await self.logger.metric(
            category="processing",
            name="document_processing_time",
            value=time() - start_time,
            unit="seconds",
            interval_ms=1000,
            tags={"language": request.lang, "model": model_name},
        )
        
        return SpacyResponse(
            sentences=sentences,
            tokens=tokens,
            dependencies=dependencies,
            entities=entities,
            noun_chunks=noun_chunks,
            meta=meta,
            modification_meta=modification_meta,
            is_pretokenized=is_pretokenized,
        )
    
    def _get_model_name(self, lang: str, parameters: Dict[str, Any]) -> str:
        """Get spaCy model name for language."""
        # Check parameters first
        if "model_name" in parameters:
            return parameters["model_name"]
        
        # Map language to model
        if lang in self.spacy_models:
            return self.spacy_models[lang]
        
        # Default to multi-language model
        return self.spacy_models["xx"]
    
    def _process_pretokenized(self, nlp: spacy.Language, request: SpacyRequest) -> spacy.tokens.Doc:
        """Process pre-tokenized input."""
        if request.sent_starts and len(request.sent_starts) == len(request.tokens):
            doc = spacy.tokens.Doc(
                nlp.vocab,
                words=request.tokens,
                spaces=request.spaces,
                sent_starts=request.sent_starts,
            )
        else:
            doc = spacy.tokens.Doc(
                nlp.vocab,
                words=request.tokens,
                spaces=request.spaces,
            )
        
        # Process with pipeline
        for pipe_name in nlp.pipe_names:
            nlp.get_pipe(pipe_name)(doc)
        
        return doc
    
    def _extract_sentences(self, doc: spacy.tokens.Doc) -> List[SpacySentence]:
        """Extract sentences from spaCy document."""
        sentences = []
        for sent in doc.sents:
            sentences.append(SpacySentence(
                begin=sent.start_char,
                end=sent.end_char,
                write_sentence=True,
            ))
        return sentences
    
    def _extract_tokens(self, doc: spacy.tokens.Doc) -> List[SpacyToken]:
        """Extract tokens from spaCy document."""
        tokens = []
        for i, token in enumerate(doc):
            if token.is_space:
                continue
                
            tokens.append(SpacyToken(
                begin=token.idx,
                end=token.idx + len(token),
                ind=i,
                write_token=True,
                lemma=token.lemma_,
                write_lemma=True,
                pos=token.tag_,
                pos_coarse=token.pos_,
                write_pos=True,
                morph="|".join(token.morph),
                write_morph=True,
                like_url=token.like_url,
                has_vector=token.has_vector,
                like_num=token.like_num,
                is_stop=token.is_stop,
                is_oov=token.is_oov,
                is_currency=token.is_currency,
                is_quote=token.is_quote,
                is_bracket=token.is_bracket,
                is_sent_start=token.is_sent_start,
                is_sent_end=token.is_sent_end,
                is_left_punct=token.is_left_punct,
                is_right_punct=token.is_right_punct,
                is_punct=token.is_punct,
                is_title=token.is_title,
                is_upper=token.is_upper,
                is_lower=token.is_lower,
                is_digit=token.is_digit,
                is_ascii=token.is_ascii,
                is_alpha=token.is_alpha,
            ))
        return tokens
    
    def _extract_dependencies(self, doc: spacy.tokens.Doc, tokens: List[SpacyToken]) -> List[SpacyDependency]:
        """Extract dependencies from spaCy document."""
        dependencies = []
        token_map = {}
        
        # Create token map by position
        for token in tokens:
            token_map[(token.begin, token.end)] = token
        
        for token in doc:
            if token.is_space or token.head.is_space:
                continue
            
            # Find corresponding token
            token_key = (token.idx, token.idx + len(token))
            head_key = (token.head.idx, token.head.idx + len(token.head))
            
            if token_key in token_map and head_key in token_map:
                token_obj = token_map[token_key]
                head_obj = token_map[head_key]
                
                # Set parent index
                token_obj.parent_ind = head_obj.ind
                
                # Create dependency
                dependencies.append(SpacyDependency(
                    begin=token.idx,
                    end=token.idx + len(token),
                    type=token.dep_.upper(),
                    flavor="basic",
                    dependent_ind=token_obj.ind,
                    governor_ind=head_obj.ind,
                    write_dep=True,
                ))
        
        return dependencies
    
    def _extract_entities(self, doc: spacy.tokens.Doc) -> List[SpacyEntity]:
        """Extract named entities from spaCy document."""
        entities = []
        for ent in doc.ents:
            entities.append(SpacyEntity(
                begin=ent.start_char,
                end=ent.end_char,
                value=ent.label_,
                write_entity=True,
            ))
        return entities
    
    def _extract_noun_chunks(self, doc: spacy.tokens.Doc) -> List[Span]:
        """Extract noun chunks from spaCy document."""
        noun_chunks = []
        for chunk in doc.noun_chunks:
            noun_chunks.append(Span(
                begin=chunk.start_char,
                end=chunk.end_char,
            ))
        return noun_chunks


# Create FastAPI app
from duui_py.app import create_app

app = create_app(SpacyAnnotator)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("spacy_annotator:app", host="0.0.0.0", port=9714, reload=True)