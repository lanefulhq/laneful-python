"""
Webhook handling for Laneful API events.
"""

import hashlib
import hmac
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, Union


class WebhookEventType(Enum):
    """Webhook event types."""

    EMAIL_SENT = "email.sent"
    EMAIL_DELIVERED = "email.delivered"
    EMAIL_OPENED = "email.opened"
    EMAIL_CLICKED = "email.clicked"
    EMAIL_BOUNCED = "email.bounced"
    EMAIL_COMPLAINED = "email.complained"
    EMAIL_UNSUBSCRIBED = "email.unsubscribed"
    EMAIL_FAILED = "email.failed"
    REQUEST = "request"


@dataclass
class WebhookEvent:
    """Webhook event data."""

    event_type: str
    message_id: str
    email: str
    timestamp: int
    data: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookEvent":
        """Create WebhookEvent from webhook payload."""
        return cls(
            event_type=str(data.get("event_type") or data.get("event") or ""),
            message_id=data.get("message_id", ""),
            email=data.get("email", ""),
            timestamp=data.get("timestamp", 0),
            data=data.get("data", {}),
        )


class WebhookHandler:
    """
    Handler for processing Laneful webhook events.

    Example:
        handler = WebhookHandler("your-webhook-secret")

        @handler.on("email.delivered")
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
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            return True  # Skip verification if no secret is configured

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
        self, event_type: str
    ) -> Callable[[Callable[[WebhookEvent], None]], Callable[[WebhookEvent], None]]:
        """
        Decorator to register event handlers.

        Args:
            event_type: The event type to handle (e.g., "email.delivered")

        Returns:
            Decorator function
        """

        def decorator(
            func: Callable[[WebhookEvent], None],
        ) -> Callable[[WebhookEvent], None]:
            self._handlers[event_type] = func
            return func

        return decorator

    def register_handler(
        self, event_type: str, handler: Callable[[WebhookEvent], None]
    ) -> None:
        """
        Register an event handler function.

        Args:
            event_type: The event type to handle
            handler: The handler function
        """
        self._handlers[event_type] = handler

    def process_webhook(self, payload: Union[str, Dict[str, Any]]) -> None:
        """
        Process a webhook payload and call appropriate handlers.

        Args:
            payload: The webhook payload (JSON string or dict)

        Raises:
            ValueError: If payload is invalid
            KeyError: If required fields are missing
        """
        if isinstance(payload, str):
            try:
                data = json.loads(payload)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON payload: {e}")
        else:
            data = payload

        event = WebhookEvent.from_dict(data)

        # Call the appropriate handler if one is registered
        if event.event_type in self._handlers:
            self._handlers[event.event_type](event)

    def handle_event(self, event_type: str, event: WebhookEvent) -> None:
        """
        Manually trigger an event handler.

        Args:
            event_type: The event type
            event: The webhook event data
        """
        if event_type in self._handlers:
            self._handlers[event_type](event)


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

        if event["event"] not in cls.VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event type: {event['event']}")

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
