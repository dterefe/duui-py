from __future__ import annotations

from typing import Any

from duui_py.models.duui import FeatureStructureKeyRef, FeatureStructureNode, FsRec, UimaValueOrKeyRef


def build_feature_structures(nodes: list[FeatureStructureNode]) -> list[FsRec]:
    keys = [n.key for n in nodes]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate FeatureStructureNode.key")

    key_to_id: dict[str, int] = {n.key: i + 1 for i, n in enumerate(nodes)}

    def encode(v: UimaValueOrKeyRef) -> Any:
        if isinstance(v, FeatureStructureKeyRef):
            if v.key not in key_to_id:
                raise ValueError(f"unknown FeatureStructureKeyRef.key: {v.key}")
            return {"$ref": key_to_id[v.key]}
        if isinstance(v, list):
            return [encode(x) for x in v]
        return v

    out: list[FsRec] = []
    for n in nodes:
        out.append(
            FsRec(
                id=key_to_id[n.key],
                ref=n.ref,
                type=n.type,
                begin=n.begin,
                end=n.end,
                features={k: encode(v) for k, v in n.features.items()},
            )
        )
    return out
