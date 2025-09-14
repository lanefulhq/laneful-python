"""
Webhook handling for Laneful API events.
"""

import hmac
import hashlib


def verify_webhook_signature(secret: str, payload: str, signature: str) -> bool:
    """Verify the signature of a webhook payload"""
    # Create HMAC with SHA256
    mac = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256)

    # Get the expected signature as hex string
    expected = mac.hexdigest()

    # Compare signatures using constant-time comparison
    return hmac.compare_digest(signature, expected)
