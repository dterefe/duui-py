from __future__ import annotations


def _mime_base(mime_type: str) -> str:
    return mime_type.split(";", 1)[0].strip().lower()


def matches_mime_type(pattern: str, actual: str) -> bool:
    if not pattern or not actual:
        return False

    actual_base = _mime_base(actual)
    if "/" not in actual_base:
        return False
    if "*" in actual_base:
        return False

    for raw in pattern.split("|"):
        p = _mime_base(raw)
        if "/" not in p:
            continue
        if p.endswith("/*"):
            major = p[:-2]
            if actual_base.startswith(major + "/"):
                return True
            continue
        if p == actual_base:
            return True

    return False

