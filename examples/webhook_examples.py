"""
Webhook handling examples for the Laneful Python client.
"""

from laneful.webhooks import WebhookHandler, WebhookEvent, create_flask_webhook_handler


def basic_webhook_example():
    """Basic webhook handler setup."""
    handler = WebhookHandler(webhook_secret="your-webhook-secret")
    
    @handler.on("email.delivered")
    def handle_delivered(event: WebhookEvent):
        print(f"Email {event.message_id} was delivered to {event.email}")
        print(f"Delivery timestamp: {event.timestamp}")
    
    @handler.on("email.opened")
    def handle_opened(event: WebhookEvent):
        print(f"Email {event.message_id} was opened by {event.email}")
        # Access additional data
        user_agent = event.data.get("user_agent", "Unknown")
        print(f"User agent: {user_agent}")
    
    @handler.on("email.clicked")
    def handle_clicked(event: WebhookEvent):
        print(f"Link clicked in email {event.message_id}")
        clicked_url = event.data.get("url", "Unknown URL")
        print(f"Clicked URL: {clicked_url}")
    
    @handler.on("email.bounced")
    def handle_bounced(event: WebhookEvent):
        print(f"Email {event.message_id} bounced for {event.email}")
        bounce_reason = event.data.get("reason", "Unknown reason")
        print(f"Bounce reason: {bounce_reason}")
    
    # Example webhook payload processing
    sample_payload = {
        "event_type": "email.delivered",
        "message_id": "msg_123456",
        "email": "user@example.com",
        "timestamp": 1640995200,
        "data": {}
    }
    
    handler.process_webhook(sample_payload)


def flask_webhook_example():
    """Flask integration example."""
    try:
        from flask import Flask, request
        
        app = Flask(__name__)
        webhook_handler = WebhookHandler("your-webhook-secret")
        
        @webhook_handler.on("email.delivered")
        def handle_delivered(event: WebhookEvent):
            print(f"Flask: Email delivered to {event.email}")
        
        @app.route("/webhooks/laneful", methods=["POST"])
        def handle_webhook():
            return create_flask_webhook_handler(webhook_handler)()
        
        print("Flask webhook handler registered at /webhooks/laneful")
        print("Start the Flask app with: app.run()")
        
    except ImportError:
        print("Flask not installed. Install with: pip install flask")


def fastapi_webhook_example():
    """FastAPI integration example."""
    try:
        from fastapi import FastAPI, Header, HTTPException
        from laneful.webhooks import create_fastapi_webhook_handler
        from typing import Optional
        
        app = FastAPI()
        webhook_handler = WebhookHandler("your-webhook-secret")
        
        @webhook_handler.on("email.delivered")
        def handle_delivered(event: WebhookEvent):
            print(f"FastAPI: Email delivered to {event.email}")
        
        fastapi_handler = create_fastapi_webhook_handler(webhook_handler)
        
        @app.post("/webhooks/laneful")
        async def handle_webhook(
            payload: dict,
            x_laneful_signature: Optional[str] = Header(None)
        ):
            return fastapi_handler(payload, x_laneful_signature)
        
        print("FastAPI webhook handler registered at /webhooks/laneful")
        print("Start the FastAPI app with: uvicorn main:app --reload")
        
    except ImportError:
        print("FastAPI not installed. Install with: pip install fastapi uvicorn")


def manual_webhook_processing():
    """Manual webhook processing without web framework."""
    handler = WebhookHandler(webhook_secret="your-webhook-secret")
    
    # Track email metrics
    email_stats = {
        "sent": 0,
        "delivered": 0,
        "opened": 0,
        "clicked": 0,
        "bounced": 0
    }
    
    @handler.on("email.sent")
    def track_sent(event: WebhookEvent):
        email_stats["sent"] += 1
        print(f"Stats update - Sent: {email_stats['sent']}")
    
    @handler.on("email.delivered")
    def track_delivered(event: WebhookEvent):
        email_stats["delivered"] += 1
        print(f"Stats update - Delivered: {email_stats['delivered']}")
    
    @handler.on("email.opened")
    def track_opened(event: WebhookEvent):
        email_stats["opened"] += 1
        print(f"Stats update - Opened: {email_stats['opened']}")
    
    @handler.on("email.clicked")
    def track_clicked(event: WebhookEvent):
        email_stats["clicked"] += 1
        print(f"Stats update - Clicked: {email_stats['clicked']}")
    
    @handler.on("email.bounced")
    def track_bounced(event: WebhookEvent):
        email_stats["bounced"] += 1
        print(f"Stats update - Bounced: {email_stats['bounced']}")
    
    # Simulate processing multiple webhook events
    sample_events = [
        {"event_type": "email.sent", "message_id": "msg_1", "email": "user1@example.com", "timestamp": 1640995200, "data": {}},
        {"event_type": "email.delivered", "message_id": "msg_1", "email": "user1@example.com", "timestamp": 1640995260, "data": {}},
        {"event_type": "email.opened", "message_id": "msg_1", "email": "user1@example.com", "timestamp": 1640995320, "data": {"user_agent": "Mozilla/5.0"}},
        {"event_type": "email.clicked", "message_id": "msg_1", "email": "user1@example.com", "timestamp": 1640995380, "data": {"url": "https://example.com"}},
    ]
    
    for event_data in sample_events:
        handler.process_webhook(event_data)
    
    print("\nFinal email statistics:")
    for metric, count in email_stats.items():
        print(f"  {metric.capitalize()}: {count}")


def signature_verification_example():
    """Example of webhook signature verification."""
    import json
    import hmac
    import hashlib
    
    webhook_secret = "your-webhook-secret"
    handler = WebhookHandler(webhook_secret)
    
    # Simulate a webhook payload
    payload = {
        "event_type": "email.delivered",
        "message_id": "msg_123456",
        "email": "user@example.com",
        "timestamp": 1640995200,
        "data": {}
    }
    
    # Create a signature (this would normally be done by Laneful)
    payload_str = json.dumps(payload, separators=(',', ':'))
    signature = hmac.new(
        webhook_secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Verify the signature
    is_valid = handler.verify_signature(payload_str, f"sha256={signature}")
    print(f"Signature verification: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    # Test with invalid signature
    is_valid_bad = handler.verify_signature(payload_str, "sha256=invalid_signature")
    print(f"Bad signature verification: {'✓ Valid' if is_valid_bad else '✗ Invalid'}")


if __name__ == "__main__":
    print("Laneful Webhook Examples")
    print("========================")
    
    print("\n1. Basic webhook handling:")
    basic_webhook_example()
    
    print("\n2. Manual webhook processing with stats:")
    manual_webhook_processing()
    
    print("\n3. Signature verification:")
    signature_verification_example()
    
    print("\n4. Web framework integration:")
    flask_webhook_example()
    fastapi_webhook_example()
