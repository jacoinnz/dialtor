"""Circuit management."""

from datetime import datetime
from typing import List, Optional

from stem.control import Controller

from dialtor.core.controller import TorController
from dialtor.models.circuit import Circuit, CircuitPath, CircuitStatus
from dialtor.utils.exceptions import CircuitCreationError


class CircuitManager:
    """Manage Tor circuits."""

    def __init__(self, controller: TorController) -> None:
        """Initialize circuit manager.

        Args:
            controller: TorController instance
        """
        self.controller = controller

    def list_circuits(self) -> List[Circuit]:
        """List all active circuits.

        Returns:
            List of Circuit objects
        """
        stem_circuits = self.controller.controller.get_circuits()
        circuits = []

        for circuit in stem_circuits:
            # Parse circuit path
            path = []
            for fingerprint, nickname in circuit.path:
                # Try to get country code from relay descriptor
                country = None
                try:
                    desc = self.controller.controller.get_network_status(fingerprint)
                    if hasattr(desc, "country_code"):
                        country = desc.country_code
                except Exception:
                    pass  # Country code not critical

                path.append(
                    CircuitPath(fingerprint=fingerprint, nickname=nickname, country_code=country)
                )

            # Map stem status to our enum
            status_map = {
                "LAUNCHED": CircuitStatus.LAUNCHED,
                "BUILT": CircuitStatus.BUILT,
                "EXTENDED": CircuitStatus.EXTENDED,
                "FAILED": CircuitStatus.FAILED,
                "CLOSED": CircuitStatus.CLOSED,
            }
            status = status_map.get(circuit.status, CircuitStatus.LAUNCHED)

            circuits.append(
                Circuit(
                    id=str(circuit.id),
                    status=status,
                    path=path,
                    purpose=circuit.purpose or "GENERAL",
                    created_at=datetime.fromtimestamp(circuit.created)
                    if hasattr(circuit, "created") and circuit.created
                    else datetime.now(),
                )
            )

        return circuits

    def create_circuit(
        self,
        hops: int = 3,
        exit_country: Optional[str] = None,
        relays: Optional[List[str]] = None,
    ) -> Circuit:
        """Create new circuit with specified parameters.

        Args:
            hops: Number of hops (default: 3)
            exit_country: Exit node country code (optional)
            relays: List of relay fingerprints to use (optional)

        Returns:
            Created Circuit object

        Raises:
            CircuitCreationError: If circuit creation fails
        """
        try:
            if relays:
                # Create circuit with specific relays
                circuit_id = self.controller.controller.new_circuit(path=relays)
            else:
                # Create circuit and let Tor choose relays
                circuit_id = self.controller.controller.new_circuit()

            # Wait for circuit to be built (with timeout)
            self.controller.controller.attach_stream = None  # Don't auto-attach streams

            # Get the created circuit
            circuits = self.list_circuits()
            for circuit in circuits:
                if circuit.id == str(circuit_id):
                    return circuit

            raise CircuitCreationError(f"Circuit {circuit_id} created but not found in list")

        except Exception as e:
            raise CircuitCreationError(f"Failed to create circuit: {e}") from e

    def close_circuit(self, circuit_id: str) -> bool:
        """Close specific circuit.

        Args:
            circuit_id: Circuit ID to close

        Returns:
            True if successful

        Raises:
            CircuitCreationError: If closing fails
        """
        try:
            self.controller.controller.close_circuit(circuit_id)
            return True
        except Exception as e:
            raise CircuitCreationError(f"Failed to close circuit {circuit_id}: {e}") from e

    def get_circuit_info(self, circuit_id: str) -> Optional[Circuit]:
        """Get detailed circuit information.

        Args:
            circuit_id: Circuit ID

        Returns:
            Circuit object or None if not found
        """
        circuits = self.list_circuits()
        for circuit in circuits:
            if circuit.id == circuit_id:
                return circuit
        return None
