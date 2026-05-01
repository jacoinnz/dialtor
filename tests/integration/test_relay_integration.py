"""Integration tests for relay features (requires Tor daemon)."""

import pytest

from dialtor.core.controller import TorController
from dialtor.core.relay_selector import RelaySelector
from dialtor.models.relay import RelayFlags


@pytest.mark.integration
class TestRelayIntegration:
    """Integration tests for relay selector with real Tor."""

    def test_get_all_relays(self, tor_running: bool) -> None:
        """Test fetching relay consensus from real Tor."""
        if not tor_running:
            pytest.skip("Tor daemon not running")

        with TorController() as controller:
            selector = RelaySelector(controller)
            relays = selector.get_all_relays()

            # Should have many relays in consensus
            assert len(relays) > 100
            assert all(r.fingerprint for r in relays)
            assert all(r.nickname for r in relays)
            assert all(r.address for r in relays)

    def test_filter_by_country_real(self, tor_running: bool) -> None:
        """Test country filtering with real data."""
        if not tor_running:
            pytest.skip("Tor daemon not running")

        with TorController() as controller:
            selector = RelaySelector(controller)
            selector.get_all_relays()

            # Filter for US relays
            us_relays = selector.filter_by_country("US")

            assert len(us_relays) > 0
            assert all(r.country_code == "US" for r in us_relays)

    def test_filter_by_flags_real(self, tor_running: bool) -> None:
        """Test flag filtering with real data."""
        if not tor_running:
            pytest.skip("Tor daemon not running")

        with TorController() as controller:
            selector = RelaySelector(controller)
            selector.get_all_relays()

            # Filter for fast relays
            fast_relays = selector.filter_by_flags({RelayFlags.FAST})

            assert len(fast_relays) > 0
            assert all(RelayFlags.FAST in r.flags for r in fast_relays)

    def test_select_exit_relay(self, tor_running: bool) -> None:
        """Test selecting suitable exit relay."""
        if not tor_running:
            pytest.skip("Tor daemon not running")

        with TorController() as controller:
            selector = RelaySelector(controller)
            selector.get_all_relays()

            # Select exit relays
            exit_relays = selector.select_random(
                count=5, flags={RelayFlags.EXIT, RelayFlags.RUNNING, RelayFlags.VALID}
            )

            assert len(exit_relays) > 0
            assert all(RelayFlags.EXIT in r.flags for r in exit_relays)
            assert all(RelayFlags.RUNNING in r.flags for r in exit_relays)

    def test_get_relay_info_real(self, tor_running: bool) -> None:
        """Test getting specific relay info."""
        if not tor_running:
            pytest.skip("Tor daemon not running")

        with TorController() as controller:
            selector = RelaySelector(controller)
            all_relays = selector.get_all_relays()

            # Get info for first relay
            first_relay = all_relays[0]
            relay_info = selector.get_relay_info(first_relay.fingerprint)

            assert relay_info is not None
            assert relay_info.fingerprint == first_relay.fingerprint
            assert relay_info.nickname == first_relay.nickname

    def test_bandwidth_filtering(self, tor_running: bool) -> None:
        """Test filtering by bandwidth."""
        if not tor_running:
            pytest.skip("Tor daemon not running")

        with TorController() as controller:
            selector = RelaySelector(controller)
            selector.get_all_relays()

            # Filter for high-bandwidth relays (>= 10 MB/s)
            high_bw_relays = selector.filter_by_bandwidth(10485760)

            assert all(r.bandwidth >= 10485760 for r in high_bw_relays)

    def test_combined_filters(self, tor_running: bool) -> None:
        """Test combining multiple filters."""
        if not tor_running:
            pytest.skip("Tor daemon not running")

        with TorController() as controller:
            selector = RelaySelector(controller)
            selector.get_all_relays()

            # Find fast, stable guard relays with good bandwidth
            relays = selector.select_random(
                count=3,
                flags={RelayFlags.GUARD, RelayFlags.FAST, RelayFlags.STABLE},
                min_bandwidth=5242880,  # 5 MB/s
            )

            for relay in relays:
                assert RelayFlags.GUARD in relay.flags
                assert RelayFlags.FAST in relay.flags
                assert RelayFlags.STABLE in relay.flags
                assert relay.bandwidth >= 5242880
