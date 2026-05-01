"""Bridge management commands."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from dialtor.cli import handle_errors
from dialtor.core.bridge_manager import BridgeManager
from dialtor.core.controller import TorController
from dialtor.models.bridge import Bridge
from dialtor.utils.config_loader import ConfigLoader

app = typer.Typer(help="Manage Tor bridges for censorship circumvention")
console = Console()


@app.command()
@handle_errors
def add(
    bridge_line: str = typer.Argument(..., help="Bridge configuration line"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Add a bridge to Tor configuration.

    Accepts bridge lines in various formats:
    - Vanilla: 192.0.2.1:9001
    - With fingerprint: 192.0.2.1:9001 AAAA1111BBBB2222...
    - obfs4: Bridge obfs4 192.0.2.1:9001 AAAA1111... cert=...,iat-mode=0
    - Other transports: snowflake, meek, webtunnel

    Examples:
        dialtor bridge add "192.0.2.1:9001"
        dialtor bridge add "obfs4 192.0.2.1:9001 AAAA1111... cert=abcd,iat-mode=0"

    Note: After adding bridges, you may need to restart Tor for changes to take effect.
    """
    # Load configuration
    config = ConfigLoader.load_with_env_override()
    if port:
        config.connection.control_port = port
    if password:
        config.connection.password = password

    # Parse bridge line
    try:
        bridge = Bridge.from_bridge_line(bridge_line)
    except Exception as e:
        console.print(f"[red]Invalid bridge line:[/red] {e}")
        raise typer.Exit(1)

    with TorController(
        port=config.connection.control_port, password=config.connection.password
    ) as controller:
        manager = BridgeManager(controller)

        # Add bridge
        manager.add_bridge(bridge)

        console.print(f"[green]✓[/green] Bridge added successfully")
        console.print(f"  Address: [cyan]{bridge.address}:{bridge.port}[/cyan]")
        console.print(f"  Transport: {bridge.transport}")
        if bridge.fingerprint:
            console.print(f"  Fingerprint: [dim]{bridge.fingerprint}[/dim]")

        console.print(
            "\n[yellow]Note:[/yellow] Tor needs to be restarted for bridge changes to take effect"
        )


@app.command()
@handle_errors
def remove(
    address: str = typer.Argument(..., help="Bridge address (IP or hostname)"),
    bridge_port: int = typer.Argument(..., help="Bridge port"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Remove a bridge from configuration.

    Examples:
        dialtor bridge remove 192.0.2.1 9001
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
        manager = BridgeManager(controller)

        # Remove bridge
        removed = manager.remove_bridge(address, bridge_port)

        if removed:
            console.print(f"[green]✓[/green] Bridge removed: {address}:{bridge_port}")
            console.print(
                "\n[yellow]Note:[/yellow] Tor needs to be restarted for changes to take effect"
            )
        else:
            console.print(f"[yellow]Bridge not found:[/yellow] {address}:{bridge_port}")


@app.command()
@handle_errors
def list(
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    List all configured bridges.

    Shows currently configured bridges with their addresses, ports, and transport types.
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
        manager = BridgeManager(controller)
        bridges = manager.list_bridges()

    if not bridges:
        console.print("[yellow]No bridges configured[/yellow]")
        console.print(
            "\nAdd bridges with: [cyan]dialtor bridge add <bridge-line>[/cyan]"
        )
        return

    # Create table
    table = Table(title=f"Configured Bridges ({len(bridges)})", show_header=True)
    table.add_column("Address", style="cyan")
    table.add_column("Port", style="green")
    table.add_column("Transport", style="blue")
    table.add_column("Fingerprint", style="dim")

    for bridge in bridges:
        table.add_row(
            bridge.address,
            str(bridge.port),
            bridge.transport,
            bridge.fingerprint[:16] + "..." if bridge.fingerprint else "-",
        )

    console.print(table)
    console.print(
        "\n[dim]Tip: Remove bridges with:[/dim] [cyan]dialtor bridge remove <address> <port>[/cyan]"
    )


@app.command()
@handle_errors
def test(
    address: str = typer.Argument(..., help="Bridge address to test"),
    bridge_port: int = typer.Argument(..., help="Bridge port"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Test if a bridge is configured and accessible.

    This checks if the bridge is in Tor's configuration.
    For detailed connectivity testing, check Tor logs.

    Examples:
        dialtor bridge test 192.0.2.1 9001
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
        manager = BridgeManager(controller)

        # Find the bridge
        bridges = manager.list_bridges()
        bridge = None
        for b in bridges:
            if b.address == address and b.port == bridge_port:
                bridge = b
                break

        if not bridge:
            console.print(f"[red]Bridge not configured:[/red] {address}:{bridge_port}")
            console.print("\nAdd it first with: [cyan]dialtor bridge add[/cyan]")
            raise typer.Exit(1)

        # Test bridge
        with console.status("[bold green]Testing bridge...", spinner="dots"):
            is_working = manager.test_bridge(bridge)

        if is_working:
            console.print(f"[green]✓[/green] Bridge is configured: {address}:{bridge_port}")
            console.print(f"  Transport: {bridge.transport}")
        else:
            console.print(f"[yellow]⚠[/yellow] Bridge configured but status unclear: {address}:{bridge_port}")
            console.print("  Check Tor logs for detailed connectivity information")


@app.command()
@handle_errors
def clear(
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation prompt"
    ),
) -> None:
    """
    Remove all configured bridges.

    This will disable bridge mode and clear all bridge configurations.
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
        manager = BridgeManager(controller)
        bridge_count = len(manager.list_bridges())

        if bridge_count == 0:
            console.print("[yellow]No bridges configured[/yellow]")
            return

        # Confirm deletion
        if not force:
            console.print(f"[yellow]Warning:[/yellow] About to remove {bridge_count} bridges")
            confirm = typer.confirm("Are you sure?")
            if not confirm:
                console.print("Cancelled")
                raise typer.Exit(0)

        # Clear bridges
        removed = manager.clear_all_bridges()
        console.print(f"[green]✓[/green] Removed {removed} bridges")
        console.print("\n[yellow]Note:[/yellow] Tor needs to be restarted for changes to take effect")
