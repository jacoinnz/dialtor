"""Main CLI application entry point."""

from functools import wraps
from typing import Any, Callable

import typer
from rich.console import Console
from rich.traceback import install

from dialtor.utils.exceptions import (
    ConfigurationError,
    DialtorError,
    TorAuthenticationError,
    TorConnectionError,
    TorNotRunningError,
)

# Install rich traceback handler for better error display
install(show_locals=False)

# Create main Typer app
app = typer.Typer(
    name="dialtor",
    help="Advanced Tor network control CLI",
    add_completion=False,
    pretty_exceptions_enable=False,
)

# Create Rich console for output
console = Console()


def handle_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for consistent error handling in CLI commands.

    Args:
        func: Command function to wrap

    Returns:
        Wrapped function with error handling
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except TorNotRunningError as e:
            console.print(f"[red]Error:[/red] {e}")
            console.print(
                "\n[yellow]Hint:[/yellow] Start Tor daemon first. "
                "On macOS: [cyan]brew services start tor[/cyan]"
            )
            raise typer.Exit(1)
        except TorAuthenticationError as e:
            console.print(f"[red]Authentication Error:[/red] {e}")
            console.print(
                "\n[yellow]Hint:[/yellow] Check your Tor control port password. "
                "You can set it in ~/.dialtor/config.toml or via DIALTOR_PASSWORD env var."
            )
            raise typer.Exit(1)
        except TorConnectionError as e:
            console.print(f"[red]Connection Error:[/red] {e}")
            raise typer.Exit(1)
        except ConfigurationError as e:
            console.print(f"[red]Configuration Error:[/red] {e}")
            console.print(
                "\n[yellow]Hint:[/yellow] Check your config file at ~/.dialtor/config.toml"
            )
            raise typer.Exit(1)
        except DialtorError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            raise typer.Exit(130)
        except Exception as e:
            console.print(f"[red]Unexpected error:[/red] {e}")
            console.print(
                "\n[yellow]This is a bug. Please report it at:[/yellow] "
                "[cyan]https://github.com/jacoinnz/dialtor/issues[/cyan]"
            )
            raise typer.Exit(2)

    return wrapper


@app.callback()
def main() -> None:
    """
    dialtor - Advanced Tor network control CLI.

    Control Tor circuits, manage relays, rotate identity, and more.
    """
    pass


# Import and register command modules
from dialtor.commands import circuit, connect, identity, relay

app.add_typer(connect.app, name="connect")
app.add_typer(circuit.app, name="circuit")
app.add_typer(identity.app, name="identity")
app.add_typer(relay.app, name="relay")

# Additional command modules will be registered as implemented:
# from dialtor.commands import bridge, onion, config as cfg_cmd
# app.add_typer(relay.app, name="relay")
# app.add_typer(identity.app, name="identity")
# app.add_typer(bridge.app, name="bridge")
# app.add_typer(onion.app, name="onion")
# app.add_typer(cfg_cmd.app, name="config")


if __name__ == "__main__":
    app()
