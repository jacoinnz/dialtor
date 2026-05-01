"""Tor controller wrapper around stem."""

from typing import Any, Optional

from stem import SocketError
from stem.connection import AuthenticationFailure
from stem.control import Controller

from dialtor.utils.exceptions import (
    TorAuthenticationError,
    TorConnectionError,
    TorNotRunningError,
)


class TorController:
    """Wrapper around stem.control.Controller with dialtor-specific functionality."""

    def __init__(self, port: int = 9051, password: Optional[str] = None) -> None:
        """Initialize Tor controller.

        Args:
            port: Tor control port (default: 9051)
            password: Control port password (optional)
        """
        self.port = port
        self.password = password
        self._controller: Optional[Controller] = None
        self._is_connected = False

    def connect(self) -> bool:
        """Establish connection to Tor control port.

        Returns:
            True if connection successful

        Raises:
            TorNotRunningError: If Tor daemon is not running
            TorConnectionError: If connection fails for other reasons
        """
        try:
            controller_context = Controller.from_port(port=self.port)
            self._controller = controller_context.__enter__()
            self._is_connected = True
            return True
        except SocketError as e:
            raise TorNotRunningError(
                f"Tor daemon is not running or not accessible on port {self.port}. "
                f"Error: {e}"
            ) from e
        except Exception as e:
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
        """Close controller connection."""
        if self._controller is not None:
            self._controller.close()
            self._controller = None
        self._is_connected = False

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
