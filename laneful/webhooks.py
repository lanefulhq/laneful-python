"""
Webhook handling for Laneful API events.
"""

import hashlib
import hmac
import json
import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class WebhookEventType(Enum):
    """Webhook event types, as sent in each event's ``event`` field."""

    REQUEST = "request"
    DELIVERY = "delivery"
    OPEN = "open"
    CLICK = "click"
    DROP = "drop"
    SPAM_COMPLAINT = "spam_complaint"
    UNSUBSCRIBE = "unsubscribe"
    BOUNCE = "bounce"

    # Deprecated aliases for the old email.* names, which never matched a Laneful
    # event. They resolve to the real event types and will be removed in 2.0.
    EMAIL_SENT = "request"
    EMAIL_DELIVERED = "delivery"
    EMAIL_OPENED = "open"
    EMAIL_CLICKED = "click"
    EMAIL_BOUNCED = "bounce"
    EMAIL_COMPLAINED = "spam_complaint"
    EMAIL_UNSUBSCRIBED = "unsubscribe"
    EMAIL_FAILED = "drop"


# Deprecated email.* event names and the real event names they map to.
_LEGACY_EVENT_NAMES = {
    "email.sent": "request",
    "email.delivered": "delivery",
    "email.opened": "open",
    "email.clicked": "click",
    "email.bounced": "bounce",
    "email.complained": "spam_complaint",
    "email.unsubscribed": "unsubscribe",
    "email.failed": "drop",
}

# Fields every event carries; everything else is event-specific and goes into data.
_COMMON_EVENT_FIELDS = {
    "id",
    "event",
    "event_type",
    "message_id",
    "email",
    "timestamp",
    "lane_id",
    "tag",
    "metadata",
    "data",
}


def _event_name(event_type: Union[str, WebhookEventType], warn: bool = True) -> str:
    """Normalize an event type to the name Laneful sends, mapping deprecated names."""
    if isinstance(event_type, WebhookEventType):
        return event_type.value
    if event_type in _LEGACY_EVENT_NAMES:
        if warn:
            warnings.warn(
                f"Webhook event name {event_type!r} is deprecated; use "
                f"{_LEGACY_EVENT_NAMES[event_type]!r}",
                DeprecationWarning,
                stacklevel=3,
            )
        return _LEGACY_EVENT_NAMES[event_type]
    return event_type


@dataclass
class WebhookEvent:
    """Webhook event data.

    Common fields are attributes. Event-specific fields (url, referer, client_ip,
    is_hard, code, extended_code, text, reason, mx_host, ...) are in ``data``.
    ``id`` is unique per event and unchanged when an event is delivered again.
    """

    event_type: str
    message_id: str
    email: str
    timestamp: int
    data: Dict[str, Any]
    id: str = ""
    lane_id: str = ""
    tag: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookEvent":
        """Create WebhookEvent from webhook payload."""
        extra = {k: v for k, v in data.items() if k not in _COMMON_EVENT_FIELDS}
        nested = data.get("data")
        if isinstance(nested, dict):
            extra.update(nested)
        return cls(
            event_type=str(data.get("event_type") or data.get("event") or ""),
            message_id=data.get("message_id", ""),
            email=data.get("email", ""),
            timestamp=data.get("timestamp", 0),
            data=extra,
            id=data.get("id") or "",
            lane_id=data.get("lane_id") or "",
            tag=data.get("tag") or "",
            metadata=data.get("metadata") or {},
        )


