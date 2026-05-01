"""Script execution commands."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from dialtor.cli import handle_errors
from dialtor.scripts.runner import get_example_script_path, list_example_scripts, run_script

app = typer.Typer(help="Run Python scripts with dialtor API")
console = Console()


@app.command()
@handle_errors
def run(
    script_path: str = typer.Argument(..., help="Path to Python script"),
) -> None:
    """
    Execute a Python script with dialtor API context.

    The script will have access to:
      - tor: Dialtor API instance (already connected)
      - ctx: ScriptContext with logging utilities

    Example script:
        # my_automation.py
        ctx.log("Creating US circuit...")
        circuit = tor.create_circuit(exit_country="US")
        ctx.log(f"Created circuit: {circuit.id}")

    Usage:
        dialtor script run my_automation.py
        dialtor script run examples/auto_rotate.py
    """
    path = Path(script_path)

    # Check if it's an example script name
    if not path.exists() and not "/" in script_path and not "\\" in script_path:
        # Try to find as example script
        example_path = get_example_script_path(script_path)
        if example_path:
            path = example_path
            console.print(f"Running example script: [cyan]{script_path}[/cyan]")
        else:
            console.print(f"[red]Error:[/red] Script not found: {script_path}")
            console.print(
                f"\nTip: Run [cyan]dialtor script list[/cyan] to see available examples"
            )
            raise typer.Exit(1)

    if not path.exists():
        console.print(f"[red]Error:[/red] Script not found: {script_path}")
        raise typer.Exit(1)

    console.print(f"\nExecuting: [cyan]{path}[/cyan]")
    console.print("=" * 60)

    # Run the script
    exit_code = run_script(path)

    console.print("=" * 60)

    if exit_code == 0:
        console.print("\n[green]✓[/green] Script completed successfully")
    else:
        console.print(f"\n[red]✗[/red] Script failed with exit code: {exit_code}")
        raise typer.Exit(exit_code)


@app.command()
@handle_errors
def list() -> None:
    """
    List available example scripts.

    Shows all built-in example scripts that demonstrate
    various dialtor automation capabilities.
    """
    examples = list_example_scripts()

    if not examples:
        console.print("[yellow]No example scripts found[/yellow]")
        return

    # Create table
    table = Table(title=f"Example Scripts ({len(examples)})", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")

    for name, description in sorted(examples.items()):
        table.add_row(name, description)

    console.print(table)

    console.print("\n[dim]Usage:[/dim]")
    console.print("  [cyan]dialtor script run <name>[/cyan]       # Run by name")
    console.print("  [cyan]dialtor script show <name>[/cyan]      # View source code")


@app.command()
@handle_errors
def show(
    script_name: str = typer.Argument(..., help="Example script name"),
) -> None:
    """
    Show the source code of an example script.

    Displays the script with syntax highlighting so you can
    understand what it does before running it.

    Usage:
        dialtor script show auto_rotate
        dialtor script show country_routing
    """
    script_path = get_example_script_path(script_name)

    if not script_path:
        console.print(f"[red]Error:[/red] Example script not found: {script_name}")
        console.print(
            "\nRun [cyan]dialtor script list[/cyan] to see available examples"
        )
        raise typer.Exit(1)

    # Read script
    try:
        code = script_path.read_text()
    except Exception as e:
        console.print(f"[red]Error reading script:[/red] {e}")
        raise typer.Exit(1)

    # Display with syntax highlighting
    console.print(f"\n[bold]Example Script:[/bold] [cyan]{script_name}[/cyan]")
    console.print(f"[dim]Path: {script_path}[/dim]\n")

    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)

    console.print(f"\n[dim]Run with:[/dim] [cyan]dialtor script run {script_name}[/cyan]")
