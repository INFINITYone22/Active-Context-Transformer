from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional


class MemoryCommandType(str, Enum):
    STORE = "STORE"
    RETRIEVE = "RETRIEVE"


@dataclass
class ContextBlock:
    id: str
    content: str
    summary: str
    type: str
    timestamp: str
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "ContextBlock":
        return ContextBlock(
            id=data["id"],
            content=data["content"],
            summary=data["summary"],
            type=data["type"],
            timestamp=data["timestamp"],
            tags=list(data.get("tags", [])),
        )


@dataclass
class MemoryCommand:
    type: MemoryCommandType
    raw: str
    block_id: Optional[str] = None
    summary: Optional[str] = None
    content_type: Optional[str] = None
    content: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class ProcessResult:
    cleaned_text: str
    stored_blocks: List[ContextBlock] = field(default_factory=list)
    retrieved_blocks: List[ContextBlock] = field(default_factory=list)
    commands: List[MemoryCommand] = field(default_factory=list)