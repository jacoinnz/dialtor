"""Relay management commands."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from dialtor.cli import handle_errors
from dialtor.core.controller import TorController
from dialtor.core.relay_selector import RelaySelector
from dialtor.models.relay import RelayFlags
from dialtor.utils.config_loader import ConfigLoader

app = typer.Typer(help="Manage and inspect Tor relays")
console = Console()


def format_bandwidth(bytes_per_sec: int) -> str:
    """Format bandwidth in human-readable format.

    Args:
        bytes_per_sec: Bandwidth in bytes per second

    Returns:
        Formatted string (e.g., "10.5 MB/s")
    """
    if bytes_per_sec >= 1_073_741_824:  # >= 1 GB
        return f"{bytes_per_sec / 1_073_741_824:.1f} GB/s"
    elif bytes_per_sec >= 1_048_576:  # >= 1 MB
        return f"{bytes_per_sec / 1_048_576:.1f} MB/s"
    elif bytes_per_sec >= 1024:  # >= 1 KB
        return f"{bytes_per_sec / 1024:.1f} KB/s"
    else:
        return f"{bytes_per_sec} B/s"


@app.command()
@handle_errors
def list(
    country: Optional[str] = typer.Option(
        None, "--country", "-c", help="Filter by country code (e.g., US, DE)"
    ),
    flags: Optional[str] = typer.Option(
        None, "--flags", "-f", help="Filter by flags (comma-separated, e.g., Fast,Stable,Guard)"
    ),
    min_bandwidth: Optional[int] = typer.Option(
        None, "--min-bandwidth", "-b", help="Minimum bandwidth in bytes/sec"
    ),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of relays to display"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    List available Tor relays with optional filtering.

    Displays a table of relays with their properties including nickname,
    country, flags, and bandwidth. Use filters to narrow down results.

    Examples:
        dialtor relay list --country US --flags Fast,Stable
        dialtor relay list --min-bandwidth 5242880  # >= 5 MB/s
    """
    # Load configuration
    config = ConfigLoader.load_with_env_override()
    if port:
        config.connection.control_port = port
    if password:
        config.connection.password = password

    with console.status("[bold green]Fetching relay consensus...", spinner="dots"):
        with TorController(
            port=config.connection.control_port, password=config.connection.password
        ) as controller:
            selector = RelaySelector(controller)
            relays = selector.get_all_relays()

            # Apply filters
            if country:
                relays = selector.filter_by_country(country, relays)

            if flags:
                flag_set = set()
                for flag in flags.split(","):
                    flag = flag.strip()
                    try:
                        flag_set.add(RelayFlags(flag))
                    except ValueError:
                        console.print(f"[yellow]Warning: Unknown flag '{flag}', ignoring[/yellow]")
                if flag_set:
                    relays = selector.filter_by_flags(flag_set, relays)

            if min_bandwidth:
                relays = selector.filter_by_bandwidth(min_bandwidth, relays)

            # Sort by bandwidth (descending)
            relays = sorted(relays, key=lambda r: r.bandwidth, reverse=True)

            # Limit results
            relays = relays[:limit]

    if not relays:
        console.print("[yellow]No relays found matching the criteria[/yellow]")
        return

    # Create table
    table = Table(
        title=f"Tor Relays ({len(relays)} shown"
        + (f" of many" if len(relays) == limit else "")
        + ")",
        show_header=True,
    )
    table.add_column("Nickname", style="cyan")
    table.add_column("Fingerprint", style="dim")
    table.add_column("Country", style="green")
    table.add_column("Bandwidth", style="yellow", justify="right")
    table.add_column("Flags", style="blue")

    for relay in relays:
        # Format flags
        flags_str = ",".join(sorted(relay.flags))

        # Color code based on key flags
        if RelayFlags.EXIT in relay.flags:
            nickname_style = "bold green"
        elif RelayFlags.GUARD in relay.flags:
            nickname_style = "bold blue"
        elif RelayFlags.FAST in relay.flags:
            nickname_style = "bold cyan"
        else:
            nickname_style = "white"

        table.add_row(
            f"[{nickname_style}]{relay.nickname}[/{nickname_style}]",
            relay.fingerprint[:16] + "...",
            relay.country_code or "??",
            format_bandwidth(relay.bandwidth),
            flags_str,
        )

    console.print(table)
    console.print(
        f"\n[dim]Tip: Use --limit to see more, --country to filter by location, "
        "--flags to filter by capabilities[/dim]"
    )


@app.command()
@handle_errors
def info(
    fingerprint: str = typer.Argument(..., help="Relay fingerprint (full or partial)"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Tor control port"),
    password: Optional[str] = typer.Option(None, "--password", help="Control port password"),
) -> None:
    """
    Show detailed information about a specific relay.

    Displays comprehensive information about a relay including
    address, ports, flags, bandwidth, and version.

    Examples:
        dialtor relay info AAAA1111BBBB2222
        dialtor relay info AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555
    """
    # Load configuration
    config = ConfigLoader.load_with_env_override()
    if port:
        config.connection.control_port = port
    if password:
        config.connection.password = password

    with console.status("[bold green]Fetching relay information...", spinner="dots"):
        with TorController(
            port=config.connection.control_port, password=config.connection.password
        ) as controller:
            selector = RelaySelector(controller)
            selector.get_all_relays()  # Load cache

            relay = selector.get_relay_info(fingerprint)

    if not relay:
        console.print(f"[red]Relay not found: {fingerprint}[/red]")
        raise typer.Exit(1)

    # Display relay information
    console.print(f"\n[bold]{relay.nickname}[/bold]")
    console.print(f"  Fingerprint: [cyan]{relay.fingerprint}[/cyan]")
    console.print(f"  Address: {relay.address}:{relay.or_port}")
    if relay.dir_port:
        console.print(f"  Directory Port: {relay.dir_port}")

    if relay.country_code:
        console.print(f"  Country: [green]{relay.country_code}[/green]")

    console.print(f"  Bandwidth: [yellow]{format_bandwidth(relay.bandwidth)}[/yellow]")

    if relay.flags:
        flags_str = ", ".join(sorted(relay.flags))
        console.print(f"  Flags: [blue]{flags_str}[/blue]")

    if relay.version:
        console.print(f"  Tor Version: {relay.version}")

    if relay.contact:
        console.print(f"  Contact: {relay.contact}")

    if relay.exit_policy:
        console.print(f"  Exit Policy: {relay.exit_policy}")

    # Categorize relay
    console.print("\n[bold]Capabilities:[/bold]")
    capabilities = []
    if RelayFlags.GUARD in relay.flags:
        capabilities.append("✓ Can be used as guard (entry) node")
    if RelayFlags.EXIT in relay.flags:
        capabilities.append("✓ Can be used as exit node")
    if RelayFlags.FAST in relay.flags:
        capabilities.append("✓ Fast relay")
    if RelayFlags.STABLE in relay.flags:
        capabilities.append("✓ Stable relay")
    if RelayFlags.HSDIR in relay.flags:
        capabilities.append("✓ Hidden service directory")

    if capabilities:
        for cap in capabilities:
            console.print(f"  {cap}")
    else:
        console.print("  [dim]No special capabilities[/dim]")
