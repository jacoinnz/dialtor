"""Tests for TorDaemon process management."""

import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from dialtor.core.tor_daemon import TorDaemon
from dialtor.utils.exceptions import TorNotRunningError


class TestTorDaemon:
    """Test TorDaemon class."""

    def test_init(self) -> None:
        """Test TorDaemon initialization."""
        daemon = TorDaemon(control_port=9051, socks_port=9050)

        assert daemon.control_port == 9051
        assert daemon.socks_port == 9050
        assert daemon.tor_binary == "tor"
        assert daemon._process is None

    def test_init_custom_binary(self) -> None:
        """Test initialization with custom tor binary."""
        daemon = TorDaemon(tor_binary="/usr/local/bin/tor")

        assert daemon.tor_binary == "/usr/local/bin/tor"

    @patch("shutil.which")
    def test_find_tor_binary_found(self, mock_which: Mock) -> None:
        """Test finding tor binary when it exists."""
        mock_which.return_value = "/usr/bin/tor"
        daemon = TorDaemon()

        result = daemon._find_tor_binary()

        assert result == "/usr/bin/tor"
        mock_which.assert_called_once_with("tor")

    @patch("shutil.which")
    def test_find_tor_binary_not_found(self, mock_which: Mock) -> None:
        """Test finding tor binary when it doesn't exist."""
        mock_which.return_value = None
        daemon = TorDaemon()

        result = daemon._find_tor_binary()

        assert result is None

    def test_generate_torrc(self, tmp_path: Path) -> None:
        """Test torrc generation."""
        daemon = TorDaemon(control_port=9051, socks_port=9050, data_dir=tmp_path)

        torrc_path = daemon._generate_torrc()

        assert torrc_path.exists()
        assert torrc_path == tmp_path / "torrc"

        content = torrc_path.read_text()
        assert f"DataDirectory {tmp_path}" in content
        assert "ControlPort 9051" in content
        assert "SocksPort 9050" in content
        assert "CookieAuthentication 1" in content

    def test_generate_torrc_temp_dir(self) -> None:
        """Test torrc generation with temporary directory."""
        daemon = TorDaemon()

        torrc_path = daemon._generate_torrc()

        assert torrc_path.exists()
        assert "dialtor_" in str(torrc_path.parent)

        # Cleanup
        daemon._cleanup()

    @patch("subprocess.Popen")
    @patch("shutil.which")
    def test_start_tor_not_found(self, mock_which: Mock, mock_popen: Mock) -> None:
        """Test starting Tor when binary not found."""
        mock_which.return_value = None
        daemon = TorDaemon()

        with pytest.raises(TorNotRunningError, match="not found in PATH"):
            daemon.start(wait_for_bootstrap=False)

    @patch("socket.socket")
    @patch("subprocess.Popen")
    @patch("shutil.which")
    def test_start_success(
        self, mock_which: Mock, mock_popen: Mock, mock_socket: Mock, tmp_path: Path
    ) -> None:
        """Test successful Tor daemon start."""
        mock_which.return_value = "/usr/bin/tor"
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Mock socket connection success
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock

        daemon = TorDaemon(data_dir=tmp_path)
        daemon.start(wait_for_bootstrap=True, timeout=5)

        assert daemon.is_running()
        assert daemon.pid == 12345
        mock_popen.assert_called_once()

    @patch("subprocess.Popen")
    @patch("shutil.which")
    def test_start_already_running(
        self, mock_which: Mock, mock_popen: Mock, tmp_path: Path
    ) -> None:
        """Test starting when already running."""
        mock_which.return_value = "/usr/bin/tor"
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        daemon = TorDaemon(data_dir=tmp_path)
        daemon._process = mock_process

        daemon.start(wait_for_bootstrap=False)

        # Should not start new process
        mock_popen.assert_not_called()

    @patch("socket.socket")
    @patch("subprocess.Popen")
    @patch("shutil.which")
    def test_bootstrap_timeout(
        self, mock_which: Mock, mock_popen: Mock, mock_socket: Mock, tmp_path: Path
    ) -> None:
        """Test bootstrap timeout."""
        mock_which.return_value = "/usr/bin/tor"
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Mock socket connection failure
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 1  # Connection refused
        mock_socket.return_value = mock_sock

        daemon = TorDaemon(data_dir=tmp_path)

        with pytest.raises(TorNotRunningError, match="failed to bootstrap"):
            daemon.start(wait_for_bootstrap=True, timeout=1)

    def test_stop_not_running(self) -> None:
        """Test stopping when not running."""
        daemon = TorDaemon()

        # Should not raise
        daemon.stop()

    @patch("subprocess.Popen")
    def test_stop_graceful(self, mock_popen: Mock) -> None:
        """Test graceful Tor daemon stop."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345

        daemon = TorDaemon()
        daemon._process = mock_process

        daemon.stop(timeout=5)

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=5)
        assert daemon._process is None

    @patch("subprocess.Popen")
    def test_stop_force_kill(self, mock_popen: Mock) -> None:
        """Test force kill when graceful shutdown fails."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345
        mock_process.wait.side_effect = [
            subprocess.TimeoutExpired("tor", 5),
            None,
        ]

        daemon = TorDaemon()
        daemon._process = mock_process

        daemon.stop(timeout=1)

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
        assert daemon._process is None

    def test_is_running_true(self) -> None:
        """Test is_running when daemon is running."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None

        daemon = TorDaemon()
        daemon._process = mock_process

        assert daemon.is_running() is True

    def test_is_running_false(self) -> None:
        """Test is_running when daemon is not running."""
        daemon = TorDaemon()

        assert daemon.is_running() is False

    def test_is_running_stopped(self) -> None:
        """Test is_running when daemon has stopped."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Exit code

        daemon = TorDaemon()
        daemon._process = mock_process

        assert daemon.is_running() is False

    def test_pid_property(self) -> None:
        """Test PID property."""
        mock_process = MagicMock()
        mock_process.pid = 12345

        daemon = TorDaemon()
        daemon._process = mock_process

        assert daemon.pid == 12345

    def test_pid_property_not_running(self) -> None:
        """Test PID property when not running."""
        daemon = TorDaemon()

        assert daemon.pid is None

    @patch("socket.socket")
    @patch("subprocess.Popen")
    @patch("shutil.which")
    def test_context_manager(
        self, mock_which: Mock, mock_popen: Mock, mock_socket: Mock, tmp_path: Path
    ) -> None:
        """Test context manager usage."""
        mock_which.return_value = "/usr/bin/tor"
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Mock socket connection success
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock

        with TorDaemon(data_dir=tmp_path) as daemon:
            assert daemon.is_running()

        # Should be stopped after context
        mock_process.terminate.assert_called_once()