class WebhookHandler:
    """
    Handler for processing Laneful webhook events.

    Example:
        handler = WebhookHandler("your-webhook-secret")

        @handler.on("delivery")
        def handle_delivered(event: WebhookEvent):
            print(f"Email {event.message_id} was delivered to {event.email}")

        # In your web framework handler:
        if handler.verify_signature(request_body, signature_header):
            handler.process_webhook(request_body)
    """

    def __init__(self, webhook_secret: Optional[str] = None) -> None:
        """
        Initialize webhook handler.

        Args:
            webhook_secret: Secret key for verifying webhook signatures
        """
        self.webhook_secret = webhook_secret
        self._handlers: Dict[str, Callable[[WebhookEvent], None]] = {}

    def verify_signature(self, payload: Union[str, bytes], signature: str) -> bool:
        """
        Verify webhook signature to ensure authenticity.

        Args:
            payload: The raw webhook payload
            signature: The signature header from the webhook request

        Returns:
            True if signature is valid, False otherwise (always False when the
            handler was created without a secret)
        """
        if not self.webhook_secret or not signature:
            return False

        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        # Extract signature from header (format: "sha256=signature")
        if signature.startswith("sha256="):
            signature = signature[7:]

        # Calculate expected signature
        expected_signature = hmac.new(
            self.webhook_secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)

    def on(
        self, event_type: Union[str, WebhookEventType]
    ) -> Callable[[Callable[[WebhookEvent], None]], Callable[[WebhookEvent], None]]:
        """
        Decorator to register event handlers.

        Args:
            event_type: The event type to handle (e.g., "delivery")

        Returns:
            Decorator function
        """
        name = _event_name(event_type)

        def decorator(
            func: Callable[[WebhookEvent], None],
        ) -> Callable[[WebhookEvent], None]:
            self._handlers[name] = func
            return func

        return decorator

    def register_handler(
        self,
        event_type: Union[str, WebhookEventType],
        handler: Callable[[WebhookEvent], None],
    ) -> None:
        """
        Register an event handler function.

        Args:
            event_type: The event type to handle
            handler: The handler function
        """
        self._handlers[_event_name(event_type)] = handler

    def process_webhook(
        self, payload: Union[str, bytes, Dict[str, Any], List[Dict[str, Any]]]
    ) -> None:
        """
        Process a webhook payload and call appropriate handlers.

        Args:
            payload: The webhook payload: a JSON string or bytes, a single event
                dict, or a list of event dicts (batch mode)

        Raises:
            ValueError: If payload is invalid
        """
        if isinstance(payload, (str, bytes)):
            try:
                data = json.loads(payload)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON payload: {e}")
        else:
            data = payload

        events = data if isinstance(data, list) else [data]
        for event_data in events:
            if not isinstance(event_data, dict):
                raise ValueError("Invalid webhook event structure")
            event = WebhookEvent.from_dict(event_data)
            name = _event_name(event.event_type, warn=False)
            # Call the appropriate handler if one is registered
            if name in self._handlers:
                self._handlers[name](event)

    def handle_event(
        self, event_type: Union[str, WebhookEventType], event: WebhookEvent
    ) -> None:
        """
        Manually trigger an event handler.

        Args:
            event_type: The event type
            event: The webhook event data
        """
        name = _event_name(event_type)
        if name in self._handlers:
            self._handlers[name](event)


class WebhookVerifier:
    """Utility class for verifying webhook signatures."""

    VALID_EVENT_TYPES = {
        "request",
        "delivery",
        "open",
        "click",
        "drop",
        "spam_complaint",
        "unsubscribe",
        "bounce",
    }

    @staticmethod
    def verify_signature(secret: str, payload: str, signature: str) -> bool:
        """Verify the HMAC-SHA256 signature of a webhook payload."""
        if not secret or not payload or not signature:
            return False

        clean_signature = (
            signature[7:] if signature.startswith("sha256=") else signature
        )
        expected = hmac.new(
            secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(clean_signature, expected)

    @staticmethod
    def generate_signature(
        secret: str, payload: str, include_prefix: bool = False
    ) -> str:
        """Generate a signature for a payload (useful for testing)."""
        signature = hmac.new(
            secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}" if include_prefix else signature

    @classmethod
    def parse_webhook_payload(cls, payload: str) -> Dict[str, Any]:
        """Validate webhook payload structure and extract events.

        Returns:
            Dict with is_batch (bool) and events (list of event dicts)
        """
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON payload: {exc}") from exc

        if isinstance(data, list) and data:
            for event in data:
                cls._validate_event_structure(event)
            return {"is_batch": True, "events": data}

        if isinstance(data, dict) and "event" in data:
            cls._validate_event_structure(data)
            return {"is_batch": False, "events": [data]}

        raise ValueError("Invalid webhook payload structure")

    @classmethod
    def _validate_event_structure(cls, event: Any) -> None:
        if not isinstance(event, dict):
            raise ValueError("Invalid webhook event structure")

        for field_name in ("event", "email", "lane_id", "message_id", "timestamp"):
            if field_name not in event:
                raise ValueError(f"Missing required field: {field_name}")

        # Unknown event types are kept, so a batch that includes an event type
        # added after this SDK release isn't rejected as a whole.
        if not isinstance(event["event"], str) or not event["event"]:
            raise ValueError(f"Invalid event type: {event['event']!r}")

        if "@" not in str(event["email"]):
            raise ValueError(f"Invalid email format: {event['email']}")

        if not isinstance(event["timestamp"], (int, float, str)) or (
            isinstance(event["timestamp"], str) and not event["timestamp"].isdigit()
        ):
            raise ValueError("Invalid timestamp format")

    @staticmethod
    def get_signature_header_name() -> str:
        """Return the documented webhook signature header name."""
        return "x-webhook-signature"

    @classmethod
    def extract_signature_from_headers(cls, headers: Dict[str, Any]) -> Optional[str]:
        """Extract the webhook signature from HTTP headers."""
        documented = cls.get_signature_header_name()
        if documented in headers:
            return str(headers[documented])

        upper = documented.upper().replace("-", "_")
        if upper in headers:
            return str(headers[upper])

        server_header = f"HTTP_{upper}"
        if server_header in headers:
            return str(headers[server_header])

        return None
