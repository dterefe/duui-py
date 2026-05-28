from typing import List, Dict, NamedTuple, Optional, Set, Tuple, Union
import json
from pathlib import Path
from collections import defaultdict
import sqlite3
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import RLock

from .file_cache import cached_path
from scispacy.umls_semantic_type_tree import (
    UmlsSemanticTypeTree,
    construct_umls_tree_from_tsv,
)

from urllib.request import pathname2url
import os

import logging

logger = logging.getLogger(__name__)

BIOFID_GBIF_BASE = "https://www.biofid.de/bio-ontologies/gbif/"
GBIF_SPECIES_BASE = "https://www.gbif.org/species/"
DEFAULT_FUSEKI_ENDPOINT = "http://host.containers.internal:8098/biofid-search/sparql"


def escape_quotes(alias):
    alias = alias.replace("'", "''")
    alias = alias.replace('"', '""')
    return alias


class Entity(NamedTuple):

    concept_id: str
    canonical_name: str
    aliases: List[str]
    types: List[str] = []
    definition: Optional[str] = None

    def __repr__(self):

        rep = ""
        num_aliases = len(self.aliases)
        rep = rep + f"CUI: {self.concept_id}, Name: {self.canonical_name}\n"
        rep = rep + f"Definition: {self.definition}\n"
        rep = rep + f"TUI(s): {', '.join(self.types)}\n"
        if num_aliases > 10:
            rep = (
                rep
                + f"Aliases (abbreviated, total: {num_aliases}): \n\t {', '.join(self.aliases[:10])}"
            )
        else:
            rep = (
                rep + f"Aliases: (total: {num_aliases}): \n\t {', '.join(self.aliases)}"
            )
        return rep


class KnowledgeBase:
    """
    A class representing two commonly needed views of a Knowledge Base:
    1. A mapping from concept_id to an Entity NamedTuple with more information.
    2. A mapping from aliases to the sets of concept ids for which they are aliases.

    Parameters
    ----------
    file_path: str, required.
        The file path to the json/jsonl representation of the KB to load.
    """

    def __init__(self, file_path: Union[str, Path, Tuple] = None, prefix: str = ""):
        self.prefix = prefix
        if file_path is None:
            raise ValueError(
                "Do not use the default arguments to KnowledgeBase. "
                "Instead, use a subclass (e.g GbifKnowledgeBase) or pass a path to a kb."
            )

        file_path = cached_path(file_path)
        if type(file_path) is tuple:
            user_friendly_name = file_path[1]
            file_path = file_path[0]
        db_path = os.path.splitext(file_path)[0] + ".db"

        if not os.path.exists(db_path):
            logger.info(
                "File {} not found, create SQLite database from {}".format(
                    db_path, file_path
                )
            )
            self.conn = self.json_to_sqlite(file_path, db_path)

        self.conn = self.get_conn_to_db(db_path)

    def json_to_sqlite(self, file_path: str = None, db_path: str = None):
        if file_path.endswith("jsonl"):
            raw = (json.loads(line) for line in open(cached_path(file_path)))
        else:
            raw = json.load(open(cached_path(file_path)))

        alias_to_cuis = defaultdict(set)
        cui_to_entity = {}

        for concept in raw:
            unique_aliases = set(concept["aliases"])
            unique_aliases.add(concept["canonical_name"])
            for alias in unique_aliases:
                # alias_to_cuis[alias] = (
                #     set() if alias not in alias_to_cuis else alias_to_cuis[alias]
                # )
                alias_to_cuis[alias].add(concept["concept_id"])
            cui_to_entity[concept["concept_id"]] = Entity(**concept)

        alias_to_cuis: Dict[str, Set[str]] = {**alias_to_cuis}

        conn = sqlite3.connect(db_path, check_same_thread=False)
        c = conn.cursor()
        c.execute("""CREATE TABLE alias_to_cuis (alias, cuis)""")
        entries = [(k, str(v)) for k, v in alias_to_cuis.items()]
        c.executemany("INSERT INTO alias_to_cuis VALUES (?,?)", entries)
        conn.commit()
        return conn

    def get_conn_to_db(self, file_path: str = None):
        dburi = "file:{}?mode=rw".format(pathname2url(file_path))
        conn = sqlite3.connect(dburi, uri=True, check_same_thread=False)
        return conn

    def get_cuis_from_alias(self, alias):
        c = self.conn.cursor()
        try:
            c.execute(
                "SELECT cuis FROM alias_to_cuis WHERE alias = '{}';".format(
                    escape_quotes(alias)
                )
            )
        except Exception as e:
            print(e, alias)
        return [self.prefix + c.fetchone()[0].strip("{}")]

    def get_cuis_from_aliases(self, aliases):
        c = self.conn.cursor()
        aliases_str = [
            "'{}'".format(escape_quotes(alias)) for alias in aliases
        ]  # Escape ' with ''
        c.execute(
            "SELECT alias, cuis FROM alias_to_cuis WHERE alias IN ({});".format(
                ",".join(aliases_str)
            )
        )
        mentions_to_concepts: Dict[str, List[str]] = defaultdict(list)
        for x in c.fetchall():
            concept_ids = [self.prefix + t.strip() for t in x[1].strip("{}").split(",")]
            mentions_to_concepts[x[0]].extend(
                concept_ids
            )  # self.prefix + x[1].strip("{}"))
        return mentions_to_concepts


