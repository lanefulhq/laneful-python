"""Tests for webhook handling functionality."""

import hashlib
import hmac
import json
from unittest.mock import Mock

import pytest

from laneful.webhooks import (
    WebhookEvent,
    WebhookEventType,
    WebhookHandler,
    WebhookVerifier,
)


class TestWebhookEvent:
    """Test cases for WebhookEvent model."""

    def test_webhook_event_creation(self):
        """Test creating webhook event."""
        event = WebhookEvent(
            event_type="email.delivered",
            message_id="msg_123",
            email="user@example.com",
            timestamp=1640995200,
            data={"delivery_time": "2022-01-01T00:00:00Z"},
        )

        assert event.event_type == "email.delivered"
        assert event.message_id == "msg_123"
        assert event.email == "user@example.com"
        assert event.timestamp == 1640995200
        assert event.data == {"delivery_time": "2022-01-01T00:00:00Z"}

    def test_webhook_event_from_dict(self):
        """Test creating webhook event from dictionary."""
        data = {
            "event_type": "email.opened",
            "message_id": "msg_456",
            "email": "user@example.com",
            "timestamp": 1640995260,
            "data": {"user_agent": "Mozilla/5.0"},
        }

        event = WebhookEvent.from_dict(data)
        assert event.event_type == "email.opened"
        assert event.message_id == "msg_456"
        assert event.email == "user@example.com"
        assert event.timestamp == 1640995260
        assert event.data == {"user_agent": "Mozilla/5.0"}

    def test_webhook_event_from_go_event_key(self):
        """Go-style payloads use event instead of event_type."""
        event = WebhookEvent.from_dict({"event": "request", "message_id": "msg_1"})
        assert event.event_type == "request"
        assert event.message_id == "msg_1"

    def test_webhook_event_from_dict_missing_fields(self):
        """Test creating webhook event from dictionary with missing fields."""
        data = {}
        event = WebhookEvent.from_dict(data)

        assert event.event_type == ""
        assert event.message_id == ""
        assert event.email == ""
        assert event.timestamp == 0
        assert event.data == {}


class TestWebhookHandler:
    """Test cases for WebhookHandler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = WebhookHandler(webhook_secret="test-secret")
        self.sample_payload = {
            "event": "delivery",
            "message_id": "msg_123",
            "email": "user@example.com",
            "timestamp": 1640995200,
            "data": {},
        }

    def test_handler_initialization(self):
        """Test webhook handler initialization."""
        handler = WebhookHandler("secret")
        assert handler.webhook_secret == "secret"
        assert handler._handlers == {}

    def test_handler_initialization_no_secret(self):
        """Test webhook handler initialization without secret."""
        handler = WebhookHandler()
        assert handler.webhook_secret is None

    def test_register_handler_decorator(self):
        """Test registering handler using decorator."""
        handler_func = Mock()

        @self.handler.on("delivery")
        def test_handler(event):
            handler_func(event)

        assert "delivery" in self.handler._handlers
        assert self.handler._handlers["delivery"] == test_handler

    def test_register_handler_method(self):
        """Test registering handler using method."""
        handler_func = Mock()

        self.handler.register_handler("open", handler_func)

        assert "open" in self.handler._handlers
        assert self.handler._handlers["open"] == handler_func

    def test_process_webhook_string_payload(self):
        """Test processing webhook with string payload."""
        handler_func = Mock()
        self.handler.register_handler("delivery", handler_func)

        payload_str = json.dumps(self.sample_payload)
        self.handler.process_webhook(payload_str)

        handler_func.assert_called_once()
        event = handler_func.call_args[0][0]
        assert isinstance(event, WebhookEvent)
        assert event.event_type == "delivery"

    def test_process_webhook_dict_payload(self):
        """Test processing webhook with dict payload."""
        handler_func = Mock()
        self.handler.register_handler("delivery", handler_func)

        self.handler.process_webhook(self.sample_payload)

        handler_func.assert_called_once()
        event = handler_func.call_args[0][0]
        assert isinstance(event, WebhookEvent)
        assert event.event_type == "delivery"

    def test_process_webhook_no_handler(self):
        """Test processing webhook with no registered handler."""
        # Should not raise an exception
        self.handler.process_webhook(self.sample_payload)

    def test_process_webhook_invalid_json(self):
        """Test processing webhook with invalid JSON."""
        with pytest.raises(ValueError) as exc_info:
            self.handler.process_webhook("invalid json")

        assert "Invalid JSON payload" in str(exc_info.value)

    def test_verify_signature_valid(self):
        """Test signature verification with valid signature."""
        payload = json.dumps(self.sample_payload)
        signature = hmac.new(
            "test-secret".encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        assert self.handler.verify_signature(payload, f"sha256={signature}")
        assert self.handler.verify_signature(payload, signature)  # without prefix

    def test_verify_signature_invalid(self):
        """Test signature verification with invalid signature."""
        payload = json.dumps(self.sample_payload)

        assert not self.handler.verify_signature(payload, "sha256=invalid")
        assert not self.handler.verify_signature(payload, "invalid")

    def test_verify_signature_no_secret(self):
        """Without a secret, every signature is rejected."""
        handler = WebhookHandler()  # No secret
        payload = json.dumps(self.sample_payload)

        assert not handler.verify_signature(payload, "any-signature")

    def test_verify_signature_empty(self):
        """An empty signature is rejected."""
        payload = json.dumps(self.sample_payload)

        assert not self.handler.verify_signature(payload, "")

    def test_verify_signature_bytes_payload(self):
        """Test signature verification with bytes payload."""
        payload_bytes = json.dumps(self.sample_payload).encode()
        signature = hmac.new(
            "test-secret".encode(), payload_bytes, hashlib.sha256
        ).hexdigest()

        assert self.handler.verify_signature(payload_bytes, f"sha256={signature}")

    def test_handle_event_manual(self):
        """Test manually handling an event."""
        handler_func = Mock()
        self.handler.register_handler("open", handler_func)

        event = WebhookEvent.from_dict(
            {
                "event": "open",
                "message_id": "msg_123",
                "email": "user@example.com",
                "timestamp": 1640995200,
                "data": {},
            }
        )

        self.handler.handle_event("open", event)
        handler_func.assert_called_once_with(event)


class TestWebhookIntegrations:
    """Test webhook framework integrations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = WebhookHandler("test-secret")
        self.sample_payload = {
            "event": "delivery",
            "message_id": "msg_123",
            "email": "user@example.com",
            "timestamp": 1640995200,
            "data": {},
        }


