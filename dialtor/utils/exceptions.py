"""Custom exceptions for dialtor."""


class DialtorError(Exception):
    """Base exception for all dialtor errors."""

    pass


class TorConnectionError(DialtorError):
    """Failed to connect to Tor control port."""

    pass


class TorAuthenticationError(DialtorError):
    """Failed to authenticate with Tor control port."""

    pass


class TorNotRunningError(DialtorError):
    """Tor daemon is not running or not accessible."""

    pass


class CircuitCreationError(DialtorError):
    """Failed to create or manage a circuit."""

    pass


class InvalidRelayError(DialtorError):
    """Invalid relay fingerprint or specification."""

    pass


class ConfigurationError(DialtorError):
    """Configuration file or settings error."""

    pass


class BridgeError(DialtorError):
    """Bridge configuration or connectivity error."""

    pass


class OnionServiceError(DialtorError):
    """Onion service management error."""

    pass
