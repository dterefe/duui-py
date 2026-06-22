"""TaxoNERD msgpack-Lua annotator.

This version intentionally runs the same Abrami TaxoNERD ``find_in_text``
procedure as the legacy Lua/JSON baseline. The evaluation then measures the
DUUI transport/procedural path instead of changing the model or query semantics.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from time import time

from duui_py.annotator import DuuiAnnotator
from duui_py.app import create_app
from duui_py.codecs.msgpack_lua import MsgPackLuaCodec
from duui_py.errors import unprocessable
from duui_py.logging import logger
from duui_py.models import (
    AnnotatorConfig,
    AnnotatorDescriptor,
    AnnotatorMeta,
    Domain,
    DomainSpec,
    DuuiError,
    DuuiResult,
    IODescriptor,
    V1RequestEnvelope,
)
from duui_py.models.uima import sofa_text_value
from duui_py.utils.params import (
    param_bool, param_float, param_json_list, param_str, resolve_prefer_gpu,
)

from _taxonerd_shared import (
    ANNOTATION_COMMENT_TYPE,
    TAXON_TYPE,
    StrategyResult,
    legacy_surface_taxons_and_comments,
    load_taxonerd,
    run_legacy_procedure,
)

# ---------------------------------------------------------------------------
# Annotator
# ---------------------------------------------------------------------------
class TaxoNERDAnnotator(DuuiAnnotator[V1RequestEnvelope, object]):
    """DUUI annotator wrapping TaxoNERD taxonomic NER + linking pipeline.

    The only supported processing path is the Abrami TaxoNERD full procedure.
    """

    config = AnnotatorConfig(
        meta=AnnotatorMeta(meta={"source": "TTLab-UIMA/taxoNERD migration (optimized)"}),
        descriptor=AnnotatorDescriptor(
            name="taxonerd-msgpack-lua",
            version="1.3.0",
            input=IODescriptor(
                text=DomainSpec(
                    default=Domain(
                        mimeType="text/plain; charset=utf-8",
                        languages=["x-unspecified"],
                    )
                )
            ),
            output=IODescriptor(
                types={
                    "Taxon": [TAXON_TYPE],
                    "AnnotationComment": [ANNOTATION_COMMENT_TYPE],
                },
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
            "model": {"type": "string", "default": "en_ner_eco_md", "description": "TaxoNERD model alias."},
            "model_name": {"type": "string", "description": "Alias for model."},
            "linking": {"type": "string", "default": "gbif_backbone", "description": "TaxoNERD linker alias."},
            "linker_name": {"type": "string", "description": "Alias for linking."},
            "prefer_gpu": {"type": "boolean", "default": False, "description": "Auto-detected if not set."},
            "threshold": {"type": "number", "default": 0.7},
            "exclude": {"type": ["array", "string"], "default": ["tagger", "parser", "taxo_abbrev_detector", "taxon_linker", "pysbd_sentencizer"]},
            "allow_unlinked": {"type": "boolean", "default": False, "description": "Allow linker none without returning an error."},
        },
    )

    def codec(self) -> MsgPackLuaCodec:
        return MsgPackLuaCodec(self.config)

    async def startup(self) -> None:
        await asyncio.to_thread(_preload_runtime)
        logger().info("TaxoNERD runtime preloaded successfully (optimized)")

    async def process(self, doc: V1RequestEnvelope) -> AsyncIterator[object]:
        started = time()
        params = doc.parameters
        text = sofa_text_value(doc.sofa) or ""

        # -- resolve parameters ---------------------------------------------------
        model_raw = param_str(params, "model") or param_str(params, "model_name") or "en_ner_eco_md"
        model = {"biobert": "en_ner_eco_biobert", "biobert_weak": "en_ner_eco_biobert_weak",
                 "md": "en_ner_eco_md", "md_weak": "en_ner_eco_md_weak"}.get(model_raw, model_raw)

        linker_raw = param_str(params, "linking") or param_str(params, "linker_name") or "gbif_backbone"
        linker_map = {"gbif": "gbif_backbone", "gbif_backbone": "gbif_backbone",
                       "taxref": "taxref", "ncbi": "ncbi_taxonomy", "ncbi_taxonomy": "ncbi_taxonomy",
                       "ncbi_lite": "ncbi_taxonomy_lite", "ncbi_taxonomy_lite": "ncbi_taxonomy_lite",
                       "none": None, "": None}
        if linker_raw not in linker_map:
            unprocessable("Unsupported TaxoNERD linker.", linker=linker_raw, supported=sorted(linker_map))
        linker = linker_map[linker_raw]

        prefer_gpu = resolve_prefer_gpu(params.get("prefer_gpu"))
        threshold = param_float(params, "threshold", 0.7)

        exclude_val = params.get("exclude")
        if exclude_val is None:
            exclude = ("tagger", "parser", "taxo_abbrev_detector", "taxon_linker", "pysbd_sentencizer")
        elif isinstance(exclude_val, str):
            exclude = param_json_list(params, "exclude", (
                "tagger", "parser", "taxo_abbrev_detector", "taxon_linker", "pysbd_sentencizer"))
        else:
            exclude = tuple(str(item) for item in exclude_val) if exclude_val else ()

        logger().trace(
            f"TaxoNERD process() entry: len={len(text)} fs={len(doc.fs)} "
            f"model={model} linker={linker}"
        )
        logger().info(
            f"TaxoNERD process started: model={model} linker={linker} text_length={len(text)}"
        )

        if linker is None and not param_bool(params, "allow_unlinked", False):
            logger().error("TaxoNERD: linker is None and allow_unlinked is False")
            unprocessable("TaxoNERD runtime evaluation requires GBIF linking.")

        logger().trace(
            "TaxoNERD process request configured",
            model=model, linker=linker,
            threshold=threshold, exclude=list(exclude),
            text_length=len(text), fs_count=len(doc.fs),
        )

        # -- run strategy in thread -----------------------------------------------
        async def run_taxonerd_strategy() -> StrategyResult:
            strategy_started = time()
            logger().info("TaxoNERD full procedure execution starting")
            try:
                return await asyncio.to_thread(
                    run_legacy_procedure,
                    text, model, linker, threshold, exclude, prefer_gpu,
                )
            finally:
                elapsed = (time() - strategy_started) * 1000
                logger().info(f"TaxoNERD strategy completed in {elapsed:.1f} ms")
                logger().trace_backend_operation(
                    "taxonerd",
                    "strategy.execute",
                    strategy="legacy-procedure",
                    elapsed_ms=elapsed,
                    model=model,
                    linker=linker or "none",
                )
                logger().metric(
                    "processing",
                    "taxonerd_strategy_ms",
                    elapsed,
                    "milliseconds",
                    tags={"annotator": "taxonerd", "strategy": "legacy-procedure"},
                )

        try:
            result = await run_taxonerd_strategy()
        except Exception as exc:
            logger().error(
                "TaxoNERD strategy failed: strategy=legacy-procedure "
                f"exception={type(exc).__name__} detail={str(exc)}",
            )
            logger().error(
                "TaxoNERD strategy failed",
                strategy="legacy-procedure", exception=type(exc).__name__, detail=str(exc),
            )
            yield DuuiResult.model_construct(
                annotations=[], feature_structures=[], meta=None,
                modification_meta=None,
                errors=[DuuiError(message=str(exc), title="TaxoNERD Processing Error",
                                  status=500, retryable=False)],
            )
            return

        # -- metrics --------------------------------------------------------------
        elapsed_ms = int((time() - started) * 1000)
        logger().info(
            f"TaxoNERD completed in {elapsed_ms} ms: "
            f"{len(result.taxons)} taxons, {result.windows} windows, {result.mentions} mentions",
        )
        logger().debug_annotation_count(
            "taxonerd",
            len(result.taxons),
            counts={
                "taxons": len(result.taxons),
                "windows": result.windows,
                "mentions": result.mentions,
            },
            strategy="legacy-procedure",
            model=model,
        )
        logger().trace_annotation_result(
            "taxonerd",
            result.taxons,
            counts={
                "taxons": len(result.taxons),
                "windows": result.windows,
                "mentions": result.mentions,
            },
            strategy="legacy-procedure",
            model=model,
            linker=linker or "none",
            metrics=result.metrics,
            elapsed_ms=elapsed_ms,
        )

        logger().metric(
            "processing",
            "taxonerd_processing_ms",
            elapsed_ms,
            "milliseconds",
            tags={"annotator": "taxonerd", "strategy": "legacy-procedure"},
        )
        logger().metric(
            "processing",
            "taxonerd_taxon_matches",
            len(result.taxons),
            "count",
            tags={"linking": linker or "none", "model": model, "strategy": "legacy-procedure"},
        )
        logger().metric("processing", "taxonerd_input_windows", result.windows, "count", tags={"strategy": "legacy-procedure"})
        logger().metric("processing", "taxonerd_input_mentions", result.mentions, "count", tags={"strategy": "legacy-procedure"})

        metric_attrs = {"linking": linker or "none", "model": model, "strategy": "legacy-procedure"}
        for metric_name, metric_value in result.metrics.items():
            if metric_name.endswith("_ms"):
                logger().metric("processing", f"taxonerd_{metric_name}", metric_value, "milliseconds", tags=metric_attrs)
            else:
                logger().metric("processing", f"taxonerd_{metric_name}", float(metric_value), "count", tags=metric_attrs)

        # -- build result ---------------------------------------------------------
        taxons, comments = legacy_surface_taxons_and_comments(result.taxons)
        yield DuuiResult.model_construct(
            annotations=taxons,
            feature_structures=comments,
            meta=None,
            modification_meta=None,
            errors=[], sofa=None,
        )
        logger().trace(f"TaxoNERD process() exit: {len(result.taxons)} taxons, {elapsed_ms} ms")

# ===================================================================
# App factory & startup
# ===================================================================
app = create_app(TaxoNERDAnnotator)


def _preload_runtime() -> None:
    """Preload model, linker, and candidate generator on startup."""
    exclude_raw = os.getenv("DUUI_TAXONERD_PRELOAD_EXCLUDE", "")
    exclude = (
        tuple(item.strip() for item in exclude_raw.split(",") if item.strip())
        if exclude_raw.strip()
        else ("tagger", "parser", "taxo_abbrev_detector", "taxon_linker", "pysbd_sentencizer")
    )
    model = os.getenv("DUUI_TAXONERD_PRELOAD_MODEL", "en_ner_eco_md")
    linker = os.getenv("DUUI_TAXONERD_PRELOAD_LINKER", "gbif_backbone")
    try:
        threshold = float(os.getenv("DUUI_TAXONERD_PRELOAD_THRESHOLD", "0.7"))
    except ValueError:
        threshold = 0.7
    prefer_gpu = resolve_prefer_gpu(None)
    load_taxonerd(model, linker, threshold, exclude, prefer_gpu)