class TestWebhookEventType:
    """Test webhook event type enum."""

    def test_event_types(self):
        """Event types match the names Laneful sends."""
        assert [t.value for t in WebhookEventType] == [
            "request",
            "delivery",
            "open",
            "click",
            "drop",
            "spam_complaint",
            "unsubscribe",
            "bounce",
        ]

    def test_deprecated_aliases_resolve_to_real_types(self):
        """The old EMAIL_* members are aliases of the real event types."""
        assert WebhookEventType.EMAIL_SENT is WebhookEventType.REQUEST
        assert WebhookEventType.EMAIL_DELIVERED is WebhookEventType.DELIVERY
        assert WebhookEventType.EMAIL_OPENED is WebhookEventType.OPEN
        assert WebhookEventType.EMAIL_CLICKED is WebhookEventType.CLICK
        assert WebhookEventType.EMAIL_BOUNCED is WebhookEventType.BOUNCE
        assert WebhookEventType.EMAIL_COMPLAINED is WebhookEventType.SPAM_COMPLAINT
        assert WebhookEventType.EMAIL_UNSUBSCRIBED is WebhookEventType.UNSUBSCRIBE
        assert WebhookEventType.EMAIL_FAILED is WebhookEventType.DROP


class TestWebhookPayloads:
    """Real Laneful payload shapes."""

    def setup_method(self):
        self.handler = WebhookHandler("test-secret")
        self.click = {
            "id": "019844e3a1b27c3d8e4f5a6b7c8d9e0f",
            "event": "click",
            "email": "user@example.com",
            "message_id": "H-1-abc",
            "lane_id": "5805dd85-ed8c-44db-91a7-1d53a41c86a5",
            "tag": "newsletter",
            "timestamp": 1753502600,
            "metadata": {"user_id": "user_123"},
            "url": "https://example.com/product/123",
            "client_ip": "192.168.1.2",
        }
        self.bounce = {
            "id": "8f14e45f-ceea-4e7a-b1c2-6d3f9a0b2c71",
            "event": "bounce",
            "email": "user@example.com",
            "message_id": "H-1-def",
            "lane_id": "",
            "tag": "",
            "timestamp": 1753502700,
            "metadata": {},
            "code": "550",
            "is_hard": True,
        }

    def test_top_level_fields_are_exposed(self):
        event = WebhookEvent.from_dict(self.click)
        assert event.id == "019844e3a1b27c3d8e4f5a6b7c8d9e0f"
        assert event.event_type == "click"
        assert event.lane_id == "5805dd85-ed8c-44db-91a7-1d53a41c86a5"
        assert event.tag == "newsletter"
        assert event.metadata == {"user_id": "user_123"}
        assert event.data == {
            "url": "https://example.com/product/123",
            "client_ip": "192.168.1.2",
        }

    def test_bounce_fields_are_exposed(self):
        event = WebhookEvent.from_dict(self.bounce)
        assert event.data["is_hard"] is True
        assert event.data["code"] == "550"

    def test_batch_payload_dispatches_every_event(self):
        clicks, bounces = Mock(), Mock()
        self.handler.on("click")(clicks)
        self.handler.register_handler("bounce", bounces)

        self.handler.process_webhook(json.dumps([self.click, self.bounce]))

        clicks.assert_called_once()
        bounces.assert_called_once()
        assert clicks.call_args[0][0].data["url"] == "https://example.com/product/123"

    def test_bytes_payload(self):
        handler_func = Mock()
        self.handler.register_handler("click", handler_func)
        self.handler.process_webhook(json.dumps(self.click).encode("utf-8"))
        handler_func.assert_called_once()

    def test_enum_member_registers_handler(self):
        handler_func = Mock()
        self.handler.on(WebhookEventType.CLICK)(handler_func)
        self.handler.process_webhook(self.click)
        handler_func.assert_called_once()

    def test_batch_with_invalid_event_raises(self):
        with pytest.raises(ValueError):
            self.handler.process_webhook([self.click, "not-an-event"])

    def test_deprecated_event_name_still_works_with_warning(self):
        handler_func = Mock()
        with pytest.warns(DeprecationWarning, match="'email.clicked' is deprecated"):
            self.handler.on("email.clicked")(handler_func)
        self.handler.process_webhook(self.click)
        handler_func.assert_called_once()


