from __future__ import annotations

from pathlib import Path

from act.processor import ACTProcessor
from act.storage import JsonStorage


def test_processor_store_and_retrieve(tmp_path: Path) -> None:
    storage = JsonStorage(storage_path=tmp_path / "store.json")
    processor = ACTProcessor(storage=storage)

    text = (
        "Intro\n"
        "```MEMORY_CMD\n"
        "STORE|a1|alpha summary|note|alpha content|x,y\n"
        "```\n"
        "More.\n"
    )
    result = processor.process_model_output(text)
    assert len(result.stored_blocks) == 1
    assert result.stored_blocks[0].id == "a1"
    assert "STORE|" not in result.cleaned_text

    # Retrieve
    result2 = processor.process_model_output("MEMORY_CMD: RETRIEVE|a1")
    assert len(result2.retrieved_blocks) == 1
    assert result2.retrieved_blocks[0].id == "a1"