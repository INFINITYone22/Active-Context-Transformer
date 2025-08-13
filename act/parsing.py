from __future__ import annotations

import re
from typing import List, Sequence, Tuple

from .models import MemoryCommand, MemoryCommandType


# Patterns for extracting commands
_CODE_FENCE_PATTERN = re.compile(r"```MEMORY_CMD\s*\n([\s\S]*?)\n```", re.MULTILINE)
_INLINE_PREFIX_PATTERN = re.compile(r"^\s*MEMORY_CMD:\s*(.+)$", re.MULTILINE)
_DIRECT_CMD_PATTERN = re.compile(r"^\s*(STORE|RETRIEVE)\|.+$", re.MULTILINE)


def _parse_command_text(cmd_text: str) -> MemoryCommand:
    raw = cmd_text.strip()
    if not raw:
        raise ValueError("Empty command text")
    if raw.startswith("STORE|"):
        parts = raw.split("|")
        if len(parts) < 6:
            raise ValueError("STORE command requires 6 fields: STORE|id|summary|type|content|tag1,tag2")
        _, block_id, summary, content_type, content, tags_csv = parts[:6]
        tags = [t.strip() for t in tags_csv.split(",") if t.strip()]
        return MemoryCommand(
            type=MemoryCommandType.STORE,
            raw=raw,
            block_id=block_id.strip(),
            summary=summary.strip(),
            content_type=content_type.strip(),
            content=content,
            tags=tags,
        )
    if raw.startswith("RETRIEVE|"):
        parts = raw.split("|")
        if len(parts) < 2:
            raise ValueError("RETRIEVE command requires 2 fields: RETRIEVE|id")
        _, block_id = parts[:2]
        return MemoryCommand(
            type=MemoryCommandType.RETRIEVE,
            raw=raw,
            block_id=block_id.strip(),
        )
    raise ValueError(f"Unknown command: {raw}")


def extract_memory_commands(text: str) -> Tuple[List[MemoryCommand], List[Tuple[int, int]]]:
    commands: List[MemoryCommand] = []
    spans: List[Tuple[int, int]] = []

    # 1) Code-fenced blocks
    for match in _CODE_FENCE_PATTERN.finditer(text):
        cmd_text = match.group(1)
        try:
            commands.append(_parse_command_text(cmd_text))
            spans.append((match.start(), match.end()))
        except Exception:
            # Skip malformed commands, but still remove the block
            spans.append((match.start(), match.end()))

    # 2) Inline prefix
    for match in _INLINE_PREFIX_PATTERN.finditer(text):
        cmd_text = match.group(1)
        try:
            commands.append(_parse_command_text(cmd_text))
            spans.append((match.start(), match.end()))
        except Exception:
            spans.append((match.start(), match.end()))

    # 3) Direct commands (avoid duplicates where already captured)
    # Build a set of ranges already covered to avoid double counting
    covered = _merge_spans(spans)
    for match in _DIRECT_CMD_PATTERN.finditer(text):
        span = (match.start(), match.end())
        if _is_span_covered(span, covered):
            continue
        cmd_text = match.group(0)
        try:
            commands.append(_parse_command_text(cmd_text))
            spans.append(span)
        except Exception:
            spans.append(span)

    return commands, _merge_spans(spans)


def strip_spans(text: str, spans: Sequence[Tuple[int, int]]) -> str:
    if not spans:
        return text
    # Remove from the end to preserve indices
    cleaned = text
    for start, end in sorted(spans, key=lambda s: s[0], reverse=True):
        cleaned = cleaned[:start] + cleaned[end:]
    return cleaned


def _merge_spans(spans: Sequence[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not spans:
        return []
    sorted_spans = sorted(spans, key=lambda s: s[0])
    merged: List[Tuple[int, int]] = []
    current_start, current_end = sorted_spans[0]
    for start, end in sorted_spans[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end
    merged.append((current_start, current_end))
    return merged


def _is_span_covered(span: Tuple[int, int], covered_spans: Sequence[Tuple[int, int]]) -> bool:
    s, e = span
    for cs, ce in covered_spans:
        if s >= cs and e <= ce:
            return True
    return False