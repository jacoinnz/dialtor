"""Tor controller wrapper around stem."""

from typing import Any, Optional

from stem import SocketError
from stem.connection import AuthenticationFailure
from stem.control import Controller

from dialtor.core.tor_daemon import TorDaemon
from dialtor.utils.exceptions import (
    TorAuthenticationError,
    TorConnectionError,
    TorNotRunningError,
)


class TorController:
    """Wrapper around stem.control.Controller with dialtor-specific functionality."""

    def __init__(
        self, port: int = 9051, password: Optional[str] = None, managed: bool = False
    ) -> None:
        """Initialize Tor controller.

        Args:
            port: Tor control port (default: 9051)
            password: Control port password (optional)
            managed: If True, start and manage Tor daemon process (default: False)
        """
        self.port = port
        self.password = password
        self.managed = managed
        self._controller: Optional[Controller] = None
        self._is_connected = False
        self._daemon: Optional[TorDaemon] = None

        # Create daemon instance if managed mode
        if self.managed:
            self._daemon = TorDaemon(control_port=port)

    def connect(self) -> bool:
        """Establish connection to Tor control port.

        If managed mode is enabled, starts the Tor daemon first.

        Returns:
            True if connection successful

        Raises:
            TorNotRunningError: If Tor daemon is not running
            TorConnectionError: If connection fails for other reasons
        """
        # Start managed daemon if configured
        if self.managed and self._daemon is not None:
            if not self._daemon.is_running():
                self._daemon.start()

        try:
            controller_context = Controller.from_port(port=self.port)
            self._controller = controller_context.__enter__()
            self._is_connected = True
            return True
        except SocketError as e:
            # Clean up daemon if we started it
            if self.managed and self._daemon is not None:
                self._daemon.stop()

            raise TorNotRunningError(
                f"Tor daemon is not running or not accessible on port {self.port}. "
                f"Error: {e}"
            ) from e
        except Exception as e:
            # Clean up daemon if we started it
            if self.managed and self._daemon is not None:
                self._daemon.stop()

            raise TorConnectionError(f"Failed to connect to Tor: {e}") from e

    def authenticate(self) -> bool:
        """Authenticate with Tor control port.

        Returns:
            True if authentication successful

        Raises:
            TorAuthenticationError: If authentication fails
            TorConnectionError: If not connected
        """
        if not self._is_connected or self._controller is None:
            raise TorConnectionError("Not connected to Tor. Call connect() first.")

        try:
            self._controller.authenticate(password=self.password)
            return True
        except AuthenticationFailure as e:
            raise TorAuthenticationError(
                f"Authentication failed. Check your control port password. Error: {e}"
            ) from e

    def is_connected(self) -> bool:
        """Check if connected and authenticated.

        Returns:
            True if connected
        """
        return self._is_connected and self._controller is not None

    def get_info(self, key: str) -> Any:
        """Get information from Tor.

        Args:
            key: Information key to retrieve

        Returns:
            Information value

        Raises:
            TorConnectionError: If not connected
        """
        if not self._is_connected or self._controller is None:
            raise TorConnectionError("Not connected to Tor")

        return self._controller.get_info(key)

    def get_version(self) -> str:
        """Get Tor version.

        Returns:
            Tor version string

        Raises:
            TorConnectionError: If not connected
        """
        if not self._is_connected or self._controller is None:
            raise TorConnectionError("Not connected to Tor")

        version = self._controller.get_version()
        return version.version_str

    def disconnect(self) -> None:
        """Close controller connection and stop managed daemon if applicable."""
        if self._controller is not None:
            self._controller.close()
            self._controller = None
        self._is_connected = False

        # Stop managed daemon
        if self.managed and self._daemon is not None:
            self._daemon.stop()

    def __enter__(self) -> "TorController":
        """Context manager entry."""
        self.connect()
        self.authenticate()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.disconnect()

    @property
    def controller(self) -> Controller:
        """Get underlying stem controller.

        Returns:
            stem Controller instance

        Raises:
            TorConnectionError: If not connected
        """
        if not self._is_connected or self._controller is None:
            raise TorConnectionError("Not connected to Tor")
        return self._controller
