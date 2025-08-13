from __future__ import annotations

from pathlib import Path

from act.models import ContextBlock
from act.storage import JsonStorage


def test_storage_crud(tmp_path: Path) -> None:
    store = JsonStorage(storage_path=tmp_path / "store.json")
    block = ContextBlock(
        id="test1",
        content="content",
        summary="summary",
        type="note",
        timestamp="2020-01-01T00:00:00Z",
        tags=["a", "b"],
    )
    store.upsert_block(block)

    fetched = store.get_block("test1")
    assert fetched is not None
    assert fetched.id == "test1"

    listed = store.list_blocks(query="cont")
    assert any(b.id == "test1" for b in listed)

    removed = store.delete_block("test1")
    assert removed is True
    assert store.get_block("test1") is None