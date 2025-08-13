from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from .processor import ACTProcessor
from .storage import JsonStorage
from .utils import get_default_store_path

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


def _get_storage(path: Optional[Path]) -> JsonStorage:
    if path is None:
        return JsonStorage()
    return JsonStorage(storage_path=path)


@app.command()
def process_output(
    input_file: Optional[Path] = typer.Option(
        None, "--input", "-i", exists=True, dir_okay=False, help="Path to a file containing model output to process."
    ),
    text: Optional[str] = typer.Option(None, "--text", help="Raw model output text to process. If omitted, reads stdin."),
    json_out: bool = typer.Option(False, "--json", help="Print full JSON result instead of just cleaned text."),
    store_path: Optional[Path] = typer.Option(None, "--store-path", help="Override path to the JSON storage file."),
):
    """Process model output, executing MEMORY_CMD directives and printing cleaned text or JSON result."""
    data: str
    if input_file is not None:
        data = input_file.read_text(encoding="utf-8")
    elif text is not None:
        data = text
    else:
        data = sys.stdin.read()

    processor = ACTProcessor(storage=_get_storage(store_path))
    result = processor.process_model_output(data)

    if json_out:
        payload = {
            "cleaned_text": result.cleaned_text,
            "stored_blocks": [b.to_dict() for b in result.stored_blocks],
            "retrieved_blocks": [b.to_dict() for b in result.retrieved_blocks],
            "commands": [vars(c) | {"type": c.type.value} for c in result.commands],
        }
        console.print_json(data=json.dumps(payload))
    else:
        console.print(result.cleaned_text)


@app.command()
def store(
    block_id: str = typer.Argument(..., help="Unique id for the context block"),
    summary: str = typer.Option(..., "--summary", "-s", help="Summary of the content"),
    content_type: str = typer.Option("generic", "--type", "-t", help="Type/category of the content"),
    content: str = typer.Option(..., "--content", "-c", help="Full content to store"),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
    store_path: Optional[Path] = typer.Option(None, "--store-path", help="Override path to the JSON storage file."),
):
    """Manually store a context block."""
    storage = _get_storage(store_path)
    processor = ACTProcessor(storage=storage)
    cmd_text = f"STORE|{block_id}|{summary}|{content_type}|{content}|{tags}"
    result = processor.process_model_output(cmd_text)
    if result.stored_blocks:
        console.print(f"Stored block: [bold green]{block_id}[/bold green]")
    else:
        console.print("No block stored.")


@app.command()
def retrieve(
    block_id: str = typer.Argument(..., help="Block id to retrieve"),
    store_path: Optional[Path] = typer.Option(None, "--store-path", help="Override path to the JSON storage file."),
):
    """Retrieve a stored context block by id."""
    storage = _get_storage(store_path)
    block = storage.get_block(block_id)
    if not block:
        console.print(f"[red]No block found with id '{block_id}'.[/red]")
        raise typer.Exit(code=1)
    console.print_json(data=json.dumps(block.to_dict()))


@app.command(name="list")
def list_blocks(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Text to search in id, summary, or content"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag"),
    store_path: Optional[Path] = typer.Option(None, "--store-path", help="Override path to the JSON storage file."),
):
    """List stored context blocks."""
    storage = _get_storage(store_path)
    blocks = storage.list_blocks(query=query, tag=tag)
    table = Table(title="Context Blocks", box=box.SIMPLE_HEAVY)
    table.add_column("ID")
    table.add_column("Type")
    table.add_column("Summary")
    table.add_column("Tags")
    table.add_column("Timestamp")
    for b in blocks:
        table.add_row(b.id, b.type, b.summary, ", ".join(b.tags), b.timestamp)
    console.print(table)


@app.command()
def delete(
    block_id: str = typer.Argument(..., help="Block id to delete"),
    store_path: Optional[Path] = typer.Option(None, "--store-path", help="Override path to the JSON storage file."),
):
    """Delete a context block by id."""
    storage = _get_storage(store_path)
    if storage.delete_block(block_id):
        console.print(f"Deleted block: [bold]{block_id}[/bold]")
    else:
        console.print(f"[yellow]No block found with id '{block_id}'.[/yellow]")


@app.command()
def clear(
    confirm: bool = typer.Option(False, "--yes", help="Confirm deletion of all blocks"),
    store_path: Optional[Path] = typer.Option(None, "--store-path", help="Override path to the JSON storage file."),
):
    """Clear all stored blocks."""
    if not confirm:
        console.print("[red]Refusing to clear without --yes[/red]")
        raise typer.Exit(code=1)
    storage = _get_storage(store_path)
    storage.clear()
    console.print("Cleared all blocks.")


@app.command()
def path() -> None:
    """Show the current storage file path."""
    console.print(str(get_default_store_path().resolve()))


def main() -> None:
    app()