"""Configuration loading and management."""

import os
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

from dialtor.models.config import DialtorConfig
from dialtor.utils.exceptions import ConfigurationError


class ConfigLoader:
    """Load and manage dialtor configuration."""

    DEFAULT_CONFIG_PATHS = [
        Path.home() / ".dialtor" / "config.toml",
        Path.home() / ".config" / "dialtor" / "config.toml",
        Path("/etc/dialtor/config.toml"),
    ]

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> DialtorConfig:
        """Load configuration from file or return defaults.

        Args:
            config_path: Optional custom config file path

        Returns:
            DialtorConfig instance

        Raises:
            ConfigurationError: If config file is invalid
        """
        if config_path:
            paths_to_try = [config_path]
        else:
            paths_to_try = cls.DEFAULT_CONFIG_PATHS

        config_data = {}

        for path in paths_to_try:
            if path.exists():
                try:
                    with open(path, "rb") as f:
                        config_data = tomllib.load(f)
                    break
                except Exception as e:
                    raise ConfigurationError(
                        f"Failed to load configuration from {path}: {e}"
                    ) from e

        # Return config with defaults for missing values
        try:
            return DialtorConfig(**config_data)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}") from e

    @classmethod
    def load_with_env_override(cls, config_path: Optional[Path] = None) -> DialtorConfig:
        """Load configuration and override with environment variables.

        Environment variables:
        - DIALTOR_CONTROL_PORT: Override control_port
        - DIALTOR_PASSWORD: Override password
        - DIALTOR_TIMEOUT: Override timeout
        - DIALTOR_LOG_LEVEL: Override logging level

        Args:
            config_path: Optional custom config file path

        Returns:
            DialtorConfig instance with env overrides
        """
        config = cls.load(config_path)

        # Override with environment variables
        if port := os.getenv("DIALTOR_CONTROL_PORT"):
            config.connection.control_port = int(port)

        if password := os.getenv("DIALTOR_PASSWORD"):
            config.connection.password = password

        if timeout := os.getenv("DIALTOR_TIMEOUT"):
            config.connection.timeout = int(timeout)

        if log_level := os.getenv("DIALTOR_LOG_LEVEL"):
            config.logging.level = log_level

        return config

    @staticmethod
    def create_default_config(path: Path) -> None:
        """Create default configuration file.

        Args:
            path: Path where config file should be created
        """
        default_config = """# dialtor configuration file

[connection]
# Tor control port (default: 9051)
control_port = 9051

# Tor control socket (alternative to port)
# control_socket = "/var/run/tor/control"

# Control port password (optional)
# password = "your_password"
# Or use environment variable: ${DIALTOR_PASSWORD}

# Connection timeout in seconds
timeout = 30

[relay_selection]
# Preferred country codes (ISO 3166-1 alpha-2)
preferred_countries = []

# Minimum bandwidth in bytes/sec (0 = no minimum)
min_bandwidth = 0

# Required relay flags
required_flags = ["Running", "Valid"]

[logging]
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
level = "INFO"

# Log file path (optional, logs to console if not specified)
# file = "~/.dialtor/dialtor.log"
"""

        # Create parent directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write default configuration
        path.write_text(default_config)
