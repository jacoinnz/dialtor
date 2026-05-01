"""Unit tests for RelaySelector."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from dialtor.core.relay_selector import RelaySelector
from dialtor.models.relay import Relay, RelayFlags


class TestRelaySelector:
    """Test RelaySelector class."""

    @pytest.fixture
    def mock_controller(self) -> Mock:
        """Create mock TorController."""
        controller = Mock()
        controller.controller = MagicMock()
        return controller

    @pytest.fixture
    def sample_relays(self) -> list[Relay]:
        """Create sample relay data."""
        return [
            Relay(
                fingerprint="AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555",
                nickname="FastRelay1",
                address="192.168.1.1",
                or_port=9001,
                dir_port=9030,
                flags={RelayFlags.FAST, RelayFlags.STABLE, RelayFlags.RUNNING, RelayFlags.VALID},
                bandwidth=10485760,  # 10 MB/s
                country_code="US",
            ),
            Relay(
                fingerprint="BBBB2222CCCC3333DDDD4444EEEE5555FFFF6666",
                nickname="GuardRelay1",
                address="192.168.1.2",
                or_port=9001,
                dir_port=9030,
                flags={RelayFlags.GUARD, RelayFlags.STABLE, RelayFlags.RUNNING, RelayFlags.VALID},
                bandwidth=5242880,  # 5 MB/s
                country_code="DE",
            ),
            Relay(
                fingerprint="CCCC3333DDDD4444EEEE5555FFFF6666AAAA7777",
                nickname="ExitRelay1",
                address="192.168.1.3",
                or_port=9001,
                dir_port=9030,
                flags={RelayFlags.EXIT, RelayFlags.FAST, RelayFlags.RUNNING, RelayFlags.VALID},
                bandwidth=2097152,  # 2 MB/s
                country_code="US",
            ),
            Relay(
                fingerprint="DDDD4444EEEE5555FFFF6666AAAA7777BBBB8888",
                nickname="SlowRelay1",
                address="192.168.1.4",
                or_port=9001,
                dir_port=0,
                flags={RelayFlags.RUNNING, RelayFlags.VALID},
                bandwidth=524288,  # 0.5 MB/s
                country_code="NL",
            ),
        ]

    def test_init(self, mock_controller: Mock) -> None:
        """Test RelaySelector initialization."""
        selector = RelaySelector(mock_controller)
        assert selector.controller == mock_controller
        assert selector._relay_cache is None

    def test_filter_by_country(self, mock_controller: Mock, sample_relays: list[Relay]) -> None:
        """Test filtering relays by country code."""
        selector = RelaySelector(mock_controller)
        selector._relay_cache = sample_relays

        us_relays = selector.filter_by_country("US")

        assert len(us_relays) == 2
        assert all(r.country_code == "US" for r in us_relays)
        assert {r.nickname for r in us_relays} == {"FastRelay1", "ExitRelay1"}

    def test_filter_by_country_case_insensitive(
        self, mock_controller: Mock, sample_relays: list[Relay]
    ) -> None:
        """Test country filtering is case-insensitive."""
        selector = RelaySelector(mock_controller)
        selector._relay_cache = sample_relays

        de_relays = selector.filter_by_country("de")

        assert len(de_relays) == 1
        assert de_relays[0].country_code == "DE"

    def test_filter_by_flags(self, mock_controller: Mock, sample_relays: list[Relay]) -> None:
        """Test filtering relays by flags."""
        selector = RelaySelector(mock_controller)
        selector._relay_cache = sample_relays

        fast_relays = selector.filter_by_flags({RelayFlags.FAST})

        assert len(fast_relays) == 2
        assert all(RelayFlags.FAST in r.flags for r in fast_relays)

    def test_filter_by_multiple_flags(
        self, mock_controller: Mock, sample_relays: list[Relay]
    ) -> None:
        """Test filtering by multiple flags (all must be present)."""
        selector = RelaySelector(mock_controller)
        selector._relay_cache = sample_relays

        fast_stable_relays = selector.filter_by_flags({RelayFlags.FAST, RelayFlags.STABLE})

        assert len(fast_stable_relays) == 1
        assert fast_stable_relays[0].nickname == "FastRelay1"

    def test_filter_by_bandwidth(
        self, mock_controller: Mock, sample_relays: list[Relay]
    ) -> None:
        """Test filtering relays by minimum bandwidth."""
        selector = RelaySelector(mock_controller)
        selector._relay_cache = sample_relays

        # Filter for relays with at least 3 MB/s
        fast_enough = selector.filter_by_bandwidth(3145728)

        assert len(fast_enough) == 2
        assert all(r.bandwidth >= 3145728 for r in fast_enough)
        assert {r.nickname for r in fast_enough} == {"FastRelay1", "GuardRelay1"}

    def test_filter_chaining(self, mock_controller: Mock, sample_relays: list[Relay]) -> None:
        """Test chaining multiple filters."""
        selector = RelaySelector(mock_controller)
        selector._relay_cache = sample_relays

        # Find fast US relays
        relays = selector.filter_by_country("US")
        relays = [r for r in relays if RelayFlags.FAST in r.flags]

        assert len(relays) == 2
        assert {r.nickname for r in relays} == {"FastRelay1", "ExitRelay1"}

    def test_select_random(self, mock_controller: Mock, sample_relays: list[Relay]) -> None:
        """Test random relay selection."""
        selector = RelaySelector(mock_controller)
        selector._relay_cache = sample_relays

        selected = selector.select_random(count=2)

        assert len(selected) == 2
        assert all(r in sample_relays for r in selected)
        # Check that they're different relays
        assert selected[0].fingerprint != selected[1].fingerprint

    def test_select_random_with_filters(
        self, mock_controller: Mock, sample_relays: list[Relay]
    ) -> None:
        """Test random selection with filters applied."""
        selector = RelaySelector(mock_controller)
        selector._relay_cache = sample_relays

        selected = selector.select_random(
            count=1, country="US", flags={RelayFlags.FAST}, min_bandwidth=5000000
        )

        assert len(selected) == 1
        assert selected[0].nickname == "FastRelay1"

    def test_select_random_not_enough_relays(
        self, mock_controller: Mock, sample_relays: list[Relay]
    ) -> None:
        """Test random selection when not enough relays match filters."""
        selector = RelaySelector(mock_controller)
        selector._relay_cache = sample_relays

        # Only 2 US relays, but requesting 5
        selected = selector.select_random(count=5, country="US")

        assert len(selected) == 2  # Should return all matching relays

    def test_get_relay_info_found(
        self, mock_controller: Mock, sample_relays: list[Relay]
    ) -> None:
        """Test getting relay info by fingerprint."""
        selector = RelaySelector(mock_controller)
        selector._relay_cache = sample_relays

        relay = selector.get_relay_info("AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555")

        assert relay is not None
        assert relay.nickname == "FastRelay1"

    def test_get_relay_info_not_found(
        self, mock_controller: Mock, sample_relays: list[Relay]
    ) -> None:
        """Test getting relay info with invalid fingerprint."""
        selector = RelaySelector(mock_controller)
        selector._relay_cache = sample_relays

        relay = selector.get_relay_info("NONEXISTENT123456789")

        assert relay is None

    def test_get_relay_info_partial_fingerprint(
        self, mock_controller: Mock, sample_relays: list[Relay]
    ) -> None:
        """Test getting relay info with partial fingerprint."""
        selector = RelaySelector(mock_controller)
        selector._relay_cache = sample_relays

        # Should match by prefix
        relay = selector.get_relay_info("AAAA1111")

        assert relay is not None
        assert relay.nickname == "FastRelay1"
