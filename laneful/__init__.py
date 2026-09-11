"""
Laneful Python Client Library

A Python client library for the Laneful API with both sync and async support.

Installation:
- Default (sync only): pip install laneful
- Async support: pip install laneful[async]
- Full support: pip install laneful[all]
"""

from typing import List, Optional, Type

from ._version import __version__
from .exceptions import LanefulAPIError, LanefulAuthError, LanefulError
from .models import (
    Address,
    Attachment,
    Email,
    EmailResponse,
    MailSettings,
    TrackingSettings,
)
from .org_models import (
    CreateDomainRequest,
    Domain,
    DomainSpamRatioRadar,
    GooglePostmasterSpamReport,
    ListDomainSpamRatioRadarParams,
    ListDomainSpamRatioRadarResponse,
    ListDomainsParams,
    ListDomainsResponse,
    ListGooglePostmasterSpamReportsParams,
    ListGooglePostmasterSpamReportsResponse,
    ListSndsReportsParams,
    ListSndsReportsResponse,
    ListUnsubscribeGroupsParams,
    ListUnsubscribeGroupsResponse,
    SndsReport,
    SuccessResponse,
    UnsubscribeGroup,
    UpdateDomainRequest,
)
from .webhooks import WebhookEvent, WebhookEventType, WebhookHandler, WebhookVerifier

# Always available (sync client)
LanefulClient: Optional[Type] = None
try:
    from .client import LanefulClient  # noqa

    _has_sync = True
except ImportError:
    _has_sync = False

# Conditionally available (async client)
AsyncLanefulClient: Optional[Type] = None
try:
    from .async_client import AsyncLanefulClient  # noqa

    _has_async = True
except ImportError:
    _has_async = False

# Build __all__ dynamically based on available imports
__all__ = [
    "__version__",
    # Models (always available)
    "Address",
    "Attachment",
    "Email",
    "EmailResponse",
    "MailSettings",
    "TrackingSettings",
    "CreateDomainRequest",
    "Domain",
    "DomainSpamRatioRadar",
    "GooglePostmasterSpamReport",
    "ListDomainSpamRatioRadarParams",
    "ListDomainSpamRatioRadarResponse",
    "ListDomainsParams",
    "ListDomainsResponse",
    "ListGooglePostmasterSpamReportsParams",
    "ListGooglePostmasterSpamReportsResponse",
    "ListSndsReportsParams",
    "ListSndsReportsResponse",
    "ListUnsubscribeGroupsParams",
    "ListUnsubscribeGroupsResponse",
    "SndsReport",
    "SuccessResponse",
    "UnsubscribeGroup",
    "UpdateDomainRequest",
    "WebhookEvent",
    "WebhookEventType",
    "WebhookHandler",
    "WebhookVerifier",
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
