"""High-level Python API for dialtor.

This module provides a clean, Pythonic API for controlling Tor programmatically.
Use this when you want to import dialtor as a library in your Python scripts.

Example:
    >>> from dialtor.api import Dialtor
    >>>
    >>> # Connect to Tor
    >>> tor = Dialtor()
    >>> tor.connect()
    >>>
    >>> # Create circuit with US exit
    >>> circuit = tor.create_circuit(exit_country="US")
    >>> print(f"Created circuit: {circuit.id}")
    >>>
    >>> # List relays
    >>> us_relays = tor.list_relays(country="US", flags=["Fast", "Stable"])
    >>> print(f"Found {len(us_relays)} US relays")
    >>>
    >>> # Request new identity
    >>> tor.new_identity()
    >>>
    >>> tor.disconnect()
"""

from pathlib import Path
from typing import List, Optional, Set

from dialtor.core.bridge_manager import BridgeManager
from dialtor.core.circuit_manager import CircuitManager
from dialtor.core.controller import TorController
from dialtor.core.onion_service import OnionService, OnionServiceManager
from dialtor.core.relay_selector import RelaySelector
from dialtor.models.bridge import Bridge
from dialtor.models.circuit import Circuit
from dialtor.models.relay import Relay, RelayFlags
from dialtor.utils.config_loader import ConfigLoader


