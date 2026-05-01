"""Circuit data models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CircuitStatus(str, Enum):
    """Circuit status values."""

    LAUNCHED = "LAUNCHED"
    BUILT = "BUILT"
    EXTENDED = "EXTENDED"
    FAILED = "FAILED"
    CLOSED = "CLOSED"


class CircuitPath(BaseModel):
    """A single hop in a circuit path."""

    fingerprint: str = Field(..., description="Relay fingerprint")
    nickname: str = Field(..., description="Relay nickname")
    country_code: Optional[str] = Field(None, description="Relay country code")

    def __str__(self) -> str:
        """String representation."""
        country = f" ({self.country_code})" if self.country_code else ""
        return f"{self.nickname}{country}"


class Circuit(BaseModel):
    """Tor circuit information."""

    id: str = Field(..., description="Circuit ID")
    status: CircuitStatus = Field(..., description="Circuit status")
    path: List[CircuitPath] = Field(default_factory=list, description="Circuit path (hops)")
    purpose: str = Field("GENERAL", description="Circuit purpose")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

    model_config = ConfigDict(use_enum_values=True)

    @property
    def age_seconds(self) -> int:
        """Calculate circuit age in seconds."""
        return int((datetime.now() - self.created_at).total_seconds())

    @property
    def path_string(self) -> str:
        """Get path as string."""
        return " -> ".join(str(hop) for hop in self.path)

    def __str__(self) -> str:
        """String representation."""
        return f"Circuit {self.id} ({self.status.value}): {self.path_string}"
