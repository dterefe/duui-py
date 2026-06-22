"""Shared span-window utilities for DUUI-Py annotators.

Consolidates the duplicated span selection, window splitting, and overlap
logic from taxonerd-async and spacy-async annotators.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TextWindow:
    begin: int
    end: int
    text: str
    source_type: str = ""


def select_spans(
    items: list[Any],
    text_len: int,
    preferred_types: tuple[str, ...],
) -> list[tuple[int, int, str]]:
    """Select spans from feature structures, preferring types in order."""
    by_type: dict[str, list[tuple[int, int, str]]] = {}
    accepted = set(preferred_types)
    for item in items:
        type_name = getattr(item, "type", "")
        if type_name not in accepted:
            continue
        begin = getattr(item, "begin", None)
        end = getattr(item, "end", None)
        if begin is None or end is None:
            continue
        begin_i = max(0, int(begin))
        end_i = min(text_len, int(end))
        if begin_i >= end_i:
            continue
        by_type.setdefault(type_name, []).append((begin_i, end_i, type_name))
    for span_type in preferred_types:
        spans = sorted(set(by_type.get(span_type, [])))
        if spans:
            return spans
    return []


def split_long_range(
    text: str,
    begin: int,
    end: int,
    max_chars: int,
    overlap_chars: int,
    source_type: str = "",
) -> Iterator[TextWindow]:
    """Split a long range into overlapping windows."""
    cursor = begin
    while cursor < end:
        hard_end = min(end, cursor + max_chars)
        if hard_end < end:
            split_at = max(
                text.rfind("\n", cursor, hard_end),
                text.rfind(" ", cursor, hard_end),
            )
            if split_at > cursor + max_chars // 2:
                hard_end = split_at
        chunk = text[cursor:hard_end]
        if chunk.strip():
            yield TextWindow(cursor, hard_end, chunk, source_type)
        if hard_end >= end:
            break
        cursor = max(cursor + 1, hard_end - overlap_chars)


def build_windows(
    text: str,
    spans: list[tuple[int, int, str]],
    max_chars: int,
    overlap_chars: int,
    merge_spans: bool = False,
) -> list[TextWindow]:
    """Build windows from span annotations with optional merging."""
    if not merge_spans:
        out: list[TextWindow] = []
        for begin, end, source_type in spans:
            if end - begin > max_chars:
                out.extend(
                    split_long_range(text, begin, end, max_chars, overlap_chars, source_type)
                )
                continue
            chunk = text[begin:end]
            if chunk.strip():
                out.append(TextWindow(begin, end, chunk, source_type))
        return out

    # merge contiguous spans
    out: list[TextWindow] = []
    cur_begin: int | None = None
    cur_end: int | None = None
    cur_type = ""
    for begin, end, source_type in spans:
        if cur_begin is None or cur_end is None:
            cur_begin, cur_end, cur_type = begin, end, source_type
            continue
        if end - cur_begin <= max_chars:
            cur_end = end
            if source_type not in cur_type:
                cur_type = f"{cur_type}+{source_type}"
            continue
        out.append(TextWindow(cur_begin, cur_end, text[cur_begin:cur_end], cur_type))
        cur_begin, cur_end, cur_type = begin, end, source_type
    if cur_begin is not None and cur_end is not None:
        out.append(TextWindow(cur_begin, cur_end, text[cur_begin:cur_end], cur_type))

    # split any merged windows that exceed max_chars
    split: list[TextWindow] = []
    for window in out:
        if window.end - window.begin > max_chars:
            split.extend(
                split_long_range(text, window.begin, window.end, max_chars, overlap_chars, window.source_type)
            )
        elif window.text.strip():
            split.append(window)
    return split
