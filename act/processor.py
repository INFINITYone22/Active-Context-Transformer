from __future__ import annotations

from typing import List

from .models import ContextBlock, MemoryCommand, MemoryCommandType, ProcessResult
from .parsing import extract_memory_commands, strip_spans
from .storage import JsonStorage
from .utils import iso_timestamp


class ACTProcessor:
    def __init__(self, storage: JsonStorage | None = None) -> None:
        self.storage = storage or JsonStorage()

    def process_model_output(self, model_output_text: str) -> ProcessResult:
        commands, spans = extract_memory_commands(model_output_text)
        stored_blocks: List[ContextBlock] = []
        retrieved_blocks: List[ContextBlock] = []

        for cmd in commands:
            if cmd.type == MemoryCommandType.STORE:
                block = ContextBlock(
                    id=cmd.block_id or "",
                    content=cmd.content or "",
                    summary=cmd.summary or "",
                    type=cmd.content_type or "generic",
                    timestamp=iso_timestamp(),
                    tags=cmd.tags,
                )
                self.storage.upsert_block(block)
                stored_blocks.append(block)
            elif cmd.type == MemoryCommandType.RETRIEVE:
                if not cmd.block_id:
                    continue
                block = self.storage.get_block(cmd.block_id)
                if block is not None:
                    retrieved_blocks.append(block)

        cleaned = strip_spans(model_output_text, spans)
        return ProcessResult(
            cleaned_text=cleaned.strip(),
            stored_blocks=stored_blocks,
            retrieved_blocks=retrieved_blocks,
            commands=commands,
        )