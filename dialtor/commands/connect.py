"""Connection commands."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from dialtor.cli import handle_errors
from dialtor.core.controller import TorController
from dialtor.utils.config_loader import ConfigLoader

app = typer.Typer(help="Connect to Tor network")
console = Console()


@app.command()
@handle_errors
def verify(
    port: Optional[int] = typer.Option(
        None, "--port", "-p", help="Tor control port (overrides config)"
    ),
    password: Optional[str] = typer.Option(
        None, "--password", help="Control port password (overrides config)"
    ),
) -> None:
    """
    Connect to Tor network and verify connection status.

    Connects to the Tor control port, authenticates, and displays
    information about the Tor daemon and network status.
    """
    # Load configuration
    config = ConfigLoader.load_with_env_override()

    # Override with command-line options
    if port:
        config.connection.control_port = port
    if password:
        config.connection.password = password

    console.print("[bold]Connecting to Tor...[/bold]")

    # Connect to Tor
    with TorController(
        port=config.connection.control_port, password=config.connection.password
    ) as controller:
        # Get Tor information
        version = controller.get_version()
        info_names = controller.controller.get_info("info/names").split("\n")

        # Get circuit status
        circuits = controller.controller.get_circuits()
        built_circuits = [c for c in circuits if c.status == "BUILT"]

        # Display connection info
        table = Table(title="Tor Connection Status", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Status", "✓ Connected")
        table.add_row("Tor Version", version)
        table.add_row("Control Port", str(config.connection.control_port))
        table.add_row(
            "Authentication", "✓ Authenticated" if config.connection.password else "✓ No password"
        )
        table.add_row("Active Circuits", str(len(built_circuits)))
        table.add_row("Available Info Keys", str(len(info_names)))

        console.print(table)

        # Check if we can connect to the network
        if built_circuits:
            console.print(
                "\n[green]✓[/green] Successfully connected to Tor network with active circuits"
            )
        else:
            console.print(
                "\n[yellow]⚠[/yellow] Connected to Tor daemon but no circuits built yet. "
                "This is normal if Tor just started."
            )
