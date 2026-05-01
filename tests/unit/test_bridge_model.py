"""Unit tests for Bridge model."""

import pytest

from dialtor.models.bridge import Bridge, BridgeType


class TestBridge:
    """Test Bridge model."""

    def test_vanilla_bridge_creation(self) -> None:
        """Test creating vanilla bridge."""
        bridge = Bridge(address="192.0.2.1", port=9001)

        assert bridge.address == "192.0.2.1"
        assert bridge.port == 9001
        assert bridge.transport == BridgeType.VANILLA
        assert bridge.fingerprint is None

    def test_obfs4_bridge_creation(self) -> None:
        """Test creating obfs4 bridge."""
        bridge = Bridge(
            address="192.0.2.1",
            port=9001,
            fingerprint="AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555",
            transport=BridgeType.OBFS4,
            transport_options="cert=abcd1234,iat-mode=0",
        )

        assert bridge.transport == BridgeType.OBFS4
        assert bridge.fingerprint == "AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555"
        assert bridge.transport_options == "cert=abcd1234,iat-mode=0"

    def test_vanilla_bridge_line_no_fingerprint(self) -> None:
        """Test generating vanilla bridge line without fingerprint."""
        bridge = Bridge(address="192.0.2.1", port=9001)

        assert bridge.bridge_line == "Bridge 192.0.2.1:9001"

    def test_vanilla_bridge_line_with_fingerprint(self) -> None:
        """Test generating vanilla bridge line with fingerprint."""
        bridge = Bridge(
            address="192.0.2.1",
            port=9001,
            fingerprint="AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555",
        )

        assert bridge.bridge_line == "Bridge 192.0.2.1:9001 AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555"

    def test_obfs4_bridge_line(self) -> None:
        """Test generating obfs4 bridge line."""
        bridge = Bridge(
            address="192.0.2.1",
            port=9001,
            fingerprint="AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555",
            transport=BridgeType.OBFS4,
            transport_options="cert=abcd1234,iat-mode=0",
        )

        expected = "Bridge obfs4 192.0.2.1:9001 AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555 cert=abcd1234,iat-mode=0"
        assert bridge.bridge_line == expected

    def test_parse_vanilla_bridge_line(self) -> None:
        """Test parsing vanilla bridge line."""
        line = "Bridge 192.0.2.1:9001"
        bridge = Bridge.from_bridge_line(line)

        assert bridge.address == "192.0.2.1"
        assert bridge.port == 9001
        assert bridge.transport == BridgeType.VANILLA
        assert bridge.fingerprint is None

    def test_parse_vanilla_bridge_with_fingerprint(self) -> None:
        """Test parsing vanilla bridge with fingerprint."""
        line = "Bridge 192.0.2.1:9001 AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555"
        bridge = Bridge.from_bridge_line(line)

        assert bridge.address == "192.0.2.1"
        assert bridge.port == 9001
        assert bridge.fingerprint == "AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555"

    def test_parse_obfs4_bridge_line(self) -> None:
        """Test parsing obfs4 bridge line."""
        line = "Bridge obfs4 192.0.2.1:9001 AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555 cert=abcd1234,iat-mode=0"
        bridge = Bridge.from_bridge_line(line)

        assert bridge.address == "192.0.2.1"
        assert bridge.port == 9001
        assert bridge.transport == BridgeType.OBFS4
        assert bridge.fingerprint == "AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555"
        assert bridge.transport_options == "cert=abcd1234,iat-mode=0"

    def test_parse_obfs4_bridge_without_fingerprint(self) -> None:
        """Test parsing obfs4 bridge without fingerprint."""
        line = "Bridge obfs4 192.0.2.1:9001 cert=abcd1234"
        bridge = Bridge.from_bridge_line(line)

        assert bridge.address == "192.0.2.1"
        assert bridge.port == 9001
        assert bridge.transport == BridgeType.OBFS4
        assert bridge.fingerprint is None
        assert bridge.transport_options == "cert=abcd1234"

    def test_parse_line_without_bridge_prefix(self) -> None:
        """Test parsing line without 'Bridge' prefix."""
        line = "192.0.2.1:9001"
        bridge = Bridge.from_bridge_line(line)

        assert bridge.address == "192.0.2.1"
        assert bridge.port == 9001

    def test_bridge_str_representation(self) -> None:
        """Test bridge string representation."""
        vanilla = Bridge(address="192.0.2.1", port=9001)
        assert str(vanilla) == "192.0.2.1:9001"

        obfs4 = Bridge(address="192.0.2.1", port=9001, transport=BridgeType.OBFS4)
        assert str(obfs4) == "192.0.2.1:9001 (obfs4)"
