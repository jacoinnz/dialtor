"""IP address checking commands."""

import socket
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from dialtor.cli import handle_errors
from dialtor.core.controller import TorController
from dialtor.utils.config_loader import ConfigLoader

app = typer.Typer(help="Check IP address and Tor connection")
console = Console()


def get_ip_via_service(url: str, socks_proxy: Optional[str] = None) -> Optional[str]:
    """Fetch IP address from a web service.

    Args:
        url: URL of IP check service
        socks_proxy: SOCKS proxy string (e.g., "socks5://127.0.0.1:9050")

    Returns:
        IP address or None if failed
    """
    try:
        import requests

        if socks_proxy:
            proxies = {"http": socks_proxy, "https": socks_proxy}
            response = requests.get(url, proxies=proxies, timeout=10)
        else:
            response = requests.get(url, timeout=10)

        return response.text.strip()
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Failed to fetch IP: {e}")
        return None


def get_tor_check_info(socks_proxy: str) -> dict:
    """Get Tor connection verification from check.torproject.org.

    Args:
        socks_proxy: SOCKS proxy string

    Returns:
        Dict with 'using_tor' (bool) and 'ip' (str)
    """
    try:
        import requests

        proxies = {"http": socks_proxy, "https": socks_proxy}
        response = requests.get(
            "https://check.torproject.org/api/ip", proxies=proxies, timeout=10
        )
        data = response.json()

        return {"using_tor": data.get("IsTor", False), "ip": data.get("IP", "Unknown")}
    except Exception:
        return {"using_tor": False, "ip": "Unknown"}


@app.command()
@handle_errors
def check(
    socks_port: int = typer.Option(9050, help="Tor SOCKS port"),
    port: int = typer.Option(9051, help="Tor control port"),
    password: Optional[str] = typer.Option(None, help="Control port password"),
) -> None:
    """
    Check your IP address and verify Tor connection.

    Shows both your real IP and your Tor exit IP to verify that
    Tor is routing your traffic correctly.

    Example:
        dialtor ip check
        dialtor ip check --socks-port 9050
    """
    # Check if requests is available
    try:
        import requests  # noqa: F401
    except ImportError:
        console.print(
            "[red]Error:[/red] 'requests' library required for IP checking"
        )
        console.print("Install with: [cyan]pip install requests[/cyan]")
        raise typer.Exit(1)

    console.print("\n[bold]Checking IP addresses...[/bold]\n")

    # Get real IP (without Tor)
    console.print("[dim]Fetching real IP address...[/dim]")
    real_ip = get_ip_via_service("https://api.ipify.org")

    # Get Tor exit IP
    console.print("[dim]Fetching Tor exit IP address...[/dim]")
    socks_proxy = f"socks5://127.0.0.1:{socks_port}"
    tor_ip = get_ip_via_service("https://api.ipify.org", socks_proxy=socks_proxy)

    # Verify with Tor Project
    console.print("[dim]Verifying Tor connection...[/dim]\n")
    tor_check = get_tor_check_info(socks_proxy)

    # Create results table
    table = Table(title="IP Address Information", show_header=True)
    table.add_column("Type", style="cyan")
    table.add_column("IP Address", style="white")
    table.add_column("Status", style="white")

    # Real IP
    table.add_row(
        "Real IP", real_ip or "Unable to determine", "[red]Not using Tor[/red]"
    )

    # Tor exit IP
    if tor_ip and tor_ip != real_ip:
        status = (
            "[green]✓ Using Tor[/green]"
            if tor_check["using_tor"]
            else "[yellow]⚠ IP changed but Tor not verified[/yellow]"
        )
        table.add_row("Tor Exit IP", tor_ip, status)
    else:
        table.add_row(
            "Tor Exit IP",
            tor_ip or "Unable to determine",
            "[red]✗ Not using Tor[/red]",
        )

    console.print(table)

    # Additional info if connected to Tor control
    try:
        config = ConfigLoader.load_with_env_override()
        if port != 9051:
            config.connection.control_port = port
        if password:
            config.connection.password = password

        controller = TorController(
            port=config.connection.control_port, password=config.connection.password
        )
        controller.connect()
        controller.authenticate()

        # Get current circuits
        from dialtor.core.circuit_manager import CircuitManager

        circuit_manager = CircuitManager(controller)
        circuits = circuit_manager.list_circuits()

        if circuits:
            console.print(f"\n[bold]Active Circuits:[/bold] {len(circuits)}")
            # Show most recent circuit
            recent = circuits[0]
            console.print(f"Recent path: [cyan]{recent.path_string}[/cyan]")

        controller.disconnect()

    except Exception:
        # Don't fail if can't connect to control port
        pass

    # Summary
    console.print()
    if tor_ip and tor_ip != real_ip and tor_check["using_tor"]:
        console.print("[green]✓ Tor is working correctly![/green]")
        console.print(
            f"Your traffic is being routed through Tor exit node: [cyan]{tor_ip}[/cyan]"
        )
    elif tor_ip and tor_ip != real_ip:
        console.print(
            "[yellow]⚠ Your IP has changed but Tor connection could not be verified[/yellow]"
        )
        console.print("This might be due to a different proxy being used.")
    else:
        console.print("[red]✗ Warning: You are NOT using Tor[/red]")
        console.print(f"Your real IP ([cyan]{real_ip}[/cyan]) is being exposed.")
        console.print(
            "\nMake sure Tor daemon is running and SOCKS proxy is on port 9050"
        )


@app.command()
@handle_errors
def current() -> None:
    """
    Show current Tor exit IP address.

    Quick command to display just the Tor exit IP.

    Example:
        dialtor ip current
    """
    try:
        import requests  # noqa: F401
    except ImportError:
        console.print(
            "[red]Error:[/red] 'requests' library required for IP checking"
        )
        console.print("Install with: [cyan]pip install requests[/cyan]")
        raise typer.Exit(1)

    socks_proxy = "socks5://127.0.0.1:9050"
    tor_ip = get_ip_via_service("https://api.ipify.org", socks_proxy=socks_proxy)

    if tor_ip:
        console.print(f"[cyan]{tor_ip}[/cyan]")
    else:
        console.print("[red]Unable to determine Tor exit IP[/red]")
        raise typer.Exit(1)
