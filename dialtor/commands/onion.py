"""Onion service (hidden service) commands."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from dialtor.cli import handle_errors
from dialtor.core.controller import TorController
from dialtor.core.onion_service import OnionServiceManager
from dialtor.utils.config_loader import ConfigLoader

app = typer.Typer(help="Manage Tor onion services (hidden services)")
console = Console()


@app.command()
@handle_errors
def create(
    virtual_port: int = typer.Option(..., "--virtual-port", "-v", help="Port in .onion address"),
    target_port: int = typer.Option(
        ..., "--target-port", "-t", help="Local port where service listens"
    ),
    target_address: str = typer.Option(
        "127.0.0.1", "--target-address", "-a", help="Local address (default: 127.0.0.1)"
    ),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Create a new onion service (v3).

    Creates an ephemeral onion service that routes traffic from the .onion address
    to a local service. The service persists while Tor is running.

    Examples:
        # Expose local web server on port 8080
        dialtor onion create --virtual-port 80 --target-port 8080

        # Expose SSH on custom port
        dialtor onion create --virtual-port 22 --target-port 22

    Note: The service is ephemeral and will be removed when Tor restarts.
    For persistent services, configure them in torrc.
    """
    # Load configuration
    config = ConfigLoader.load_with_env_override()
    if port:
        config.connection.control_port = port
    if password:
        config.connection.password = password

    with console.status("[bold green]Creating onion service...", spinner="dots"):
        with TorController(
            port=config.connection.control_port, password=config.connection.password
        ) as controller:
            manager = OnionServiceManager(controller)

            # Create service
            service = manager.create_service(
                virtual_port=virtual_port,
                target_port=target_port,
                target_address=target_address,
            )

    console.print("[green]✓[/green] Onion service created successfully!")
    console.print(f"\n  [bold]Onion Address:[/bold] [cyan]{service.onion_address}[/cyan]")
    console.print(f"  Virtual Port: {service.virtual_port}")
    console.print(f"  Target: {service.target_address}:{service.target_port}")

    if service.key_content:
        console.print(f"\n  [dim]Private Key: {service.key_content[:32]}...[/dim]")
        console.print("  [yellow]Save this key to recreate the same .onion address later[/yellow]")

    console.print(
        f"\n[green]Your service is now accessible at:[/green] "
        f"[bold]http://{service.onion_address}[/bold]"
    )
    console.print(
        "\n[yellow]Note:[/yellow] This is an ephemeral service. "
        "It will be removed when Tor restarts."
    )


@app.command()
@handle_errors
def list(
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    List active onion services.

    Shows ephemeral onion services created through the control port.
    Services configured in torrc are not shown.
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
        manager = OnionServiceManager(controller)
        services = manager.list_services()

    if not services:
        console.print("[yellow]No active ephemeral onion services[/yellow]")
        console.print(
            "\nCreate one with: [cyan]dialtor onion create --virtual-port 80 --target-port 8080[/cyan]"
        )
        return

    # Create table
    table = Table(title=f"Active Onion Services ({len(services)})", show_header=True)
    table.add_column("Onion Address", style="cyan")
    table.add_column("Virtual Port", style="green")
    table.add_column("Target", style="yellow")

    for service in services:
        target = (
            f"{service.target_address}:{service.target_port}"
            if service.target_port > 0
            else "Unknown"
        )
        virtual_port = str(service.virtual_port) if service.virtual_port > 0 else "Unknown"

        table.add_row(service.onion_address, virtual_port, target)

    console.print(table)
    console.print("\n[dim]Tip: Remove services with:[/dim] [cyan]dialtor onion remove <address>[/cyan]")


@app.command()
@handle_errors
def remove(
    address: str = typer.Argument(..., help="Onion address to remove (with or without .onion)"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Remove an ephemeral onion service.

    Examples:
        dialtor onion remove abc123def456.onion
        dialtor onion remove abc123def456
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
        manager = OnionServiceManager(controller)

        # Remove service
        removed = manager.remove_service(address)

        if removed:
            console.print(f"[green]✓[/green] Onion service removed: {address}")
        else:
            console.print(f"[yellow]Service not found or already removed:[/yellow] {address}")


@app.command()
@handle_errors
def info(
    address: str = typer.Argument(..., help="Onion address to inspect"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Show information about an onion service.

    Displays service descriptor and status information if available.

    Examples:
        dialtor onion info abc123def456.onion
    """
    # Load configuration
    config = ConfigLoader.load_with_env_override()
    if port:
        config.connection.control_port = port
    if password:
        config.connection.password = password

    with console.status("[bold green]Fetching service information...", spinner="dots"):
        with TorController(
            port=config.connection.control_port, password=config.connection.password
        ) as controller:
            manager = OnionServiceManager(controller)

            # Get service descriptor
            descriptor = manager.get_service_descriptor(address)

    # Remove .onion suffix for display
    service_id = address.replace(".onion", "")

    console.print(f"\n[bold]Onion Service:[/bold] [cyan]{service_id}.onion[/cyan]")

    if descriptor:
        console.print(f"\n[bold]Descriptor:[/bold]")
        console.print(f"[dim]{descriptor}[/dim]")
    else:
        console.print("\n[yellow]Service descriptor not available[/yellow]")
        console.print(
            "This may be because:\n"
            "  • Service is not published yet\n"
            "  • Service does not exist\n"
            "  • Service is configured externally"
        )
