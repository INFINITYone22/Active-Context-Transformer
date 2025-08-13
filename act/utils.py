from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console


console = Console()


def iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_default_store_path() -> Path:
    env_path = os.environ.get("ACT_STORE_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    cwd = Path.cwd()
    data_dir = cwd / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "context_store.json"


def load_json_file(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)