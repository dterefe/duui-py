import pandas as pd
import spacy
import os
from glob import glob
import warnings
import sys
import logging
from spacy.tokens import Span
import pathlib


class TaxoNERD:
    def __init__(
        self,
        prefer_gpu=False,
        verbose=False,
        logger=None,
    ):
        self.logger = logger if logger else logging.getLogger(__name__)
        warnings.simplefilter("ignore")

        self.verbose = verbose
        self.extractor = None

        if prefer_gpu:
            import torch

            use_cuda = torch.cuda.is_available()
            self.logger.info("GPU is available" if use_cuda else "GPU not found")
            if use_cuda:
                spacy.require_gpu()
                self.logger.info("TaxoNERD will use GPU")

        self.nlp = None
        self.linker = None
        self.abbrev = None
        self.senten = None
        self._candidate_generators = {}

    def _extractor(self):
        if self.extractor is None:
            from taxonerd.extractor import TextExtractor

            self.extractor = TextExtractor(logger=self.logger)
        return self.extractor

    def load(
        self,
        model,
        exclude=[],
        linker=None,
        neighbours=10,
        threshold=0.7,
    ):
        self.nlp = spacy.load(model, exclude=exclude)
        if "pysbd_sentencizer" not in exclude:
            from scispacy.custom_sentence_segmenter import pysbd_sentencizer

            if not Span.has_extension("sent_id"):
                Span.set_extension("sent_id", default=None)
            before = "parser" if "parser" not in exclude else "ner"
            self.nlp.add_pipe("pysbd_sentencizer", before=before)
            self.senten = "pysbd_sentencizer"
        if "taxo_abbrev_detector" not in exclude:
            from taxonerd.abbreviation import TaxonomicAbbreviationDetector

            self.nlp.add_pipe("taxo_abbrev_detector")
            self.abbrev = "taxo_abbrev_detector"
        if linker:
            if "lemmatizer" in exclude:
                raise Exception(
                    "Lemmatizer is needed for entity linking. Make sure lemmatizer is not excluded from the pipeline"
                )

            import taxonerd.linking.linking

            self.nlp.add_pipe("lower_case_lemmas", after="lemmatizer")

            self.nlp.add_pipe(
                "taxo_linker",
                config={
                    "linker_name": linker,
                    "resolve_abbreviations": "taxo_abbrev_detector" not in exclude,
                    "filter_for_definitions": False,
                    "k": neighbours,
                    "threshold": threshold,
                },
                name="taxon_linker",
            )
            self.linker = "taxon_linker" in self.nlp.pipe_names
        if self.verbose:
            self.logger.info(
                "Loaded model {}-{}".format(
                    self.nlp.meta["name"], self.nlp.meta["version"]
                )
            )
            self.logger.info(f"Pipeline components: {self.nlp.pipe_names}")
        return self.nlp

    def find_in_corpus(self, input_dir, output_dir=None):
        df_map = {}
        input_dir = self._extractor()(input_dir)
        if input_dir:
            for filename in glob(os.path.join(input_dir, "*.txt")):
                df = self.find_in_file(filename, output_dir)
                if df is not None:
                    df_map[os.path.basename(filename)] = df
        return df_map

    def find_in_file(self, filename, output_dir=None):
        if not os.path.exists(filename):
            raise FileNotFoundError("File {} not found".format(filename))
        filename = self._extractor()(filename)
        if filename:
            self.logger.info("Extract taxa from file {}".format(filename))
            with open(filename, "r") as f:
                text = f.read()
            df = self.find_in_text(text)
            if output_dir:
                ann_filename = os.path.join(
                    output_dir,
                    ".".join(os.path.basename(filename).split(".")[:-1]) + ".ann",
                )
                df.to_csv(ann_filename, sep="\t", header=False)
                return ann_filename
            return df
        return None

    def find_in_text(self, text):
        doc = self.ner(text)
        return self.doc_to_df(doc)

    def _is_valid_entity(self, ent, text):
        return (
            "\n" not in text[ent.start_char : ent.end_char].strip("\n")
            and ent.label_ in ["LIVB"]
            and (ent._.kb_ents if self.linker else True)
        )

    def _filter_doc_entities(self, doc):
        ents = [ent for ent in doc.ents if self._is_valid_entity(ent, doc.text)]

        if ents and self.senten:
            sentences = {sent: id for id, sent in enumerate(doc.sents)}
            for ent in ents:
                ent._.sent_id = sentences[ent.sent]

        doc.set_ents(ents)
        return doc

    def ner(self, text):
        doc = self.nlp(text)
        return self._filter_doc_entities(doc)

    def pipe_texts(self, texts, batch_size=8, n_process=1):
        docs = self.nlp.pipe(texts, batch_size=batch_size, n_process=n_process)
        for doc in docs:
            yield self._filter_doc_entities(doc)

    def link_mentions(
        self,
        mentions,
        linker="gbif_backbone",
        neighbours=10,
        threshold=0.7,
        filter_for_definitions=False,
        no_definition_threshold=0.95,
        max_entities_per_mention=5,
        lowercase=True,
    ):
        from taxonerd.linking.candidate_generation import CandidateGenerator

        if linker not in self._candidate_generators:
            self._candidate_generators[linker] = CandidateGenerator(name_or_path=linker)
        generator = self._candidate_generators[linker]
        mention_strings = [
            str(mention).strip().lower() if lowercase else str(mention).strip()
            for mention in mentions
            if mention is not None and str(mention).strip()
        ]
        unique_mention_strings = list(dict.fromkeys(mention_strings))
        if not unique_mention_strings:
            return {}

        linked = {}
        batch_candidates = generator(unique_mention_strings, neighbours)
        entities = getattr(generator.kb, "cui_to_entity", {})
        for mention_string, candidates in zip(unique_mention_strings, batch_candidates):
            predicted = []
            for candidate in candidates:
                score = max(candidate.similarities) if candidate.similarities else 0.0
                entity = entities.get(candidate.concept_id)
                definition = getattr(entity, "definition", None)
                if (
                    filter_for_definitions
                    and definition is None
                    and score < no_definition_threshold
                ):
                    continue
                if score > threshold:
                    predicted.append((candidate.concept_id, candidate.aliases[0], score))

            sorted_predicted = sorted(predicted, reverse=True, key=lambda item: item[2])
            if sorted_predicted:
                max_score = sorted_predicted[0][-1]
                linked[mention_string] = [
                    item
                    for item in sorted_predicted[:max_entities_per_mention]
                    if item[-1] == max_score
                ]
            else:
                linked[mention_string] = []
        return linked

    def doc_to_df(self, doc):
        def get_entity_dict(ent):
            ent_dict = {
                "offsets": "{} {} {}".format(ent.label_, ent.start_char, ent.end_char),
                "text": ent.text.replace("\n", " "),
            }
            if self.linker:
                ent_dict["entity"] = ent._.kb_ents
            if self.senten:
                ent_dict["sent"] = ent._.sent_id
            return ent_dict

        entities = []
        if len(doc.ents) > 0:
            entities = [get_entity_dict(ent) for ent in doc.ents]
        df = pd.DataFrame(entities)
        df = df.dropna()
        df = df.loc[df.astype(str).drop_duplicates().index]
        df = df.reset_index(drop=True)
        return df.rename("T{}".format)
