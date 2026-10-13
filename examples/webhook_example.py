#!/usr/bin/env python3
"""Receive Laneful webhooks: verify the signature, then process single or batch events."""

import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from laneful import WebhookEvent, WebhookEventType, WebhookHandler

webhook_secret = os.environ.get("LANEFUL_WEBHOOK_SECRET")
port = int(os.environ.get("PORT", "8000"))

if not webhook_secret:
    # Without a secret, verify_signature accepts every payload.
    print("Missing LANEFUL_WEBHOOK_SECRET")
    sys.exit(1)

handler = WebhookHandler(webhook_secret=webhook_secret)


def log_event(event: WebhookEvent) -> None:
    print(
        f"[{event.event_type}] id={event.id} message_id={event.message_id} "
        f"email={event.email} tag={event.tag!r} metadata={event.metadata} "
        f"data={event.data}"
    )


# Register a handler for every event type Laneful sends.
for event_type in WebhookEventType:
    handler.register_handler(event_type, log_event)


class WebhookRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        # Verify the raw body: re-serializing parsed JSON can change the bytes.
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        signature = self.headers.get("x-webhook-signature")

        if not signature or not handler.verify_signature(body, signature):
            self.respond(401, "Invalid signature")
            return

        try:
            handler.process_webhook(body)
        except Exception as e:
            print(f"Webhook processing failed: {e}")
            self.respond(500, "Error")
            return

        self.respond(200, "OK")

    def respond(self, status: int, message: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))


if __name__ == "__main__":
    print(f"Webhook example listening on http://localhost:{port}/")
    HTTPServer(("", port), WebhookRequestHandler).serve_forever()