class KnowledgeBaseFactory:
    def get_kb(self, name=None):
        if name == "gbif_backbone":
            return GbifKnowledgeBase()
        elif name in {"gbif_fuseki", "biofid_fuseki"}:
            return FusekiGbifKnowledgeBase()
        elif name == "taxref":
            return TaxRefKnowledgeBase()
        elif name == "ncbi_taxonomy":
            return NCBIKnowledgeBase()
        elif name == "ncbi_lite":
            return NCBILiteKnowledgeBase()
        else:
            raise ValueError(name)


class GbifKnowledgeBase(KnowledgeBase):
    def __init__(
        self,
        file_path=(
            "http://taxonerd.texttechnologylab.org/gbif/gbif_backbone_20230828.jsonl",
            "gbif_backbone_20230828.jsonl",
        ),
        prefix="GBIF:",
    ):
        super().__init__(file_path, prefix)


class FusekiGbifKnowledgeBase:
    """
    GBIF KB resolver backed by the UCE BioFID Fuseki service.

    The ANN index/vectorizer still comes from TaxoNERD's GBIF linker files. This
    class matches the KnowledgeBase interface used by CandidateGenerator.

    The ANN alias index and the Fuseki taxon graph are different artifacts:
    ANN candidates are aliases from the pinned TaxoNERD GBIF dictionary, while
    Fuseki contains BioFID graph labels and taxon facts. Resolving every ANN
    alias through SPARQL is both slow and incomplete. The hot path therefore
    canonicalizes ANN aliases with the local GBIF dictionary first, then uses
    Fuseki only for aliases absent from that dictionary.
    """

    prefix = "GBIF:"

    def __init__(
        self,
        endpoint: str | None = None,
        batch_size: int | None = None,
        concurrency: int | None = None,
        timeout: float | None = None,
    ):
        self.cui_to_entity = _MissingEntityDict()
        self._local_kb: GbifKnowledgeBase | None = None
        self._remote_alias_cache: Dict[str, List[str]] = {}
        self._lock = RLock()
        self.configure(
            endpoint=endpoint,
            batch_size=batch_size,
            concurrency=concurrency,
            timeout=timeout,
        )
        self.last_stats: Dict[str, float] = {}

    def configure(
        self,
        endpoint: str | None = None,
        batch_size: int | None = None,
        concurrency: int | None = None,
        timeout: float | None = None,
    ) -> None:
        self.endpoint = endpoint or DEFAULT_FUSEKI_ENDPOINT
        self.batch_size = int(batch_size or 128)
        self.concurrency = int(concurrency or 8)
        self.timeout = float(timeout or 20.0)
        self.local_fallback = True

    def get_cuis_from_alias(self, alias):
        return self.get_cuis_from_aliases([alias]).get(alias, [])

    def get_cuis_from_aliases(self, aliases):
        started = time.perf_counter()
        alias_list = list(dict.fromkeys(str(alias) for alias in aliases if str(alias).strip()))
        mentions_to_concepts: Dict[str, List[str]] = defaultdict(list)
        if not alias_list:
            self.last_stats = {
                "fuseki_aliases": 0.0,
                "fuseki_local_matches": 0.0,
                "fuseki_remote_aliases": 0.0,
                "fuseki_matches": 0.0,
                "fuseki_errors": 0.0,
                "fuseki_ms": 0.0,
                "fuseki_remote_ms": 0.0,
                "fuseki_cache_hits": 0.0,
                "fuseki_cache_misses": 0.0,
            }
            return mentions_to_concepts

        local_ms = 0.0
        local_matches = 0
        errors = 0
        if self.local_fallback:
            local_started = time.perf_counter()
            try:
                local_results = self._local().get_cuis_from_aliases(alias_list)
                for alias in alias_list:
                    concept_ids = self._dedupe_concepts(local_results.get(alias, ()))
                    if not concept_ids:
                        continue
                    mentions_to_concepts[alias].extend(concept_ids)
                    local_matches += 1
            except Exception as exc:
                errors += 1
                logger.warning("Local GBIF alias fallback failed: %s", exc)
            local_ms = (time.perf_counter() - local_started) * 1000.0

        unresolved = [alias for alias in alias_list if not mentions_to_concepts.get(alias)]
        remote_aliases: List[str] = []
        cache_hits = 0
        with self._lock:
            for alias in unresolved:
                cached = self._remote_alias_cache.get(alias)
                if cached is None:
                    remote_aliases.append(alias)
                    continue
                cache_hits += 1
                if cached:
                    mentions_to_concepts[alias].extend(cached)

        remote_ms = 0.0
        if remote_aliases:
            remote_started = time.perf_counter()
            chunks = [
                remote_aliases[index:index + self.batch_size]
                for index in range(0, len(remote_aliases), self.batch_size)
            ]
            workers = max(1, min(self.concurrency, len(chunks)))
            queried: Dict[str, List[str]] = defaultdict(list)
            if workers == 1:
                for chunk in chunks:
                    try:
                        for alias, concept_ids in self._query_alias_chunk(chunk).items():
                            queried[alias].extend(concept_ids)
                    except Exception as exc:
                        errors += 1
                        logger.warning("Fuseki GBIF alias chunk failed: %s", exc)
            else:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = [executor.submit(self._query_alias_chunk, chunk) for chunk in chunks]
                    for future in as_completed(futures):
                        try:
                            for alias, concept_ids in future.result().items():
                                queried[alias].extend(concept_ids)
                        except Exception as exc:
                            errors += 1
                            logger.warning("Fuseki GBIF alias chunk failed: %s", exc)
            with self._lock:
                for alias in remote_aliases:
                    concept_ids = self._dedupe_concepts(queried.get(alias, ()))
                    self._remote_alias_cache[alias] = concept_ids
                    if concept_ids:
                        mentions_to_concepts[alias].extend(concept_ids)
            remote_ms = (time.perf_counter() - remote_started) * 1000.0

        self.last_stats = {
            "fuseki_aliases": float(len(alias_list)),
            "fuseki_local_matches": float(local_matches),
            "fuseki_remote_aliases": float(len(remote_aliases)),
            "fuseki_matches": float(sum(1 for values in mentions_to_concepts.values() if values)),
            "fuseki_errors": float(errors),
            "fuseki_ms": (time.perf_counter() - started) * 1000.0,
            "fuseki_remote_ms": remote_ms,
            "fuseki_local_ms": local_ms,
            "fuseki_cache_hits": float(cache_hits),
            "fuseki_cache_misses": float(len(remote_aliases)),
        }
        return mentions_to_concepts

    def _local(self) -> GbifKnowledgeBase:
        if self._local_kb is None:
            with self._lock:
                if self._local_kb is None:
                    kb = GbifKnowledgeBase()
                    try:
                        kb.conn.execute("CREATE INDEX IF NOT EXISTS idx_alias_to_cuis_alias ON alias_to_cuis(alias)")
                        kb.conn.commit()
                    except Exception:
                        pass
                    self._local_kb = kb
        return self._local_kb

    def _query_alias_chunk(self, aliases: List[str]) -> Dict[str, List[str]]:
        if not aliases:
            return {}
        alias_to_variants = {
            alias: self._name_variants(alias)
            for alias in aliases
        }
        variant_to_aliases: Dict[str, List[str]] = defaultdict(list)
        for alias, variants in alias_to_variants.items():
            for variant in variants:
                variant_to_aliases[variant].append(alias)
        pair_values = " ".join(
            f"({predicate} {self._sparql_literal(value)})"
            for value in sorted(variant_to_aliases)
            for predicate in (
                "dwc:cleanedScientificName",
                "dwc:scientificName",
                "dwc:vernacularName",
                "rdfs:label",
            )
        )
        if not pair_values:
            return {}
        query = f"""
PREFIX dwc: <http://rs.tdwg.org/dwc/terms/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?name ?subject ?taxonID ?status ?rank
WHERE {{
  VALUES (?predicate ?name) {{ {pair_values} }}
  ?subject ?predicate ?name .
  OPTIONAL {{ ?subject dwc:taxonID ?taxonID . }}
  OPTIONAL {{ ?subject dwc:taxonomicStatus ?status . }}
  OPTIONAL {{ ?subject dwc:taxonRank ?rank . }}
}}
"""
        payload = self._sparql_query(query)
        rows_by_alias: Dict[str, List[Tuple[Tuple[int, int, int], str]]] = defaultdict(list)
        for binding in self._sparql_bindings(payload):
            name = self._binding_value(binding, "name")
            if not name:
                continue
            identifier = (
                self._gbif_identifier_from_uri(self._binding_value(binding, "taxonID"))
                or self._gbif_identifier_from_uri(self._binding_value(binding, "subject"))
            )
            if not identifier:
                continue
            rank = self._row_rank(
                self._binding_value(binding, "status") or "",
                self._binding_value(binding, "rank") or "",
                identifier,
            )
            for alias in variant_to_aliases.get(name, []):
                rows_by_alias[alias].append((rank, identifier))

        out: Dict[str, List[str]] = defaultdict(list)
        for alias, ranked_ids in rows_by_alias.items():
            seen = set()
            for _, identifier in sorted(ranked_ids, key=lambda item: item[0]):
                if identifier in seen:
                    continue
                seen.add(identifier)
                out[alias].append(identifier)
        return out

    @staticmethod
    def _dedupe_concepts(concept_ids) -> List[str]:
        out: List[str] = []
        seen = set()
        for concept_id in concept_ids or ():
            value = str(concept_id)
            if not value or value in seen:
                continue
            seen.add(value)
            out.append(value)
        return out

    @staticmethod
    def _env_bool(value: str | None, default: bool) -> bool:
        if value is None:
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}

    def _sparql_query(self, query: str) -> dict:
        data = urllib.parse.urlencode({"query": query}).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=data,
            method="POST",
            headers={
                "Accept": "application/sparql-results+json, application/json",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "User-Agent": "taxonerd-fuseki-gbif-kb/1.0",
            },
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _sparql_bindings(payload: dict) -> list:
        results = payload.get("results")
        if not isinstance(results, dict):
            return []
        bindings = results.get("bindings")
        return bindings if isinstance(bindings, list) else []

    @staticmethod
    def _binding_value(binding: dict, name: str) -> str | None:
        value = binding.get(name)
        if not isinstance(value, dict):
            return None
        raw = value.get("value")
        return str(raw) if raw is not None else None

    @staticmethod
    def _sparql_literal(value: str) -> str:
        return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'

    @staticmethod
    def _name_variants(value: str) -> List[str]:
        text = " ".join(str(value or "").strip().split())
        if not text:
            return []
        variants = {text}
        words = text.split()
        if len(words) == 1:
            variants.add(words[0][:1].upper() + words[0][1:])
            variants.add(words[0].title())
        elif words:
            variants.add(words[0][:1].upper() + words[0][1:] + " " + " ".join(words[1:]))
            variants.add(" ".join(item[:1].upper() + item[1:] for item in words))
            variants.add(text.title())
        return sorted(item for item in variants if item)

    @staticmethod
    def _gbif_identifier_from_uri(value: str | None) -> str | None:
        if not value:
            return None
        text = str(value).strip()
        if text.startswith("GBIF:"):
            return text
        for prefix in (GBIF_SPECIES_BASE, BIOFID_GBIF_BASE):
            if text.startswith(prefix):
                tail = text[len(prefix):].strip("/#")
                if tail:
                    return f"GBIF:{tail.split('/')[-1]}"
        if text.isdigit():
            return f"GBIF:{text}"
        return None

    @staticmethod
    def _row_rank(status: str, rank: str, identifier: str) -> Tuple[int, int, int]:
        status_value = str(status or "").lower()
        rank_value = str(rank or "").lower()
        try:
            numeric = int(str(identifier).rsplit(":", 1)[-1])
        except ValueError:
            numeric = 2_147_483_647
        status_score = 0 if "accepted" in status_value else 1 if "synonym" in status_value else 2
        rank_order = {
            "species": 0,
            "subspecies": 1,
            "variety": 2,
            "varietas": 2,
            "form": 3,
            "forma": 3,
            "genus": 4,
            "family": 5,
            "order": 6,
            "class": 7,
            "phylum": 8,
            "kingdom": 9,
        }
        return status_score, rank_order.get(rank_value, 20), numeric


class _MissingEntityDict(dict):
    def __missing__(self, key):
        entity = Entity(str(key), str(key), [str(key)], [], None)
        self[key] = entity
        return entity


class TaxRefKnowledgeBase(KnowledgeBase):
    def __init__(
        self,
        file_path=(
            "http://taxonerd.texttechnologylab.org/taxref/taxref_v17.jsonl",
            "taxref_v17.jsonl",
        ),
        prefix="TAXREF:",
    ):
        super().__init__(file_path, prefix)


class NCBIKnowledgeBase(KnowledgeBase):
    def __init__(
        self,
        file_path=(
            "http://taxonerd.texttechnologylab.org/ncbi/ncbi_taxonomy_20240522.jsonl",
            "ncbi_taxonomy_20240522.jsonl",
        ),
        prefix="NCBI:",
    ):
        super().__init__(file_path, prefix)


class NCBILiteKnowledgeBase(KnowledgeBase):
    def __init__(
        self,
        file_path=(
                "http://taxonerd.texttechnologylab.org/ncbi/ncbi_taxonomy_20240522.jsonl",
                "ncbi_taxonomy_20240522.jsonl",
        ),
        prefix="NCBI:",
    ):
        super().__init__(file_path, prefix)
