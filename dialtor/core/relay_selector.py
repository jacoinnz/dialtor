"""Relay selection and filtering."""

import random
from typing import List, Optional, Set

from dialtor.core.controller import TorController
from dialtor.models.relay import Relay, RelayFlags


class RelaySelector:
    """Select and filter Tor relays based on criteria."""

    def __init__(self, controller: TorController) -> None:
        """Initialize relay selector.

        Args:
            controller: TorController instance
        """
        self.controller = controller
        self._relay_cache: Optional[List[Relay]] = None

    def get_all_relays(self, refresh: bool = False) -> List[Relay]:
        """Get all available relays from consensus.

        Args:
            refresh: Force refresh of cached data

        Returns:
            List of all relays
        """
        if self._relay_cache is not None and not refresh:
            return self._relay_cache

        relays = []

        # Get all relay descriptors from Tor
        for desc in self.controller.controller.get_network_statuses():
            # Parse relay flags
            flags = set()
            if desc.flags:
                for flag in desc.flags:
                    try:
                        flags.add(RelayFlags(flag))
                    except ValueError:
                        # Skip unknown flags
                        pass

            # Get country code if available
            country_code = None
            if hasattr(desc, "country_code"):
                country_code = desc.country_code

            # Create Relay object
            relay = Relay(
                fingerprint=desc.fingerprint,
                nickname=desc.nickname,
                address=desc.address,
                or_port=desc.or_port,
                dir_port=desc.dir_port if hasattr(desc, "dir_port") else 0,
                flags=flags,
                bandwidth=desc.bandwidth if hasattr(desc, "bandwidth") else 0,
                country_code=country_code,
            )
            relays.append(relay)

        # Cache the results
        self._relay_cache = relays
        return relays

    def filter_by_country(self, country_code: str, relays: Optional[List[Relay]] = None) -> List[Relay]:
        """Filter relays by country code.

        Args:
            country_code: Two-letter country code (case-insensitive)
            relays: Optional list of relays to filter (uses cache if not provided)

        Returns:
            Filtered list of relays
        """
        if relays is None:
            relays = self._relay_cache if self._relay_cache else []

        country_code = country_code.upper()
        return [r for r in relays if r.country_code and r.country_code.upper() == country_code]

    def filter_by_flags(
        self, flags: Set[RelayFlags], relays: Optional[List[Relay]] = None
    ) -> List[Relay]:
        """Filter relays by flags (all flags must be present).

        Args:
            flags: Set of required flags
            relays: Optional list of relays to filter (uses cache if not provided)

        Returns:
            Filtered list of relays
        """
        if relays is None:
            relays = self._relay_cache if self._relay_cache else []

        return [r for r in relays if flags.issubset(r.flags)]

    def filter_by_bandwidth(
        self, min_bandwidth: int, relays: Optional[List[Relay]] = None
    ) -> List[Relay]:
        """Filter relays by minimum bandwidth.

        Args:
            min_bandwidth: Minimum bandwidth in bytes/sec
            relays: Optional list of relays to filter (uses cache if not provided)

        Returns:
            Filtered list of relays
        """
        if relays is None:
            relays = self._relay_cache if self._relay_cache else []

        return [r for r in relays if r.bandwidth >= min_bandwidth]

    def select_random(
        self,
        count: int = 1,
        country: Optional[str] = None,
        flags: Optional[Set[RelayFlags]] = None,
        min_bandwidth: Optional[int] = None,
        relays: Optional[List[Relay]] = None,
    ) -> List[Relay]:
        """Select random relays matching criteria.

        Args:
            count: Number of relays to select
            country: Optional country code filter
            flags: Optional flags filter
            min_bandwidth: Optional minimum bandwidth filter
            relays: Optional list of relays to select from (uses cache if not provided)

        Returns:
            List of randomly selected relays (may be fewer than count if not enough match)
        """
        if relays is None:
            relays = self._relay_cache if self._relay_cache else []

        # Apply filters
        filtered = relays
        if country:
            filtered = self.filter_by_country(country, filtered)
        if flags:
            filtered = self.filter_by_flags(flags, filtered)
        if min_bandwidth:
            filtered = self.filter_by_bandwidth(min_bandwidth, filtered)

        # Select random subset
        if len(filtered) <= count:
            return filtered

        return random.sample(filtered, count)

    def get_relay_info(self, fingerprint: str) -> Optional[Relay]:
        """Get detailed information about a specific relay.

        Args:
            fingerprint: Relay fingerprint (full or partial)

        Returns:
            Relay object or None if not found
        """
        if not self._relay_cache:
            return None

        fingerprint = fingerprint.upper()

        # Try exact match first
        for relay in self._relay_cache:
            if relay.fingerprint == fingerprint:
                return relay

        # Try prefix match
        for relay in self._relay_cache:
            if relay.fingerprint.startswith(fingerprint):
                return relay

        return None
