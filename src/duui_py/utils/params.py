"""Shared parameter parsing utilities for DUUI-Py annotators.

Eliminates the duplicated inline _param_str/_param_bool/_param_int/_param_float
functions that every annotator's process() method redefines.
"""

from __future__ import annotations

import json
import os
from typing import Any


def param_str(params: dict[str, Any], key: str, default: str = "") -> str:
    val = params.get(key)
    return str(val).strip() if val is not None else default


def param_bool(params: dict[str, Any], key: str, default: bool = False) -> bool:
    val = params.get(key)
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


def param_int(
    params: dict[str, Any], key: str, default: int, minimum: int = 1
) -> int:
    try:
        return max(minimum, int(params.get(key, default)))
    except (TypeError, ValueError):
        return default


def param_float(params: dict[str, Any], key: str, default: float) -> float:
    val = params.get(key)
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def param_csv(
    params: dict[str, Any], key: str, default: tuple[str, ...]
) -> tuple[str, ...]:
    val = params.get(key)
    if val is None:
        return default
    if isinstance(val, str):
        raw = [item.strip() for item in val.split(",")]
    elif isinstance(val, (list, tuple, set)):
        raw = [str(item).strip() for item in val]
    else:
        raw = [str(val).strip()]
    return tuple(item for item in raw if item) or default


def param_csv_lower(
    params: dict[str, Any], key: str, default: tuple[str, ...]
) -> tuple[str, ...]:
    return tuple(item.lower() for item in param_csv(params, key, default))


def param_json_list(params: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """Parse a parameter that may be a JSON array string, a list, or a comma-separated string."""
    val = params.get(key)
    if val is None:
        return default
    if isinstance(val, str):
        text = val.strip()
        if not text or text == "[]":
            return ()
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            decoded = [item.strip().strip("'\"") for item in text.strip("[]").split(",") if item.strip()]
        if isinstance(decoded, list):
            return tuple(str(item).strip() for item in decoded if str(item).strip())
        return (str(decoded).strip(),)
    if isinstance(val, (list, tuple, set)):
        return tuple(str(item).strip().strip("'\"") for item in val if str(item).strip())
    return (str(val).strip(),)


def param_enum(
    params: dict[str, Any],
    key: str,
    allowed: tuple[str, ...],
    default: str,
    aliases: dict[str, str] | None = None,
) -> str:
    raw = param_str(params, key, default).strip().lower().replace("_", "-")
    if aliases:
        raw = aliases.get(raw, raw)
    return raw if raw in allowed else default


def resolve_prefer_gpu(parameter_value: object | None = None) -> bool:
    """Detect whether GPU should be preferred, from parameter or environment."""
    if parameter_value is not None:
        if isinstance(parameter_value, bool):
            return parameter_value
        return str(parameter_value).strip().lower() in {"1", "true", "yes", "y", "on"}
    for env_var in ("CUDA_VISIBLE_DEVICES", "CUDA_DEVICE_ORDER"):
        if os.environ.get(env_var, "").strip():
            return True
    try:
        import torch  # noqa: F401
        return torch.cuda.is_available()
    except Exception:
        pass
    try:
        import spacy  # noqa: F401
        spacy.prefer_gpu()
        return True
    except Exception:
        pass
    return False
