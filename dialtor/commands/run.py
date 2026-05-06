"""Run commands through Tor proxy."""

import os
import subprocess
import sys

import typer
from rich.console import Console

from dialtor.cli import handle_errors

console = Console()


@handle_errors
def run_command(
    ctx: typer.Context,
    socks_port: int = typer.Option(9050, help="Tor SOCKS port"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress dialtor output"),
) -> None:
    """
    Run a command through Tor's SOCKS proxy.

    All arguments after 'dialtor run' are passed to the command.

    Examples:

        \b
        # Run curl through Tor
        dialtor run curl https://api.ipify.org

        \b
        # SSH through Tor
        dialtor run ssh user@example.com

        \b
        # Telnet through Tor
        dialtor run telnet example.com 80

        \b
        # Python script through Tor
        dialtor run python script.py

        \b
        # Git clone through Tor
        dialtor run git clone https://github.com/user/repo

        \b
        # Custom SOCKS port
        dialtor run --socks-port 9150 curl https://api.ipify.org

    Environment variables set:
        ALL_PROXY, HTTP_PROXY, HTTPS_PROXY, FTP_PROXY,
        SOCKS_PROXY, SOCKS5_PROXY, GIT_PROXY_COMMAND, GIT_SSH_COMMAND
    """
    if not ctx.args:
        console.print("[red]Error:[/red] No command specified")
        console.print("\nUsage: [cyan]dialtor run <command> [args...][/cyan]")
        console.print("\nExamples:")
        console.print("  dialtor run curl https://api.ipify.org")
        console.print("  dialtor run ssh user@server")
        console.print("  dialtor run telnet example.com 80")
        console.print("  dialtor run python script.py")
        raise typer.Exit(1)

    command_args = ctx.args

    if not quiet:
        console.print(f"[dim]Running through Tor (SOCKS5 127.0.0.1:{socks_port})...[/dim]")

    # Set up environment with Tor proxy
    env = os.environ.copy()
    socks_proxy = f"socks5://127.0.0.1:{socks_port}"
    http_proxy = f"socks5h://127.0.0.1:{socks_port}"

    env.update({
        # Standard proxy variables
        "ALL_PROXY": socks_proxy,
        "all_proxy": socks_proxy,
        "HTTP_PROXY": http_proxy,
        "http_proxy": http_proxy,
        "HTTPS_PROXY": http_proxy,
        "https_proxy": http_proxy,
        "FTP_PROXY": http_proxy,
        "ftp_proxy": http_proxy,
        # SOCKS-specific variables
        "SOCKS_PROXY": socks_proxy,
        "socks_proxy": socks_proxy,
        "SOCKS5_PROXY": socks_proxy,
        "socks5_proxy": socks_proxy,
        # Git-specific
        "GIT_PROXY_COMMAND": f"nc -X 5 -x 127.0.0.1:{socks_port} %h %p",
        # SSH-specific (for git over SSH)
        "GIT_SSH_COMMAND": f"ssh -o ProxyCommand='nc -X 5 -x 127.0.0.1:{socks_port} %h %p'",
    })

    # Run the command
    try:
        result = subprocess.run(
            command_args,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr,
            stdin=sys.stdin,
        )
        sys.exit(result.returncode)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Command not found: {command_args[0]}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        raise typer.Exit(130)
