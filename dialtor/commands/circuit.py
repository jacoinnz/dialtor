"""Circuit management commands."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from dialtor.cli import handle_errors
from dialtor.core.circuit_manager import CircuitManager
from dialtor.core.controller import TorController
from dialtor.utils.config_loader import ConfigLoader

app = typer.Typer(help="Manage Tor circuits")
console = Console()


@app.command()
@handle_errors
def list(
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    List all active Tor circuits.

    Displays a table showing circuit IDs, status, paths (relay hops),
    and purpose for all active circuits.
    """
    # Load configuration
    config = ConfigLoader.load_with_env_override()
    if port:
        config.connection.control_port = port
    if password:
        config.connection.password = password

    with TorController(
        port=config.connection.control_port, password=config.connection.password
    ) as controller:
        manager = CircuitManager(controller)
        circuits = manager.list_circuits()

        if not circuits:
            console.print("[yellow]No active circuits found[/yellow]")
            return

        # Create table
        table = Table(title=f"Active Circuits ({len(circuits)})", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Path", style="white")
        table.add_column("Purpose", style="blue")
        table.add_column("Age", style="yellow")

        for circuit in circuits:
            # Format status with color
            status_color = {
                "BUILT": "green",
                "LAUNCHED": "yellow",
                "EXTENDED": "cyan",
                "FAILED": "red",
                "CLOSED": "dim",
            }.get(circuit.status.value, "white")

            status_display = f"[{status_color}]{circuit.status.value}[/{status_color}]"

            # Format age
            age_seconds = circuit.age_seconds
            if age_seconds < 60:
                age_display = f"{age_seconds}s"
            elif age_seconds < 3600:
                age_display = f"{age_seconds // 60}m"
            else:
                age_display = f"{age_seconds // 3600}h"

            table.add_row(
                circuit.id, status_display, circuit.path_string, circuit.purpose, age_display
            )

        console.print(table)


@app.command()
@handle_errors
def create(
    exit_country: Optional[str] = typer.Option(
        None, "--exit-country", help="Exit node country code (e.g., US, DE)"
    ),
    relays: Optional[str] = typer.Option(
        None, "--relays", help="Comma-separated relay fingerprints to use for circuit path"
    ),
    hops: int = typer.Option(3, "--hops", help="Number of hops in circuit"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Create a new Tor circuit.

    Creates a new circuit with the specified number of hops.
    Optionally specify an exit node country or specific relays to use.

    Examples:
        dialtor circuit create --exit-country DE
        dialtor circuit create --relays AAAA1111...,BBBB2222...,CCCC3333...
    """
    # Load configuration
    config = ConfigLoader.load_with_env_override()
    if port:
        config.connection.control_port = port
    if password:
        config.connection.password = password

    # Parse relays if provided
    relay_list = None
    if relays:
        relay_list = [r.strip() for r in relays.split(",")]

    with console.status(
        f"[bold green]Creating circuit with {hops} hops...", spinner="dots"
    ):
        with TorController(
            port=config.connection.control_port, password=config.connection.password
        ) as controller:
            manager = CircuitManager(controller)

            # Create circuit
            circuit = manager.create_circuit(
                hops=hops, exit_country=exit_country, relays=relay_list
            )

            console.print(f"\n[green]✓[/green] Circuit created successfully!")
            console.print(f"  Circuit ID: [cyan]{circuit.id}[/cyan]")
            console.print(f"  Status: [green]{circuit.status.value}[/green]")
            console.print(f"  Path: {circuit.path_string}")


@app.command()
@handle_errors
def close(
    circuit_id: str = typer.Argument(..., help="Circuit ID to close"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Close a specific circuit.

    Closes the circuit with the given ID.
    """
    # Load configuration
    config = ConfigLoader.load_with_env_override()
    if port:
        config.connection.control_port = port
    if password:
        config.connection.password = password

    with TorController(
        port=config.connection.control_port, password=config.connection.password
    ) as controller:
        manager = CircuitManager(controller)

        # Check if circuit exists
        circuit = manager.get_circuit_info(circuit_id)
        if not circuit:
            console.print(f"[red]Circuit {circuit_id} not found[/red]")
            raise typer.Exit(1)

        # Close circuit
        manager.close_circuit(circuit_id)
        console.print(f"[green]✓[/green] Circuit {circuit_id} closed successfully")


@app.command()
@handle_errors
def info(
    circuit_id: str = typer.Argument(..., help="Circuit ID to inspect"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Show detailed information about a circuit.

    Displays detailed information about the specified circuit including
    all relay hops and their properties.
    """
    # Load configuration
    config = ConfigLoader.load_with_env_override()
    if port:
        config.connection.control_port = port
    if password:
        config.connection.password = password

    with TorController(
        port=config.connection.control_port, password=config.connection.password
    ) as controller:
        manager = CircuitManager(controller)

        circuit = manager.get_circuit_info(circuit_id)
        if not circuit:
            console.print(f"[red]Circuit {circuit_id} not found[/red]")
            raise typer.Exit(1)

        # Display circuit info
        console.print(f"\n[bold]Circuit {circuit.id}[/bold]")
        console.print(f"  Status: [green]{circuit.status.value}[/green]")
        console.print(f"  Purpose: {circuit.purpose}")
        console.print(f"  Created: {circuit.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"  Age: {circuit.age_seconds} seconds")

        # Display path
        console.print("\n[bold]Path:[/bold]")
        for i, hop in enumerate(circuit.path, 1):
            console.print(
                f"  {i}. {hop.nickname} ({hop.fingerprint[:16]}...)"
                + (f" - {hop.country_code}" if hop.country_code else "")
            )
