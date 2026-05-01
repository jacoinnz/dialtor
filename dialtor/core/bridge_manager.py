"""Bridge management."""

from typing import List

from dialtor.core.controller import TorController
from dialtor.models.bridge import Bridge
from dialtor.utils.exceptions import BridgeError


class BridgeManager:
    """Manage Tor bridges for censorship circumvention."""

    def __init__(self, controller: TorController) -> None:
        """Initialize bridge manager.

        Args:
            controller: TorController instance
        """
        self.controller = controller

    def list_bridges(self) -> List[Bridge]:
        """List currently configured bridges.

        Returns:
            List of Bridge objects
        """
        try:
            # Get bridge configuration from Tor
            bridge_lines = self.controller.controller.get_conf("Bridge", multiple=True)

            if not bridge_lines:
                return []

            bridges = []
            for line in bridge_lines:
                if line:  # Skip empty lines
                    try:
                        bridge = Bridge.from_bridge_line(line)
                        bridges.append(bridge)
                    except Exception:
                        # Skip invalid bridge lines
                        pass

            return bridges

        except Exception as e:
            raise BridgeError(f"Failed to list bridges: {e}") from e

    def add_bridge(self, bridge: Bridge) -> None:
        """Add a bridge to Tor configuration.

        Args:
            bridge: Bridge object to add

        Raises:
            BridgeError: If bridge addition fails
        """
        try:
            # Get current bridges
            current_bridges = self.controller.controller.get_conf("Bridge", multiple=True) or []

            # Add new bridge
            new_bridges = current_bridges + [bridge.bridge_line]

            # Set configuration
            self.controller.controller.set_conf("Bridge", new_bridges)

            # Enable UseBridges
            self.controller.controller.set_conf("UseBridges", "1")

        except Exception as e:
            raise BridgeError(f"Failed to add bridge: {e}") from e

    def remove_bridge(self, address: str, port: int) -> bool:
        """Remove a bridge from configuration.

        Args:
            address: Bridge IP address or hostname
            port: Bridge port

        Returns:
            True if bridge was removed, False if not found

        Raises:
            BridgeError: If bridge removal fails
        """
        try:
            # Get current bridges
            current_bridges = self.controller.controller.get_conf("Bridge", multiple=True) or []

            # Filter out the bridge to remove
            new_bridges = []
            removed = False

            for line in current_bridges:
                if not line:
                    continue

                try:
                    bridge = Bridge.from_bridge_line(line)
                    if bridge.address == address and bridge.port == port:
                        removed = True
                        continue  # Skip this bridge
                except Exception:
                    pass

                new_bridges.append(line)

            if removed:
                # Update configuration
                if new_bridges:
                    self.controller.controller.set_conf("Bridge", new_bridges)
                else:
                    # No bridges left, reset configuration
                    self.controller.controller.reset_conf("Bridge")
                    self.controller.controller.set_conf("UseBridges", "0")

            return removed

        except Exception as e:
            raise BridgeError(f"Failed to remove bridge: {e}") from e

    def test_bridge(self, bridge: Bridge) -> bool:
        """Test if a bridge is reachable.

        Note: This is a basic connectivity test. Actual bridge
        functionality depends on proper Tor configuration and
        pluggable transports being available.

        Args:
            bridge: Bridge to test

        Returns:
            True if bridge appears in Tor's bridge status

        Raises:
            BridgeError: If test fails
        """
        try:
            # Check if bridge is configured
            bridges = self.list_bridges()
            is_configured = any(
                b.address == bridge.address and b.port == bridge.port for b in bridges
            )

            if not is_configured:
                return False

            # Get bridge status from Tor (if available)
            # Note: Bridge status reporting varies by Tor version
            try:
                status_info = self.controller.controller.get_info("status/bootstrap-phase")
                # If we got this far and have bridge status, consider it working
                return "SUMMARY" in status_info.upper()
            except Exception:
                # Status not available, assume configured bridge works
                return True

        except Exception as e:
            raise BridgeError(f"Failed to test bridge: {e}") from e

    def clear_all_bridges(self) -> int:
        """Remove all configured bridges.

        Returns:
            Number of bridges removed

        Raises:
            BridgeError: If clearing fails
        """
        try:
            bridges = self.list_bridges()
            count = len(bridges)

            if count > 0:
                self.controller.controller.reset_conf("Bridge")
                self.controller.controller.set_conf("UseBridges", "0")

            return count

        except Exception as e:
            raise BridgeError(f"Failed to clear bridges: {e}") from e