class TestWebhookVerifier:
    """Test cases for WebhookVerifier."""

    def test_verify_and_extract_signature(self):
        """HMAC verification accepts a sha256= prefix."""
        payload = '{"event":"delivery"}'
        signature = WebhookVerifier.generate_signature("secret", payload, True)
        assert WebhookVerifier.verify_signature("secret", payload, signature)
        assert (
            WebhookVerifier.extract_signature_from_headers(
                {"x-webhook-signature": signature}
            )
            == signature
        )

    def test_parse_single_and_batch_payload(self):
        """Single objects and arrays are both accepted."""
        event = {
            "event": "delivery",
            "email": "user@example.com",
            "lane_id": "11111111-1111-1111-1111-111111111111",
            "message_id": "msg_1",
            "timestamp": 1640995200,
        }
        single = WebhookVerifier.parse_webhook_payload(json.dumps(event))
        assert single["is_batch"] is False
        assert len(single["events"]) == 1

        batch = WebhookVerifier.parse_webhook_payload(json.dumps([event, event]))
        assert batch["is_batch"] is True
        assert len(batch["events"]) == 2

    def test_parse_keeps_unknown_event(self):
        """An unknown event type doesn't reject the rest of the batch."""
        known = {
            "event": "delivery",
            "email": "user@example.com",
            "lane_id": "11111111-1111-1111-1111-111111111111",
            "message_id": "msg_1",
            "timestamp": 1640995200,
        }
        unknown = {**known, "event": "a-future-event", "message_id": "msg_2"}
        batch = WebhookVerifier.parse_webhook_payload(json.dumps([known, unknown]))
        assert [e["event"] for e in batch["events"]] == ["delivery", "a-future-event"]

    def test_parse_rejects_empty_event_type(self):
        """A missing or empty event type is still rejected."""
        event = {
            "event": "",
            "email": "user@example.com",
            "lane_id": "11111111-1111-1111-1111-111111111111",
            "message_id": "msg_1",
            "timestamp": 1640995200,
        }
        with pytest.raises(ValueError, match="Invalid event type"):
            WebhookVerifier.parse_webhook_payload(json.dumps(event))

    def test_parse_accepts_request_event(self):
        """The request event type is valid."""
        event = {
            "event": "request",
            "email": "user@example.com",
            "lane_id": "11111111-1111-1111-1111-111111111111",
            "message_id": "msg_1",
            "timestamp": 1640995200,
        }
        parsed = WebhookVerifier.parse_webhook_payload(json.dumps(event))
        assert parsed["events"][0]["event"] == "request"
