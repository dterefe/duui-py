"""Auto-generated namespace-mapped UIMA model package."""

from __future__ import annotations

import importlib
import pkgutil

UIMA_TYPE_TO_CLASS = {}
for modinfo in pkgutil.walk_packages(__path__, prefix=__name__ + '.'):
    if not modinfo.name.endswith('.types'):
        continue
    mod = importlib.import_module(modinfo.name)
    UIMA_TYPE_TO_CLASS.update(getattr(mod, 'UIMA_TYPE_TO_CLASS', {}))

def get_uima_model_class(type_name: str):
    return UIMA_TYPE_TO_CLASS.get(type_name)

__all__ = ['UIMA_TYPE_TO_CLASS', 'get_uima_model_class']
