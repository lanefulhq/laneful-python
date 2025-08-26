"""
Webhook handling for Laneful API events.
"""

import json
import hmac
import hashlib
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum


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
            event_type=data.get("event_type", ""),
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
            self.webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)
    
    def on(self, event_type: str) -> Callable[[Callable[[WebhookEvent], None]], Callable[[WebhookEvent], None]]:
        """
        Decorator to register event handlers.
        
        Args:
            event_type: The event type to handle (e.g., "email.delivered")
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable[[WebhookEvent], None]) -> Callable[[WebhookEvent], None]:
            self._handlers[event_type] = func
            return func
        return decorator
    
    def register_handler(self, event_type: str, handler: Callable[[WebhookEvent], None]) -> None:
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


# Flask integration helper
def create_flask_webhook_handler(
    handler: WebhookHandler,
    signature_header: str = "X-Laneful-Signature"
) -> Callable[[], Any]:
    """
    Create a Flask route handler for webhooks.
    
    Args:
        handler: Configured WebhookHandler instance
        signature_header: Name of the signature header
        
    Returns:
        Flask route handler function
        
    Example:
        from flask import Flask, request
        
        app = Flask(__name__)
        webhook_handler = WebhookHandler("your-secret")
        
        @app.route("/webhooks/laneful", methods=["POST"])
        def handle_webhook():
            return create_flask_webhook_handler(webhook_handler)()
    """
    def flask_handler() -> Any:
        try:
            from flask import request, jsonify
        except ImportError:
            raise ImportError("Flask is required for Flask webhook integration")
        
        # Verify signature if provided
        signature = request.headers.get(signature_header)
        if signature and not handler.verify_signature(request.data, signature):
            return jsonify({"error": "Invalid signature"}), 401
        
        try:
            handler.process_webhook(request.get_json())
            return jsonify({"status": "success"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    return flask_handler


# FastAPI integration helper
def create_fastapi_webhook_handler(
    handler: WebhookHandler,
    signature_header: str = "x-laneful-signature"
) -> Callable[[Dict[str, Any], Optional[str]], Dict[str, str]]:
    """
    Create a FastAPI route handler for webhooks.
    
    Args:
        handler: Configured WebhookHandler instance
        signature_header: Name of the signature header
        
    Returns:
        FastAPI route handler function
        
    Example:
        from fastapi import FastAPI, Header, HTTPException
        
        app = FastAPI()
        webhook_handler = WebhookHandler("your-secret")
        
        @app.post("/webhooks/laneful")
        async def handle_webhook(
            payload: dict,
            x_laneful_signature: str = Header(None)
        ):
            return create_fastapi_webhook_handler(webhook_handler)(payload, x_laneful_signature)
    """
    def fastapi_handler(payload: Dict[str, Any], signature: Optional[str] = None) -> Dict[str, str]:
        try:
            from fastapi import HTTPException
        except ImportError:
            raise ImportError("FastAPI is required for FastAPI webhook integration")
        
        # Verify signature if provided
        if signature and not handler.verify_signature(json.dumps(payload), signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        try:
            handler.process_webhook(payload)
            return {"status": "success"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return fastapi_handler
