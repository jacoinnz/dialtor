"""Pytest configuration and fixtures."""

import socket
from typing import Generator
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_tor_controller() -> Generator[Mock, None, None]:
    """Provide mock Tor controller for unit tests."""
    mock = Mock()
    mock.get_version.return_value = Mock(version_str="0.4.7.13")
    mock.get_circuits.return_value = []
    mock.get_info.return_value = "test_value"
    yield mock


def is_tor_running() -> bool:
    """Check if Tor daemon is running on default control port.

    Returns:
        True if Tor is accessible on port 9051
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", 9051))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture
def tor_running() -> bool:
    """Fixture that checks if Tor is running.

    Returns:
        True if Tor daemon is running

    Use with pytest.mark.skipif for integration tests:
        @pytest.mark.skipif(not tor_running(), reason="Tor not running")
    """
    return is_tor_running()


# Configure pytest markers
def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (default, no Tor required)")
    config.addinivalue_line(
        "markers", "integration: Integration tests (requires Tor daemon running)"
    )
