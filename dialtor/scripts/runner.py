"""Script execution engine for dialtor.

This module provides utilities for running Python scripts with dialtor context.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from dialtor.api import Dialtor


class ScriptContext:
    """Context object provided to scripts."""

    def __init__(self, tor: Dialtor, args: Optional[Dict[str, Any]] = None) -> None:
        """Initialize script context.

        Args:
            tor: Dialtor API instance
            args: Optional arguments passed to script
        """
        self.tor = tor
        self.args = args or {}

    def log(self, message: str) -> None:
        """Log a message.

        Args:
            message: Message to log
        """
        print(f"[dialtor] {message}")

    def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: Error message
        """
        print(f"[dialtor ERROR] {message}", file=sys.stderr)


def run_script(script_path: Path, args: Optional[Dict[str, Any]] = None) -> int:
    """Execute a Python script with dialtor context.

    The script will have access to:
    - `tor`: Dialtor API instance (already connected)
    - `ctx`: ScriptContext with logging utilities
    - All standard Python libraries

    Args:
        script_path: Path to Python script to execute
        args: Optional arguments to pass to script

    Returns:
        Exit code (0 for success, non-zero for failure)

    Example script:
        ```python
        # my_script.py
        # Available: tor (Dialtor instance), ctx (ScriptContext)

        ctx.log("Starting automation...")

        # Create circuit with US exit
        circuit = tor.create_circuit(exit_country="US")
        ctx.log(f"Created circuit: {circuit.id}")

        # List US relays
        relays = tor.list_relays(country="US", flags=["Fast"], limit=10)
        ctx.log(f"Found {len(relays)} fast US relays")

        ctx.log("Done!")
        ```
    """
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}", file=sys.stderr)
        return 1

    # Read script
    try:
        script_code = script_path.read_text()
    except Exception as e:
        print(f"Error reading script: {e}", file=sys.stderr)
        return 1

    # Create Dialtor instance
    try:
        tor = Dialtor()
        tor.connect()
    except Exception as e:
        print(f"Error connecting to Tor: {e}", file=sys.stderr)
        return 1

    # Create context
    ctx = ScriptContext(tor, args)

    # Prepare globals for script
    script_globals: Dict[str, Any] = {
        "tor": tor,
        "ctx": ctx,
        "__name__": "__main__",
        "__file__": str(script_path),
    }

    # Execute script
    exit_code = 0
    try:
        exec(compile(script_code, str(script_path), "exec"), script_globals)
    except KeyboardInterrupt:
        ctx.log("Interrupted by user")
        exit_code = 130
    except Exception as e:
        ctx.error(f"Script error: {e}")
        import traceback

        traceback.print_exc()
        exit_code = 1
    finally:
        # Disconnect
        try:
            tor.disconnect()
        except Exception:
            pass

    return exit_code


def list_example_scripts() -> Dict[str, str]:
    """List available example scripts.

    Returns:
        Dictionary mapping script names to descriptions
    """
    examples_dir = Path(__file__).parent / "examples"

    if not examples_dir.exists():
        return {}

    examples = {}
    for script_file in examples_dir.glob("*.py"):
        # Read first line (should be docstring)
        try:
            with open(script_file) as f:
                lines = f.readlines()
                # Find first docstring line
                for line in lines:
                    if line.strip().startswith('"""') or line.strip().startswith("'''"):
                        desc = line.strip().strip('"""').strip("'''").strip()
                        examples[script_file.stem] = desc
                        break
                else:
                    examples[script_file.stem] = "No description"
        except Exception:
            examples[script_file.stem] = "No description"

    return examples


def get_example_script_path(name: str) -> Optional[Path]:
    """Get path to example script.

    Args:
        name: Script name (without .py extension)

    Returns:
        Path to script or None if not found
    """
    examples_dir = Path(__file__).parent / "examples"
    script_path = examples_dir / f"{name}.py"

    if script_path.exists():
        return script_path

    return None
