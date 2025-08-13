from __future__ import annotations

from act.parsing import extract_memory_commands, strip_spans


def test_extract_from_code_fence() -> None:
    text = (
        "Here is a response.\n\n"
        "```MEMORY_CMD\n"
        "STORE|blk1|sum|note|hello world|a,b\n"
        "```\n\n"
        "And more text.\n"
    )
    commands, spans = extract_memory_commands(text)
    assert len(commands) == 1
    assert commands[0].raw.startswith("STORE|")
    cleaned = strip_spans(text, spans)
    assert "MEMORY_CMD" not in cleaned
    assert "STORE|" not in cleaned


def test_extract_inline_and_direct() -> None:
    text = (
        "Start\n"
        "MEMORY_CMD: RETRIEVE|blk1\n"
        "Some line\n"
        "STORE|blk2|s|t|c|x,y\n"
        "End\n"
    )
    commands, spans = extract_memory_commands(text)
    types = sorted([c.type.value for c in commands])
    assert types == ["RETRIEVE", "STORE"]
    cleaned = strip_spans(text, spans)
    assert "RETRIEVE|" not in cleaned
    assert "STORE|" not in cleaned