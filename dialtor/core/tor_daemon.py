"""Tor daemon process management."""

import atexit
import logging
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

from dialtor.utils.exceptions import TorNotRunningError

logger = logging.getLogger(__name__)

# Global registry for signal cleanup
_daemon_registry: list["TorDaemon"] = []
_signal_handlers_registered = False


class TorDaemon:
    """Manages a Tor daemon process lifecycle.

    Spawns, monitors, and cleans up a Tor process. Ensures the daemon
    stops when the parent process exits.

    Example:
        daemon = TorDaemon(control_port=9051)
        daemon.start()
        # Use Tor...
        daemon.stop()

    Or with context manager:
        with TorDaemon(control_port=9051) as daemon:
            # Tor is running
            pass
        # Tor automatically stopped
    """

    def __init__(
        self,
        control_port: int = 9051,
        socks_port: int = 9050,
        data_dir: Optional[Path] = None,
        tor_binary: str = "tor",
    ) -> None:
        """Initialize Tor daemon manager.

        Args:
            control_port: Control port for Tor (default: 9051)
            socks_port: SOCKS proxy port (default: 9050)
            data_dir: Tor data directory (default: temporary directory)
            tor_binary: Path to tor executable (default: "tor" from PATH)
        """
        self.control_port = control_port
        self.socks_port = socks_port
        self.tor_binary = tor_binary
        self._process: Optional[subprocess.Popen] = None
        self._data_dir = data_dir
        self._temp_data_dir: Optional[tempfile.TemporaryDirectory] = None
        self._torrc_path: Optional[Path] = None
        self._cleanup_registered = False

    @staticmethod
    def _signal_handler(signum: int, frame: Any) -> None:
        """Handle termination signals to stop all managed daemons."""
        logger.info(f"Received signal {signum}, stopping managed Tor daemons...")

        # Stop all registered daemons
        for daemon in _daemon_registry:
            if daemon.is_running():
                daemon.stop()

        # Re-raise the signal to allow default handling
        sys.exit(128 + signum)

    def _find_tor_binary(self) -> Optional[str]:
        """Find tor binary in system PATH.

        Returns:
            Path to tor binary or None if not found
        """
        return shutil.which(self.tor_binary)

    def _generate_torrc(self) -> Path:
        """Generate temporary torrc configuration.

        Returns:
            Path to generated torrc file
        """
        # Create temporary directory for data if not provided
        if self._data_dir is None:
            self._temp_data_dir = tempfile.TemporaryDirectory(prefix="dialtor_")
            data_dir = Path(self._temp_data_dir.name)
        else:
            data_dir = self._data_dir
            data_dir.mkdir(parents=True, exist_ok=True)

        # Create torrc file
        torrc_content = f"""# dialtor managed Tor configuration
DataDirectory {data_dir}
ControlPort {self.control_port}
SocksPort {self.socks_port}
CookieAuthentication 1
CookieAuthFile {data_dir}/control_auth_cookie

# Disable some features for faster startup
DisableDebuggerAttachment 0
"""

        torrc_path = data_dir / "torrc"
        torrc_path.write_text(torrc_content)
        self._torrc_path = torrc_path

        return torrc_path

    def start(self, wait_for_bootstrap: bool = True, timeout: int = 60) -> None:
        """Start the Tor daemon.

        Args:
            wait_for_bootstrap: Wait for Tor to bootstrap (default: True)
            timeout: Bootstrap timeout in seconds (default: 60)

        Raises:
            TorNotRunningError: If tor binary not found or process fails to start
        """
        # Check if already running
        if self._process is not None and self._process.poll() is None:
            logger.info("Tor daemon already running")
            return

        # Find tor binary
        tor_path = self._find_tor_binary()
        if tor_path is None:
            raise TorNotRunningError(
                f"Tor binary '{self.tor_binary}' not found in PATH. "
                "Install Tor: brew install tor (macOS) or apt-get install tor (Linux)"
            )

        # Generate torrc
        torrc_path = self._generate_torrc()
        logger.info(f"Generated torrc at: {torrc_path}")

        # Start Tor process
        try:
            self._process = subprocess.Popen(
                [tor_path, "-f", str(torrc_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.info(f"Started Tor daemon (PID: {self._process.pid})")

            # Register cleanup handler
            if not self._cleanup_registered:
                atexit.register(self._cleanup)
                self._cleanup_registered = True

            # Register signal handlers (once globally)
            if not _signal_handlers_registered:
                self._register_signal_handlers()

            # Add to daemon registry for signal handling
            if self not in _daemon_registry:
                _daemon_registry.append(self)

            # Wait for Tor to be ready
            if wait_for_bootstrap:
                self._wait_for_bootstrap(timeout)

        except Exception as e:
            self._cleanup()
            raise TorNotRunningError(f"Failed to start Tor daemon: {e}")

    def _wait_for_bootstrap(self, timeout: int) -> None:
        """Wait for Tor to bootstrap.

        Args:
            timeout: Maximum time to wait in seconds

        Raises:
            TorNotRunningError: If bootstrap fails or times out
        """
        import socket

        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if process is still running
            if self._process and self._process.poll() is not None:
                stderr = self._process.stderr.read() if self._process.stderr else ""
                raise TorNotRunningError(f"Tor process exited during bootstrap: {stderr}")

            # Try to connect to control port
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(("127.0.0.1", self.control_port))
                sock.close()

                if result == 0:
                    logger.info("Tor daemon bootstrapped successfully")
                    return

            except Exception:
                pass

            time.sleep(0.5)

        raise TorNotRunningError(
            f"Tor daemon failed to bootstrap within {timeout} seconds"
        )

    def stop(self, timeout: int = 10) -> None:
        """Stop the Tor daemon gracefully.

        Args:
            timeout: Maximum time to wait for graceful shutdown (default: 10)
        """
        if self._process is None:
            return

        if self._process.poll() is not None:
            logger.info("Tor daemon already stopped")
            self._cleanup()
            return

        # Try graceful shutdown first (SIGTERM)
        logger.info(f"Stopping Tor daemon (PID: {self._process.pid})")
        try:
            self._process.terminate()
            self._process.wait(timeout=timeout)
            logger.info("Tor daemon stopped gracefully")
        except subprocess.TimeoutExpired:
            # Force kill if graceful shutdown fails
            logger.warning("Tor daemon did not stop gracefully, forcing kill")
            self._process.kill()
            self._process.wait(timeout=5)
            logger.info("Tor daemon killed")

        self._cleanup()

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        global _signal_handlers_registered

        # Only register once globally
        if _signal_handlers_registered:
            return

        # Handle SIGINT (Ctrl+C) and SIGTERM
        signal.signal(signal.SIGINT, TorDaemon._signal_handler)
        signal.signal(signal.SIGTERM, TorDaemon._signal_handler)

        _signal_handlers_registered = True
        logger.debug("Registered signal handlers for graceful shutdown")

    def _cleanup(self) -> None:
        """Clean up temporary resources."""
        # Remove from daemon registry
        if self in _daemon_registry:
            _daemon_registry.remove(self)

        # Close process handles
        if self._process:
            if self._process.stdout:
                self._process.stdout.close()
            if self._process.stderr:
                self._process.stderr.close()
            self._process = None

        # Clean up temporary data directory
        if self._temp_data_dir:
            try:
                self._temp_data_dir.cleanup()
                logger.debug("Cleaned up temporary data directory")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")
            finally:
                self._temp_data_dir = None

    def is_running(self) -> bool:
        """Check if Tor daemon is running.

        Returns:
            True if running, False otherwise
        """
        return self._process is not None and self._process.poll() is None

    @property
    def pid(self) -> Optional[int]:
        """Get Tor daemon process ID.

        Returns:
            Process ID or None if not running
        """
        return self._process.pid if self._process else None

    def __enter__(self) -> "TorDaemon":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Context manager exit."""
        self.stop()

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        if self.is_running():
            self.stop()
