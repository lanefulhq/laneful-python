"""
Laneful Python Client Library

A Python client library for the Laneful API with both sync and async support.

Installation:
- Default (sync only): pip install laneful-python
- Async support: pip install laneful-python[async]
- Full support: pip install laneful-python[all]
"""

from typing import List

from .exceptions import LanefulAPIError, LanefulAuthError, LanefulError
from .models import Address, Attachment, Email, EmailResponse, TrackingSettings

# Always available (sync client)
try:
    from .client import LanefulClient

    _has_sync = True
except ImportError:
    _has_sync = False
    LanefulClient = None

# Conditionally available (async client)
try:
    from .async_client import AsyncLanefulClient

    _has_async = True
except ImportError:
    _has_async = False
    AsyncLanefulClient = None

__version__ = "1.0.0"

# Build __all__ dynamically based on available imports
__all__ = [
    # Models (always available)
    "Address",
    "Attachment",
    "Email",
    "EmailResponse",
    "TrackingSettings",
    # Exceptions (always available)
    "LanefulError",
    "LanefulAPIError",
    "LanefulAuthError",
]

# Add clients if available
if _has_sync:
    __all__.append("LanefulClient")
if _has_async:
    __all__.append("AsyncLanefulClient")


# Convenience functions to check what's available
def has_sync_support() -> bool:
    """Check if synchronous client support is available."""
    return _has_sync


def has_async_support() -> bool:
    """Check if asynchronous client support is available."""
    return _has_async


def get_available_clients() -> List[str]:
    """Get a list of available client types."""
    clients = []
    if _has_sync:
        clients.append("sync")
    if _has_async:
        clients.append("async")
    return clients


__all__.extend(["has_sync_support", "has_async_support", "get_available_clients"])
