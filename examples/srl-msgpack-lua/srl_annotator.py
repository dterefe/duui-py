from __future__ import annotations

from time import time

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.models import (
    AnnotationMeta,
    DocumentModification,
    DuuiDocument,
    DuuiResult,
    FeatureStructureKeyRef,
    FeatureStructureNode,
)

TOKEN_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token"
SENTENCE_TYPE = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence"
ENTITY_TYPE = "org.texttechnologylab.annotation.semaf.isobase.Entity"
SRLINK_TYPE = "org.texttechnologylab.annotation.semaf.semafsr.SrLink"


class SRLAnnotator(DuuiAnnotator[DuuiDocument, DuuiResult]):
    config_path = "annotator_config.json"

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    @staticmethod
    def _is_type(value: str, target: str) -> bool:
        return value == target or value.endswith(f".{target.split('.')[-1]}")

    async def process(self, doc: DuuiDocument) -> DuuiResult:
        text = doc.text or ""
        tokens = sorted(
            [fs for fs in doc.fs if fs.begin is not None and fs.end is not None and self._is_type(fs.type, TOKEN_TYPE)],
            key=lambda fs: (fs.begin or 0, fs.end or 0),
        )
        sentences = sorted(
            [fs for fs in doc.fs if fs.begin is not None and fs.end is not None and self._is_type(fs.type, SENTENCE_TYPE)],
            key=lambda fs: (fs.begin or 0, fs.end or 0),
        )

        if not tokens and text:
            tokens = []
            start = 0
            for word in text.split():
                idx = text.find(word, start)
                if idx < 0:
                    continue
                end = idx + len(word)
                from duui_py.models import FsRec

                tokens.append(FsRec(id=len(tokens) + 1, type=TOKEN_TYPE, begin=idx, end=end, features={}))
                start = end

        nodes: list[FeatureStructureNode] = []
        token_keys: list[str] = []
        for i, tok in enumerate(tokens):
            key = f"entity-{i}"
            token_keys.append(key)
            nodes.append(
                FeatureStructureNode(
                    key=key,
                    type=ENTITY_TYPE,
                    begin=tok.begin,
                    end=tok.end,
                    features={"comment": "token-entity"},
                )
            )

        max_links = int(doc.parameters.get("max_links_per_sentence") or 3)

        if not sentences and tokens:
            from duui_py.models import FsRec

            sentences = [FsRec(id=1, type=SENTENCE_TYPE, begin=tokens[0].begin, end=tokens[-1].end, features={})]

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
                nodes.append(
                    FeatureStructureNode(
                        key=f"link-{link_counter}",
                        type=SRLINK_TYPE,
                        begin=tokens[predicate_idx].begin,
                        end=tokens[predicate_idx].end,
                        features={
                            "figure": FeatureStructureKeyRef(key=token_keys[predicate_idx]),
                            "ground": FeatureStructureKeyRef(key=token_keys[ground_idx]),
                            "rel_type": f"ARG{role_i}",
                        },
                    )
                )

        return DuuiResult(
            feature_structures=nodes,
            meta=AnnotationMeta(
                name=self.config.descriptor.name,
                version=self.config.descriptor.version,
                modelName="heuristic-srl",
                modelVersion="1",
            ),
            modification_meta=DocumentModification(
                user=self.config.descriptor.name,
                timestamp=int(time()),
                comment=f"{self.config.descriptor.name} heuristic SRL",
            ),
        )


app = create_app(SRLAnnotator)
