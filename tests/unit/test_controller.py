"""Unit tests for TorController."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from dialtor.core.controller import TorController
from dialtor.utils.exceptions import (
    TorAuthenticationError,
    TorConnectionError,
    TorNotRunningError,
)


class TestTorController:
    """Test TorController class."""

    def test_init_with_defaults(self) -> None:
        """Test controller initialization with default values."""
        controller = TorController()
        assert controller.port == 9051
        assert controller.password is None
        assert not controller.is_connected()

    def test_init_with_custom_values(self) -> None:
        """Test controller initialization with custom values."""
        controller = TorController(port=9052, password="secret")
        assert controller.port == 9052
        assert controller.password == "secret"

    @patch("dialtor.core.controller.Controller")
    def test_connect_success(self, mock_controller_class: Mock) -> None:
        """Test successful connection to Tor."""
        mock_stem_controller = MagicMock()
        mock_controller_class.from_port.return_value.__enter__.return_value = (
            mock_stem_controller
        )

        controller = TorController()
        result = controller.connect()

        assert result is True
        assert controller.is_connected()
        mock_controller_class.from_port.assert_called_once_with(port=9051)

    @patch("dialtor.core.controller.Controller")
    def test_connect_failure(self, mock_controller_class: Mock) -> None:
        """Test connection failure."""
        from stem import SocketError

        mock_controller_class.from_port.side_effect = SocketError("Connection refused")

        controller = TorController()

        with pytest.raises(TorNotRunningError) as exc_info:
            controller.connect()

        assert "not running" in str(exc_info.value).lower()

    @patch("dialtor.core.controller.Controller")
    def test_authenticate_success(self, mock_controller_class: Mock) -> None:
        """Test successful authentication."""
        mock_stem_controller = MagicMock()
        mock_controller_class.from_port.return_value.__enter__.return_value = (
            mock_stem_controller
        )

        controller = TorController(password="secret")
        controller.connect()
        result = controller.authenticate()

        assert result is True
        mock_stem_controller.authenticate.assert_called_once_with(password="secret")

    @patch("dialtor.core.controller.Controller")
    def test_authenticate_failure(self, mock_controller_class: Mock) -> None:
        """Test authentication failure."""
        from stem.connection import AuthenticationFailure

        mock_stem_controller = MagicMock()
        mock_stem_controller.authenticate.side_effect = AuthenticationFailure("Invalid password")
        mock_controller_class.from_port.return_value.__enter__.return_value = (
            mock_stem_controller
        )

        controller = TorController(password="wrong")
        controller.connect()

        with pytest.raises(TorAuthenticationError) as exc_info:
            controller.authenticate()

        assert "authentication failed" in str(exc_info.value).lower()

    @patch("dialtor.core.controller.Controller")
    def test_get_version(self, mock_controller_class: Mock) -> None:
        """Test getting Tor version."""
        mock_stem_controller = MagicMock()
        mock_stem_controller.get_version.return_value = Mock(version_str="0.4.7.13")
        mock_controller_class.from_port.return_value.__enter__.return_value = (
            mock_stem_controller
        )

        controller = TorController()
        controller.connect()
        controller.authenticate()

        version = controller.get_version()

        assert version == "0.4.7.13"
        mock_stem_controller.get_version.assert_called_once()

    @patch("dialtor.core.controller.Controller")
    def test_context_manager(self, mock_controller_class: Mock) -> None:
        """Test using controller as context manager."""
        mock_stem_controller = MagicMock()
        mock_controller_class.from_port.return_value.__enter__.return_value = (
            mock_stem_controller
        )

        with TorController() as controller:
            assert controller.is_connected()

        # Should disconnect on exit
        mock_stem_controller.close.assert_called_once()

    @patch("dialtor.core.controller.Controller")
    def test_get_info(self, mock_controller_class: Mock) -> None:
        """Test getting information from Tor."""
        mock_stem_controller = MagicMock()
        mock_stem_controller.get_info.return_value = "value"
        mock_controller_class.from_port.return_value.__enter__.return_value = (
            mock_stem_controller
        )

        controller = TorController()
        controller.connect()
        controller.authenticate()

        result = controller.get_info("version")

        assert result == "value"
        mock_stem_controller.get_info.assert_called_once_with("version")
