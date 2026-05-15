from __future__ import annotations

from collections.abc import AsyncIterator

from time import time

from duui_py.annotator import DuuiAnnotator
from duui_py.adapters import AsyncChunkedRequestAdapter
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.metrics import metrics
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
from duui_py.models.uima_typesystem.de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.types import (
    Sentence,
    Token,
)
from duui_py.models.uima_typesystem.texttechnologylab.annotation.semaf.isobase.types import Entity
from duui_py.models.uima_typesystem.texttechnologylab.annotation.semaf.semafsr.types import SrLink

TOKEN_TYPE = Token.model_fields["type"].default
SENTENCE_TYPE = Sentence.model_fields["type"].default


class SRLAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"example": "duui-srl migration"}),
        descriptor=AnnotatorDescriptor(
            name="srl-msgpack-lua",
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
                        types={"Span": [SENTENCE_TYPE, TOKEN_TYPE]},
                    )
                ),
            ),
            output=IODescriptor(
                types={
                    "Entity": ["org.texttechnologylab.annotation.semaf.isobase.Entity"],
                    "SrLink": ["org.texttechnologylab.annotation.semaf.semafsr.SrLink"],
                },
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                ),
            ),
        ),
        typesystem_xml_path="TypeSystemSRL.xml",
        parameters_schema={
            "max_links_per_sentence": {
                "type": "integer",
                "default": 3,
                "description": "Maximum generated SRL links per sentence.",
            }
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @staticmethod
    def _is_type(value: str, target: str) -> bool:
        return value == target or value.endswith(f".{target.split('.')[-1]}")

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        text = sofa_text_value(doc.sofa) or ""
        max_links = int(doc.parameters.get("max_links_per_sentence") or 3)

        tokens = sorted(
            [fs for fs in doc.fs if fs.begin is not None and fs.end is not None and self._is_type(fs.type, TOKEN_TYPE)],
            key=lambda fs: (fs.begin or 0, fs.end or 0),
        )
        sentences = sorted(
            [fs for fs in doc.fs if fs.begin is not None and fs.end is not None and self._is_type(fs.type, SENTENCE_TYPE)],
            key=lambda fs: (fs.begin or 0, fs.end or 0),
        )

        if not tokens and text:
            start = 0
            for word in text.split():
                idx = text.find(word, start)
                if idx < 0:
                    continue
                end = idx + len(word)
                tokens.append(Token(begin=idx, end=end))
                start = end

        annotations = 0
        for tok in tokens:
            annotations += 1
            yield Entity(begin=tok.begin, end=tok.end, comment="token-entity")

        if not sentences and tokens:
            sentences = [Sentence(begin=tokens[0].begin, end=tokens[-1].end)]

        link_counter = 0
        for sent in sentences:
            sent_token_ids = [
                idx
                for idx, tok in enumerate(tokens)
                if (tok.begin or 0) >= (sent.begin or 0) and (tok.end or 0) <= (sent.end or 0)
            ]
            if len(sent_token_ids) < 2:
                continue

            predicate_local = len(sent_token_ids) // 2
            predicate_idx = sent_token_ids[predicate_local]
            role_targets = [i for i in sent_token_ids if i != predicate_idx][:max_links]

            for role_i, ground_idx in enumerate(role_targets):
                link_counter += 1
                yield SrLink(
                            begin=tokens[predicate_idx].begin,
                            end=tokens[predicate_idx].end,
                            rel_type=f"ARG{role_i}",
                            features={
                                "figureBegin": tokens[predicate_idx].begin,
                                "figureEnd": tokens[predicate_idx].end,
                                "groundBegin": tokens[ground_idx].begin,
                                "groundEnd": tokens[ground_idx].end,
                            },
                )

        elapsed_ms = int((time() - started) * 1000)
        await metrics.count("srl_tokens", len(tokens))
        await metrics.count("srl_sentences", len(sentences))
        await metrics.count("srl_links", link_counter)
        await metrics.count("srl_annotations", annotations)
        await metrics.timing("srl_processing_ms", elapsed_ms)

        yield AnnotatorMetaData(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName="heuristic-srl",
                modelVersion="1",
        )
        yield DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} heuristic SRL",
        )


app = create_app(SRLAnnotator, request_adapter=AsyncChunkedRequestAdapter())
