"""Configuration data models."""

from typing import List, Optional

from pydantic import BaseModel, Field


class TorConnectionConfig(BaseModel):
    """Tor connection configuration."""

    control_port: int = Field(9051, description="Tor control port")
    control_socket: Optional[str] = Field(None, description="Tor control socket path")
    password: Optional[str] = Field(None, description="Control port password")
    timeout: int = Field(30, description="Connection timeout in seconds")


class RelaySelectionConfig(BaseModel):
    """Relay selection preferences."""

    preferred_countries: List[str] = Field(
        default_factory=list, description="Preferred country codes"
    )
    min_bandwidth: int = Field(0, description="Minimum bandwidth in bytes/sec")
    required_flags: List[str] = Field(
        default_factory=lambda: ["Running", "Valid"],
        description="Required relay flags"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field("INFO", description="Log level")
    file: Optional[str] = Field(None, description="Log file path")


class DialtorConfig(BaseModel):
    """Main dialtor configuration."""

    connection: TorConnectionConfig = Field(
        default_factory=TorConnectionConfig,
        description="Tor connection settings"
    )
    relay_selection: RelaySelectionConfig = Field(
        default_factory=RelaySelectionConfig,
        description="Relay selection preferences"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging settings"
    )
