"""Unit tests for ConfigLoader."""

import os
from pathlib import Path
from typing import Generator
from unittest.mock import mock_open, patch

import pytest

from dialtor.models.config import DialtorConfig
from dialtor.utils.config_loader import ConfigLoader
from dialtor.utils.exceptions import ConfigurationError


@pytest.fixture
def sample_config_toml() -> str:
    """Sample TOML configuration."""
    return """
[connection]
control_port = 9052
password = "test_password"
timeout = 60

[relay_selection]
preferred_countries = ["us", "de"]
min_bandwidth = 2097152
required_flags = ["Fast", "Stable", "Guard"]

[logging]
level = "DEBUG"
file = "/var/log/dialtor.log"
"""


@pytest.fixture
def minimal_config_toml() -> str:
    """Minimal TOML configuration."""
    return """
[connection]
control_port = 9051
"""


class TestConfigLoader:
    """Test ConfigLoader class."""

    def test_load_default_config(self) -> None:
        """Test loading with no config file returns defaults."""
        with patch("dialtor.utils.config_loader.Path.exists", return_value=False):
            config = ConfigLoader.load()

        assert config.connection.control_port == 9051
        assert config.connection.password is None
        assert config.connection.timeout == 30
        assert config.relay_selection.min_bandwidth == 0
        assert config.relay_selection.required_flags == ["Running", "Valid"]
        assert config.logging.level == "INFO"

    def test_load_from_file(self, sample_config_toml: str, tmp_path: Path) -> None:
        """Test loading configuration from file."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(sample_config_toml)

        config = ConfigLoader.load(config_path=config_file)

        assert config.connection.control_port == 9052
        assert config.connection.password == "test_password"
        assert config.connection.timeout == 60
        assert config.relay_selection.preferred_countries == ["us", "de"]
        assert config.relay_selection.min_bandwidth == 2097152
        assert config.relay_selection.required_flags == ["Fast", "Stable", "Guard"]
        assert config.logging.level == "DEBUG"
        assert config.logging.file == "/var/log/dialtor.log"

    def test_load_minimal_config(self, minimal_config_toml: str, tmp_path: Path) -> None:
        """Test loading minimal config merges with defaults."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(minimal_config_toml)

        config = ConfigLoader.load(config_path=config_file)

        assert config.connection.control_port == 9051
        assert config.connection.timeout == 30  # default
        assert config.relay_selection.min_bandwidth == 0  # default

    def test_load_with_env_override(self, sample_config_toml: str, tmp_path: Path) -> None:
        """Test environment variable override."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(sample_config_toml)

        with patch.dict(os.environ, {"DIALTOR_CONTROL_PORT": "9053", "DIALTOR_PASSWORD": "env_pwd"}):
            config = ConfigLoader.load_with_env_override(config_path=config_file)

        assert config.connection.control_port == 9053  # from env
        assert config.connection.password == "env_pwd"  # from env
        assert config.connection.timeout == 60  # from file

    def test_load_invalid_toml(self) -> None:
        """Test loading invalid TOML raises error."""
        invalid_toml = "this is not valid TOML [["

        with patch("dialtor.utils.config_loader.Path.exists", return_value=True), patch(
            "builtins.open", mock_open(read_data=invalid_toml)
        ):
            with pytest.raises(ConfigurationError):
                ConfigLoader.load()

    def test_load_from_custom_path(self, sample_config_toml: str, tmp_path: Path) -> None:
        """Test loading from custom config path."""
        custom_path = tmp_path / "custom_config.toml"
        custom_path.write_text(sample_config_toml)

        config = ConfigLoader.load(config_path=custom_path)

        assert config.connection.control_port == 9052

    def test_create_default_config(self, tmp_path: Path) -> None:
        """Test creating default configuration file."""
        config_file = tmp_path / "config.toml"

        ConfigLoader.create_default_config(config_file)

        assert config_file.exists()
        content = config_file.read_text()
        assert "[connection]" in content
        assert "[relay_selection]" in content
        assert "[logging]" in content
