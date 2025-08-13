from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .models import ContextBlock
from .processor import ACTProcessor
from .storage import JsonStorage


class ProcessOutputRequest(BaseModel):
    text: str = Field(..., description="Raw model output text to process")


class StoreRequest(BaseModel):
    id: str
    summary: str
    type: str = "generic"
    content: str
    tags: List[str] = []


class BlockResponse(BaseModel):
    id: str
    summary: str
    type: str
    content: str
    timestamp: str
    tags: List[str]

    @staticmethod
    def from_block(block: ContextBlock) -> "BlockResponse":
        return BlockResponse(
            id=block.id,
            summary=block.summary,
            type=block.type,
            content=block.content,
            timestamp=block.timestamp,
            tags=list(block.tags),
        )


class ProcessOutputResponse(BaseModel):
    cleaned_text: str
    stored_blocks: List[BlockResponse]
    retrieved_blocks: List[BlockResponse]


app = FastAPI(title="Active Context Transformer (ACT)", version="0.1.0")
_storage = JsonStorage()
_processor = ACTProcessor(storage=_storage)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/process_output", response_model=ProcessOutputResponse)
async def process_output(req: ProcessOutputRequest) -> ProcessOutputResponse:
    result = _processor.process_model_output(req.text)
    return ProcessOutputResponse(
        cleaned_text=result.cleaned_text,
        stored_blocks=[BlockResponse.from_block(b) for b in result.stored_blocks],
        retrieved_blocks=[BlockResponse.from_block(b) for b in result.retrieved_blocks],
    )


@app.post("/store", response_model=BlockResponse)
async def store_block(req: StoreRequest) -> BlockResponse:
    # Reuse processor path to keep behavior consistent
    cmd_text = f"STORE|{req.id}|{req.summary}|{req.type}|{req.content}|{','.join(req.tags)}"
    result = _processor.process_model_output(cmd_text)
    if not result.stored_blocks:
        raise HTTPException(status_code=400, detail="Failed to store block")
    return BlockResponse.from_block(result.stored_blocks[0])


@app.get("/retrieve/{block_id}", response_model=BlockResponse)
async def retrieve_block(block_id: str) -> BlockResponse:
    block = _storage.get_block(block_id)
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    return BlockResponse.from_block(block)


@app.get("/blocks", response_model=List[BlockResponse])
async def list_blocks(query: Optional[str] = None, tag: Optional[str] = None) -> List[BlockResponse]:
    blocks = _storage.list_blocks(query=query, tag=tag)
    return [BlockResponse.from_block(b) for b in blocks]


@app.delete("/blocks/{block_id}")
async def delete_block(block_id: str) -> dict:
    removed = _storage.delete_block(block_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Block not found")
    return {"deleted": True, "id": block_id}


def main() -> None:
    import uvicorn

    uvicorn.run("act.server:app", host="0.0.0.0", port=8000, reload=False)