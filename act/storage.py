from __future__ import annotations

import threading
from pathlib import Path
from typing import Dict, List, Optional

from filelock import FileLock

from .models import ContextBlock
from .utils import dump_json_file, get_default_store_path, load_json_file


class JsonStorage:
    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self._path: Path = (storage_path or get_default_store_path()).resolve()
        self._lock_path: Path = self._path.with_suffix(self._path.suffix + ".lock")
        self._lock = FileLock(str(self._lock_path))
        self._in_memory_cache: Dict[str, ContextBlock] = {}
        self._cache_lock = threading.Lock()
        self._load_into_cache()

    @property
    def path(self) -> Path:
        return self._path

    def _load_into_cache(self) -> None:
        with self._lock:
            data = load_json_file(self._path) or {"version": 1, "blocks": {}}
            blocks = data.get("blocks", {})
            parsed: Dict[str, ContextBlock] = {}
            for block_id, block_data in blocks.items():
                try:
                    parsed[block_id] = ContextBlock.from_dict(block_data)
                except Exception:
                    # Skip malformed entries
                    continue
            with self._cache_lock:
                self._in_memory_cache = parsed

    def _save_cache(self) -> None:
        with self._lock:
            with self._cache_lock:
                serializable = {
                    "version": 1,
                    "blocks": {bid: block.to_dict() for bid, block in self._in_memory_cache.items()},
                }
            dump_json_file(self._path, serializable)

    def upsert_block(self, block: ContextBlock) -> None:
        with self._cache_lock:
            self._in_memory_cache[block.id] = block
        self._save_cache()

    def get_block(self, block_id: str) -> Optional[ContextBlock]:
        with self._cache_lock:
            return self._in_memory_cache.get(block_id)

    def delete_block(self, block_id: str) -> bool:
        removed = False
        with self._cache_lock:
            if block_id in self._in_memory_cache:
                del self._in_memory_cache[block_id]
                removed = True
        if removed:
            self._save_cache()
        return removed

    def list_blocks(self, query: Optional[str] = None, tag: Optional[str] = None) -> List[ContextBlock]:
        with self._cache_lock:
            blocks = list(self._in_memory_cache.values())
        if query:
            q = query.lower()
            blocks = [
                b for b in blocks if q in b.id.lower() or q in b.summary.lower() or q in b.content.lower()
            ]
        if tag:
            t = tag.lower()
            blocks = [b for b in blocks if any(t == tg.lower() for tg in b.tags)]
        # Sort by timestamp descending
        return sorted(blocks, key=lambda b: b.timestamp, reverse=True)

    def clear(self) -> None:
        with self._cache_lock:
            self._in_memory_cache.clear()
        self._save_cache()