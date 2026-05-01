"""Onion service (hidden service) management."""

from pathlib import Path
from typing import Dict, List, Optional

from dialtor.core.controller import TorController
from dialtor.utils.exceptions import OnionServiceError


class OnionService:
    """Onion service information."""

    def __init__(
        self,
        service_id: str,
        virtual_port: int,
        target_port: int,
        target_address: str = "127.0.0.1",
        key_type: str = "NEW",
        key_content: Optional[str] = None,
    ) -> None:
        """Initialize onion service.

        Args:
            service_id: Service ID (.onion address without .onion suffix)
            virtual_port: Port advertised in the .onion address
            target_port: Local port where service listens
            target_address: Local address where service listens
            key_type: Key type (NEW, RSA1024, ED25519-V3)
            key_content: Private key content (for existing keys)
        """
        self.service_id = service_id
        self.virtual_port = virtual_port
        self.target_port = target_port
        self.target_address = target_address
        self.key_type = key_type
        self.key_content = key_content

    @property
    def onion_address(self) -> str:
        """Get full .onion address."""
        return f"{self.service_id}.onion"

    def __str__(self) -> str:
        """String representation."""
        return f"{self.onion_address}:{self.virtual_port} -> {self.target_address}:{self.target_port}"


class OnionServiceManager:
    """Manage Tor hidden services (onion services)."""

    def __init__(self, controller: TorController) -> None:
        """Initialize onion service manager.

        Args:
            controller: TorController instance
        """
        self.controller = controller

    def create_service(
        self,
        virtual_port: int,
        target_port: int,
        target_address: str = "127.0.0.1",
        key_type: str = "ED25519-V3",
        key_content: Optional[str] = None,
    ) -> OnionService:
        """Create a new onion service (ephemeral or persistent).

        Args:
            virtual_port: Port advertised in .onion address
            target_port: Local port where service listens
            target_address: Local address (default: 127.0.0.1)
            key_type: Key type - "NEW", "RSA1024", or "ED25519-V3" (default: ED25519-V3)
            key_content: Private key for existing service (optional)

        Returns:
            OnionService object

        Raises:
            OnionServiceError: If service creation fails
        """
        try:
            # Create port mapping
            ports = {virtual_port: target_port} if target_address == "127.0.0.1" else {
                virtual_port: f"{target_address}:{target_port}"
            }

            # Create ephemeral onion service
            response = self.controller.controller.create_ephemeral_hidden_service(
                ports=ports,
                key_type=key_type,
                key_content=key_content,
                await_publication=True,
            )

            # Extract service ID from response
            service_id = response.service_id

            return OnionService(
                service_id=service_id,
                virtual_port=virtual_port,
                target_port=target_port,
                target_address=target_address,
                key_type=key_type,
                key_content=response.private_key if hasattr(response, "private_key") else None,
            )

        except Exception as e:
            raise OnionServiceError(f"Failed to create onion service: {e}") from e

    def list_services(self) -> List[OnionService]:
        """List active ephemeral onion services.

        Returns:
            List of OnionService objects

        Note: This only lists ephemeral services created through the control port,
        not services configured in torrc.
        """
        try:
            # Get onion services from Tor's GETINFO command
            services = []

            # Try to get ephemeral onion services
            try:
                onion_list = self.controller.controller.get_info("onions/current")
                if onion_list:
                    service_ids = onion_list.split("\n")
                    for service_id in service_ids:
                        if service_id.strip():
                            # Get service details (this is limited info)
                            services.append(
                                OnionService(
                                    service_id=service_id.strip(),
                                    virtual_port=0,  # Unknown
                                    target_port=0,  # Unknown
                                    target_address="unknown",
                                    key_type="UNKNOWN",
                                )
                            )
            except Exception:
                # onions/current not available in all Tor versions
                pass

            return services

        except Exception as e:
            raise OnionServiceError(f"Failed to list onion services: {e}") from e

    def remove_service(self, service_id: str) -> bool:
        """Remove an ephemeral onion service.

        Args:
            service_id: Service ID (.onion address without .onion suffix)

        Returns:
            True if service was removed

        Raises:
            OnionServiceError: If removal fails
        """
        try:
            # Remove .onion suffix if present
            if service_id.endswith(".onion"):
                service_id = service_id[:-6]

            self.controller.controller.remove_ephemeral_hidden_service(service_id)
            return True

        except Exception as e:
            raise OnionServiceError(f"Failed to remove onion service: {e}") from e

    def get_service_descriptor(self, service_id: str) -> Optional[str]:
        """Get service descriptor for an onion service.

        Args:
            service_id: Service ID

        Returns:
            Service descriptor string or None if not available
        """
        try:
            # Remove .onion suffix if present
            if service_id.endswith(".onion"):
                service_id = service_id[:-6]

            descriptor = self.controller.controller.get_hidden_service_descriptor(service_id)
            return str(descriptor) if descriptor else None

        except Exception:
            return None
