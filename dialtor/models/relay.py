"""Relay data models."""

from enum import Enum
from typing import Optional, Set

from pydantic import BaseModel, ConfigDict, Field


class RelayFlags(str, Enum):
    """Tor relay flags."""

    FAST = "Fast"
    STABLE = "Stable"
    RUNNING = "Running"
    VALID = "Valid"
    GUARD = "Guard"
    EXIT = "Exit"
    AUTHORITY = "Authority"
    HSDIR = "HSDir"
    V2DIR = "V2Dir"
    BADEXT = "BadExit"


class Relay(BaseModel):
    """Tor relay information."""

    fingerprint: str = Field(..., description="Relay fingerprint (hex)")
    nickname: str = Field(..., description="Relay nickname")
    address: str = Field(..., description="IP address")
    or_port: int = Field(..., description="OR (Onion Router) port")
    dir_port: int = Field(0, description="Directory port")
    flags: Set[RelayFlags] = Field(default_factory=set, description="Relay flags")
    bandwidth: int = Field(0, description="Bandwidth in bytes/sec")
    country_code: Optional[str] = Field(None, description="Two-letter country code")
    exit_policy: Optional[str] = Field(None, description="Exit policy summary")
    contact: Optional[str] = Field(None, description="Contact information")
    version: Optional[str] = Field(None, description="Tor version")

    model_config = ConfigDict(use_enum_values=True)

    def __str__(self) -> str:
        """String representation."""
        flags_str = ",".join(sorted(self.flags))
        country = f" ({self.country_code})" if self.country_code else ""
        return f"{self.nickname} [{self.fingerprint[:8]}...]{country} - {flags_str}"