class Dialtor:
    """High-level API for Tor control.

    This class provides a simple, Pythonic interface to all dialtor functionality.
    It manages the Tor controller connection and provides convenient methods for
    common operations.

    Attributes:
        controller: TorController instance
        circuits: CircuitManager instance
        relays: RelaySelector instance
        bridges: BridgeManager instance
        onions: OnionServiceManager instance
    """

    def __init__(
        self,
        port: int = 9051,
        password: Optional[str] = None,
        config_file: Optional[Path] = None,
        managed: bool = False,
    ) -> None:
        """Initialize Dialtor API.

        Args:
            port: Tor control port (default: 9051)
            password: Control port password (optional)
            config_file: Path to config file (optional)
            managed: If True, start and manage Tor daemon process (default: False)
        """
        # Load configuration
        if config_file:
            config = ConfigLoader.load(config_file)
        else:
            config = ConfigLoader.load_with_env_override()

        # Override with parameters
        if port != 9051:
            config.connection.control_port = port
        if password:
            config.connection.password = password

        # Initialize controller
        self.controller = TorController(
            port=config.connection.control_port,
            password=config.connection.password,
            managed=managed,
        )

        # Initialize managers (will be available after connect)
        self.circuits: Optional[CircuitManager] = None
        self.relays: Optional[RelaySelector] = None
        self.bridges: Optional[BridgeManager] = None
        self.onions: Optional[OnionServiceManager] = None

        self._connected = False

    def connect(self) -> bool:
        """Connect to Tor control port.

        Returns:
            True if connection successful

        Raises:
            TorNotRunningError: If Tor daemon is not running
            TorConnectionError: If connection fails
        """
        self.controller.connect()
        self.controller.authenticate()
        self._connected = True

        # Initialize managers
        self.circuits = CircuitManager(self.controller)
        self.relays = RelaySelector(self.controller)
        self.bridges = BridgeManager(self.controller)
        self.onions = OnionServiceManager(self.controller)

        return True

    def disconnect(self) -> None:
        """Disconnect from Tor."""
        if self._connected:
            self.controller.disconnect()
            self._connected = False

    def is_connected(self) -> bool:
        """Check if connected to Tor.

        Returns:
            True if connected
        """
        return self._connected and self.controller.is_connected()

    # Circuit methods

    def list_circuits(self) -> List[Circuit]:
        """List all active circuits.

        Returns:
            List of Circuit objects
        """
        self._ensure_connected()
        return self.circuits.list_circuits()

    def create_circuit(
        self,
        hops: int = 3,
        exit_country: Optional[str] = None,
        relays: Optional[List[str]] = None,
    ) -> Circuit:
        """Create a new circuit.

        Args:
            hops: Number of hops (default: 3)
            exit_country: Exit node country code (e.g., "US", "DE")
            relays: List of relay fingerprints for custom path

        Returns:
            Created Circuit object
        """
        self._ensure_connected()
        return self.circuits.create_circuit(hops=hops, exit_country=exit_country, relays=relays)

    def close_circuit(self, circuit_id: str) -> bool:
        """Close a specific circuit.

        Args:
            circuit_id: Circuit ID to close

        Returns:
            True if successful
        """
        self._ensure_connected()
        return self.circuits.close_circuit(circuit_id)

    def get_circuit(self, circuit_id: str) -> Optional[Circuit]:
        """Get circuit information.

        Args:
            circuit_id: Circuit ID

        Returns:
            Circuit object or None if not found
        """
        self._ensure_connected()
        return self.circuits.get_circuit_info(circuit_id)

    # Relay methods

    def list_relays(
        self,
        country: Optional[str] = None,
        flags: Optional[List[str]] = None,
        min_bandwidth: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Relay]:
        """List and filter relays.

        Args:
            country: Filter by country code (e.g., "US")
            flags: Filter by flags (e.g., ["Fast", "Stable"])
            min_bandwidth: Minimum bandwidth in bytes/sec
            limit: Maximum number of relays to return

        Returns:
            List of Relay objects
        """
        self._ensure_connected()
        self.relays.get_all_relays()  # Load cache

        relays = self.relays._relay_cache or []

        # Apply filters
        if country:
            relays = self.relays.filter_by_country(country, relays)

        if flags:
            flag_set = {RelayFlags(f) for f in flags}
            relays = self.relays.filter_by_flags(flag_set, relays)

        if min_bandwidth:
            relays = self.relays.filter_by_bandwidth(min_bandwidth, relays)

        # Sort by bandwidth
        relays = sorted(relays, key=lambda r: r.bandwidth, reverse=True)

        # Limit results
        if limit:
            relays = relays[:limit]

        return relays

    def get_relay(self, fingerprint: str) -> Optional[Relay]:
        """Get relay information.

        Args:
            fingerprint: Relay fingerprint (full or partial)

        Returns:
            Relay object or None if not found
        """
        self._ensure_connected()
        self.relays.get_all_relays()
        return self.relays.get_relay_info(fingerprint)

    def select_random_relays(
        self,
        count: int = 1,
        country: Optional[str] = None,
        flags: Optional[List[str]] = None,
        min_bandwidth: Optional[int] = None,
    ) -> List[Relay]:
        """Select random relays matching criteria.

        Args:
            count: Number of relays to select
            country: Country code filter
            flags: Flags filter
            min_bandwidth: Minimum bandwidth filter

        Returns:
            List of randomly selected relays
        """
        self._ensure_connected()
        self.relays.get_all_relays()

        flag_set = {RelayFlags(f) for f in flags} if flags else None

        return self.relays.select_random(
            count=count,
            country=country,
            flags=flag_set,
            min_bandwidth=min_bandwidth,
        )

    # Identity methods

    def new_identity(self) -> None:
        """Request a new Tor identity (NEWNYM signal)."""
        self._ensure_connected()
        self.controller.controller.signal("NEWNYM")

    def rotate_circuits(self, max_age: int = 600) -> int:
        """Close circuits older than specified age.

        Args:
            max_age: Maximum circuit age in seconds (default: 600)

        Returns:
            Number of circuits closed
        """
        self._ensure_connected()
        circuits = self.circuits.list_circuits()
        old_circuits = [c for c in circuits if c.age_seconds > max_age]

        closed = 0
        for circuit in old_circuits:
            try:
                self.circuits.close_circuit(circuit.id)
                closed += 1
            except Exception:
                pass

        return closed

    # Bridge methods

    def add_bridge(self, bridge_line: str) -> Bridge:
        """Add a bridge.

        Args:
            bridge_line: Bridge configuration line

        Returns:
            Bridge object
        """
        self._ensure_connected()
        bridge = Bridge.from_bridge_line(bridge_line)
        self.bridges.add_bridge(bridge)
        return bridge

    def remove_bridge(self, address: str, port: int) -> bool:
        """Remove a bridge.

        Args:
            address: Bridge address
            port: Bridge port

        Returns:
            True if removed
        """
        self._ensure_connected()
        return self.bridges.remove_bridge(address, port)

    def list_bridges(self) -> List[Bridge]:
        """List configured bridges.

        Returns:
            List of Bridge objects
        """
        self._ensure_connected()
        return self.bridges.list_bridges()

    # Onion service methods

    def create_onion_service(
        self,
        virtual_port: int,
        target_port: int,
        target_address: str = "127.0.0.1",
    ) -> OnionService:
        """Create an ephemeral onion service.

        Args:
            virtual_port: Port advertised in .onion address
            target_port: Local port where service listens
            target_address: Local address (default: 127.0.0.1)

        Returns:
            OnionService object
        """
        self._ensure_connected()
        return self.onions.create_service(
            virtual_port=virtual_port,
            target_port=target_port,
            target_address=target_address,
        )

    def remove_onion_service(self, service_id: str) -> bool:
        """Remove an onion service.

        Args:
            service_id: Service ID or .onion address

        Returns:
            True if removed
        """
        self._ensure_connected()
        return self.onions.remove_service(service_id)

    def list_onion_services(self) -> List[OnionService]:
        """List active onion services.

        Returns:
            List of OnionService objects
        """
        self._ensure_connected()
        return self.onions.list_services()

    # Utility methods

    def get_tor_version(self) -> str:
        """Get Tor version.

        Returns:
            Tor version string
        """
        self._ensure_connected()
        return self.controller.get_version()

    def _ensure_connected(self) -> None:
        """Ensure connected to Tor.

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected:
            raise RuntimeError("Not connected to Tor. Call connect() first.")

    def __enter__(self) -> "Dialtor":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Context manager exit."""
        self.disconnect()

    def __repr__(self) -> str:
        """String representation."""
        status = "connected" if self._connected else "disconnected"
        return f"<Dialtor {status}>"
