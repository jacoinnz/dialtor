"""Bridge data models."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BridgeType(str, Enum):
    """Bridge transport types."""

    VANILLA = "vanilla"
    OBFS4 = "obfs4"
    MEEK = "meek"
    SNOWFLAKE = "snowflake"
    WEBTUNNEL = "webtunnel"


class Bridge(BaseModel):
    """Tor bridge configuration."""

    address: str = Field(..., description="Bridge IP address or hostname")
    port: int = Field(..., description="Bridge port")
    fingerprint: Optional[str] = Field(None, description="Bridge fingerprint")
    transport: BridgeType = Field(BridgeType.VANILLA, description="Transport type")
    transport_options: Optional[str] = Field(None, description="Transport-specific options")

    model_config = ConfigDict(use_enum_values=True)

    @property
    def bridge_line(self) -> str:
        """Get Tor bridge configuration line.

        Returns:
            Bridge line for torrc configuration
        """
        if self.transport == BridgeType.VANILLA:
            # Vanilla bridge: Bridge <address>:<port> [fingerprint]
            line = f"Bridge {self.address}:{self.port}"
            if self.fingerprint:
                line += f" {self.fingerprint}"
        else:
            # Pluggable transport: Bridge <transport> <address>:<port> [fingerprint] [options]
            line = f"Bridge {self.transport} {self.address}:{self.port}"
            if self.fingerprint:
                line += f" {self.fingerprint}"
            if self.transport_options:
                line += f" {self.transport_options}"

        return line

    @classmethod
    def from_bridge_line(cls, line: str) -> "Bridge":
        """Parse bridge configuration line.

        Args:
            line: Bridge line from torrc or BridgeDB

        Returns:
            Bridge object

        Examples:
            Bridge 192.0.2.1:9001
            Bridge 192.0.2.1:9001 AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555
            Bridge obfs4 192.0.2.1:9001 AAAA1111... cert=abcd,iat-mode=0
        """
        parts = line.strip().split()

        # Remove "Bridge" prefix if present
        if parts[0].lower() == "bridge":
            parts = parts[1:]

        # Check if first part is a transport type
        transport = BridgeType.VANILLA
        start_idx = 0
        try:
            transport = BridgeType(parts[0].lower())
            start_idx = 1
        except (ValueError, IndexError):
            pass

        # Parse address:port
        addr_port = parts[start_idx].split(":")
        address = addr_port[0]
        port = int(addr_port[1]) if len(addr_port) > 1 else 443

        # Parse fingerprint (40 hex chars) and options
        fingerprint = None
        transport_options = None

        if len(parts) > start_idx + 1:
            next_part = parts[start_idx + 1]
            # Check if it's a fingerprint (40 hex characters)
            if len(next_part) == 40 and all(c in "0123456789ABCDEFabcdef" for c in next_part):
                fingerprint = next_part.upper()
                # Rest is transport options
                if len(parts) > start_idx + 2:
                    transport_options = " ".join(parts[start_idx + 2 :])
            else:
                # No fingerprint, all rest is transport options
                transport_options = " ".join(parts[start_idx + 1 :])

        return cls(
            address=address,
            port=port,
            fingerprint=fingerprint,
            transport=transport,
            transport_options=transport_options,
        )

    def __str__(self) -> str:
        """String representation."""
        transport_str = f" ({self.transport})" if self.transport != BridgeType.VANILLA else ""
        return f"{self.address}:{self.port}{transport_str}"
