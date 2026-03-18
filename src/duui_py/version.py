from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def distribution_version() -> str:
    try:
        return version("duui-py")
    except PackageNotFoundError:
        return "0.0.0"

