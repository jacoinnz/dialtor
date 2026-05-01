"""Identity management commands."""

from datetime import datetime, timedelta
from typing import Optional

import typer
from rich.console import Console

from dialtor.cli import handle_errors
from dialtor.core.controller import TorController
from dialtor.utils.config_loader import ConfigLoader

app = typer.Typer(help="Manage Tor identity")
console = Console()

# Track last identity change (in-memory for now)
_last_identity_change: Optional[datetime] = None


@app.command()
@handle_errors
def new(
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Request a new Tor identity.

    Sends NEWNYM signal to Tor, which causes it to create new circuits
    for subsequent connections. This effectively gives you a new identity.

    Note: Tor enforces a 10-second rate limit on NEWNYM signals.
    """
    global _last_identity_change

    # Check rate limit (10 seconds)
    if _last_identity_change:
        elapsed = (datetime.now() - _last_identity_change).total_seconds()
        if elapsed < 10:
            wait_time = int(10 - elapsed)
            console.print(
                f"[yellow]⚠[/yellow] Rate limit: Please wait {wait_time} more seconds "
                "before requesting another new identity"
            )
            raise typer.Exit(1)

    # Load configuration
    config = ConfigLoader.load_with_env_override()
    if port:
        config.connection.control_port = port
    if password:
        config.connection.password = password

    with console.status("[bold green]Requesting new identity...", spinner="dots"):
        with TorController(
            port=config.connection.control_port, password=config.connection.password
        ) as controller:
            # Send NEWNYM signal
            controller.controller.signal("NEWNYM")
            _last_identity_change = datetime.now()

            console.print("\n[green]✓[/green] New identity requested successfully!")
            console.print(
                "\n[yellow]Note:[/yellow] Existing circuits will remain active. "
                "New connections will use fresh circuits."
            )
            console.print("You can close old circuits with: [cyan]dialtor circuit list[/cyan]")


@app.command()
@handle_errors
def rotate(
    max_age: int = typer.Option(
        600, "--max-age", help="Close circuits older than this many seconds"
    ),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Rotate old circuits.

    Closes circuits that are older than the specified age (default: 600 seconds).
    This helps maintain fresh circuits and improve anonymity.
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
        from dialtor.core.circuit_manager import CircuitManager

        manager = CircuitManager(controller)
        circuits = manager.list_circuits()

        # Find old circuits
        old_circuits = [c for c in circuits if c.age_seconds > max_age]

        if not old_circuits:
            console.print(
                f"[green]✓[/green] No circuits older than {max_age} seconds found"
            )
            return

        console.print(f"Found {len(old_circuits)} circuits older than {max_age} seconds")

        # Close old circuits
        closed_count = 0
        with console.status("[bold green]Closing old circuits...", spinner="dots"):
            for circuit in old_circuits:
                try:
                    manager.close_circuit(circuit.id)
                    closed_count += 1
                except Exception as e:
                    console.print(f"[yellow]Warning:[/yellow] Failed to close circuit {circuit.id}: {e}")

        console.print(f"\n[green]✓[/green] Closed {closed_count} old circuits")


@app.command()
@handle_errors
def status(
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Show current identity status.

    Displays information about active circuits and when the last
    identity change was requested.
    """
    global _last_identity_change

    # Load configuration
    config = ConfigLoader.load_with_env_override()
    if port:
        config.connection.control_port = port
    if password:
        config.connection.password = password

    with TorController(
        port=config.connection.control_port, password=config.connection.password
    ) as controller:
        from dialtor.core.circuit_manager import CircuitManager

        manager = CircuitManager(controller)
        circuits = manager.list_circuits()

        built_circuits = [c for c in circuits if c.status.value == "BUILT"]

        console.print("[bold]Identity Status[/bold]\n")
        console.print(f"Active circuits: [cyan]{len(circuits)}[/cyan]")
        console.print(f"Built circuits: [green]{len(built_circuits)}[/green]")

        if circuits:
            avg_age = sum(c.age_seconds for c in circuits) / len(circuits)
            console.print(f"Average circuit age: [yellow]{int(avg_age)}s[/yellow]")

        if _last_identity_change:
            elapsed = (datetime.now() - _last_identity_change).total_seconds()
            console.print(f"\nLast identity change: [yellow]{int(elapsed)}s ago[/yellow]")
        else:
            console.print("\nLast identity change: [dim]Unknown (this session)[/dim]")
