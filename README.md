# Laneful Python Client

A Python client library for the [Laneful API](https://app.laneful.com/docs/sending-email), providing easy email sending capabilities with support for templates, attachments, tracking, and webhooks. 

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Installation

The library supports flexible installation options:

```bash
# Default installation (sync client only)
pip install laneful

# Add async support to existing sync installation
pip install laneful[async] 

# Async-only (no sync dependencies)
pip install laneful[async-only]

# Explicit sync support (same as default)
pip install laneful[sync]

# Full support (both sync and async)
pip install laneful[all]
```

## Quick Start

### Synchronous Usage

```bash
pip install laneful  # Default installation
```

```python
from laneful import LanefulClient, Email, Address

# Initialize the sync client
client = LanefulClient(
    base_url="https://custom-endpoint.send.laneful.net",
    auth_token="your-auth-token"
)

# Create an email
email = Email(
    from_address=Address(email="sender@example.com", name="Your Name"),
    to=[Address(email="recipient@example.com", name="Recipient Name")],
    subject="Hello from Laneful",
    text_content="This is a test email.",
    html_content="<h1>This is a test email.</h1>",
)

# Send the email
response = client.send_email(email)
print(f"Email sent successfully: {response.status}")
```

### Asynchronous Usage

```bash
pip install laneful[async]  # Add async to sync
# OR
pip install laneful[async-only]  # Pure async, no sync deps
```

```python
import asyncio
from laneful import AsyncLanefulClient, Email, Address

async def send_email_async():
    # Initialize the async client
    async with AsyncLanefulClient(
        base_url="https://custom-endpoint.send.laneful.net",
        auth_token="your-auth-token"
    ) as client:
        # Create an email
        email = Email(
            from_address=Address(email="sender@example.com", name="Your Name"),
            to=[Address(email="recipient@example.com", name="Recipient Name")],
            subject="Hello from Laneful (Async)",
            text_content="This is an async test email.",
            html_content="<h1>This is an async test email.</h1>",
        )
        
        # Send the email
        response = await client.send_email(email)
        print(f"Email sent successfully: {response.status}")

# Run the async function
asyncio.run(send_email_async())
```

## Features

- ✅ Send single or multiple emails
- ✅ Support for plain text and HTML content  
- ✅ Email templates with dynamic data
- ✅ File attachments
- ✅ Email tracking (opens, clicks, unsubscribes)
- ✅ Visible `from_header` and request-level `mail_settings`
- ✅ Custom headers
- ✅ Scheduled sending
- ✅ Webhook handling and signature verification
- ✅ Domain management (list, create, verify, update email track, delete)
- ✅ Unsubscribe groups
- ✅ Deliverability analytics (spam-ratio radar, Google Postmaster, Microsoft SNDS)
- ✅ Reply-to addresses
- ✅ Context manager support
- ✅ Type hints and mypy support
- ✅ Comprehensive error handling

## API Reference

### Creating Clients

#### Synchronous Client

```python
from laneful import LanefulClient

client = LanefulClient(
    base_url="https://custom-endpoint.laneful.net",
    auth_token="your-auth-token",
    timeout=30.0,  # Optional: request timeout in seconds
    verify_ssl=True  # Optional: SSL verification
)
```

#### Asynchronous Client

```python
from laneful import AsyncLanefulClient

# Method 1: Using async context manager (recommended)
async with AsyncLanefulClient(
    base_url="https://custom-endpoint.laneful.net",
    auth_token="your-auth-token",
    timeout=30.0,  # Optional: request timeout in seconds
    verify_ssl=True  # Optional: SSL verification
) as client:
    # Use client here
    pass

# Method 2: Manual session management
client = AsyncLanefulClient(base_url, auth_token)
try:
    # Use client here
    pass
finally:
    await client.close()
```

#### Email

```python
from laneful import Email, Address, Attachment, TrackingSettings

email = Email(
    from_address=Address(email="sender@example.com", name="Sender"),
    to=[Address(email="recipient@example.com", name="Recipient")],
    subject="Email Subject",
    text_content="Plain text content",  # Optional
    html_content="<h1>HTML content</h1>",  # Optional
    cc=[Address(email="cc@example.com")],  # Optional
    bcc=[Address(email="bcc@example.com")],  # Optional
    reply_to=Address(email="reply@example.com"),  # Optional
    attachments=[],  # Optional: List of Attachment objects
    headers={"X-Custom": "value"},  # Optional
    template_id="template-123",  # Optional: for template emails
    template_data={"name": "John"},  # Optional: template variables
    send_time=1640995200,  # Optional: Unix timestamp for scheduling
    tracking=TrackingSettings(opens=True, clicks=True),  # Optional
    webhook_data={"user_id": "123"},  # Optional: custom webhook data
    from_header=Address(email="newsletter@example.com", name="Newsletter"),  # Optional
)
```

### Sending Emails

#### Single Email (Sync)

```python
from laneful import MailSettings

response = client.send_email(
    email,
    MailSettings(sandbox_mode=True, return_message_ids=True),
)
print(f"Status: {response.status}")
print(f"Message ID: {response.message_id}")
print(f"Message IDs: {response.message_ids}")
```

#### Single Email (Async)

```python
response = await client.send_email(email)
print(f"Status: {response.status}")
print(f"Message ID: {response.message_id}")
```

#### Multiple Emails (Sync)

```python
emails = [email1, email2, email3]
responses = client.send_emails(emails)

for i, response in enumerate(responses):
    print(f"Email {i+1} status: {response.status}")
```

#### Multiple Emails (Async)

```python
emails = [email1, email2, email3]
responses = await client.send_emails(emails)

for i, response in enumerate(responses):
    print(f"Email {i+1} status: {response.status}")
```

### Bulk Email Sending

For sending multiple emails at once, use the `send_emails` method:

```python
from laneful import LanefulClient, Email, Address

client = LanefulClient("https://custom-endpoint.send.laneful.net", "your-auth-token")

emails = [
    Email(from_address=Address(email="sender@example.com"), 
          to=[Address(email="user1@example.com")], subject="Hello User 1"),
    Email(from_address=Address(email="sender@example.com"), 
          to=[Address(email="user2@example.com")], subject="Hello User 2"),
]

responses = client.send_emails(emails)
```

#### Concurrent Email Sending (Async Only)

```python
import asyncio

async with AsyncLanefulClient(base_url, auth_token) as client:
    # Send multiple emails concurrently
    tasks = [client.send_email(email) for email in emails]
    responses = await asyncio.gather(*tasks)
    
    print(f"Sent {len(responses)} emails concurrently!")
```

#### Context Managers

```python
# Sync context manager
with LanefulClient(base_url, auth_token) as client:
    response = client.send_email(email)
    print(f"Email sent: {response.status}")
# Client session automatically closed

# Async context manager  
async with AsyncLanefulClient(base_url, auth_token) as client:
    response = await client.send_email(email)
    print(f"Email sent: {response.status}")
# Client session automatically closed
```

## Examples

### Template Email

```python
from laneful import Email, Address, LanefulClient

client = LanefulClient("https://custom-endpoint.send.laneful.net", "your-auth-token")

email = Email(
    from_address=Address(email="sender@example.com"),
    to=[Address(email="user@example.com")],
    subject="Welcome!",
    template_id="11",
    template_data={
        "name": "John Doe",
        "company": "Acme Corp",
        "activation_link": "https://example.com/activate?token=abc123"
    },
)

response = client.send_email(email)
```

### Email with Attachments

```python
import base64
from laneful import Attachment, Email, Address, LanefulClient

client = LanefulClient("https://custom-endpoint.send.laneful.net", "your-auth-token")

# Prepare attachment (base64 encoded content)
with open("document.pdf", "rb") as f:
    content = base64.b64encode(f.read()).decode()

email = Email(
    from_address=Address(email="sender@example.com"),
    to=[Address(email="user@example.com")],
    subject="Document Attached",
    text_content="Please find the document attached.",
    attachments=[
        Attachment(
            file_name="document.pdf",
            content=content,
            content_type="application/pdf",
            inline_id="123",
        )
    ],
)

response = client.send_email(email)
```

### Scheduled Email

```python
import time

from laneful import Email, Address, LanefulClient

client = LanefulClient("https://custom-endpoint.send.laneful.net", "your-auth-token")

# Schedule email to be sent 1 hour from now
send_time = int(time.time()) + 3600

email = Email(
    from_address=Address(email="sender@example.com"),
    to=[Address(email="user@example.com")],
    subject="Scheduled Email",
    text_content="This email was scheduled.",
    send_time=send_time,
)

response = client.send_email(email)
```

### Email with Tracking

```python
from laneful import TrackingSettings, Address, LanefulClient, Email

client = LanefulClient("https://custom-endpoint.send.laneful.net", "your-auth-token")

email = Email(
    from_address=Address(email="sender@example.com"),
    to=[Address(email="user@example.com")],
    subject="Tracked Email",
    html_content='<h1>Tracked Email</h1><a href="https://example.com">Click me</a>',
    tracking=TrackingSettings(
        opens=True,
        clicks=True,
        unsubscribes=True,
        unsubscribe_group_id=123,
        # ignored if unsubscribe_group_id is set
        unsubscribe_group_name="Newsletters",
    ),
)

# Sync
response = client.send_email(email)
```

### AsyncIO support

```python
import asyncio
from laneful import AsyncLanefulClient
  
async def send_emails_async(emails):
    async with AsyncLanefulClient("https://custom-endpoint.send.laneful.net", "your-auth-token") as client:
        tasks = [client.send_email(email) for email in emails]
        return await asyncio.gather(*tasks)

```

## Domain, unsubscribe groups, and analytics

These endpoints live on the organization API host. Point the client at it:

```python
client = LanefulClient(
    base_url="https://api.laneful.net",
    auth_token="your-auth-token",
)
```

Development uses `https://api.dev.laneful.net`.

### Unsubscribe groups

```python
from laneful import ListUnsubscribeGroupsParams

groups = client.list_unsubscribe_groups(42, ListUnsubscribeGroupsParams(limit=50))
created = client.create_unsubscribe_group(42, "Newsletters")
updated = client.update_unsubscribe_group(42, created.unsubscribe_group_id, "Weekly Newsletters")
```

### Domains

```python
from laneful import CreateDomainRequest, ListDomainsParams, UpdateDomainRequest

listing = client.list_domains(42, ListDomainsParams(limit=50))
domain = client.create_domain(
    42,
    CreateDomainRequest(domain="mydomain.com", tracking="tracking", return_path="return-path"),
)
domain = client.get_domain(42, "mydomain.com")
domain = client.verify_domain(42, "mydomain.com")

# Set the email track; pass "" to clear it, or omit email_track_id to leave it unchanged
domain = client.update_domain(
    42,
    "mydomain.com",
    UpdateDomainRequest(email_track_id="e59f0a35-05bc-4516-b585-c06f69c3e67e"),
)

client.delete_domain(42, "mydomain.com")
```

### Deliverability analytics

```python
from laneful import (
    ListDomainSpamRatioRadarParams,
    ListGooglePostmasterSpamReportsParams,
    ListSndsReportsParams,
)

radar = client.list_domain_spam_ratio_radar(
    ListDomainSpamRatioRadarParams(
        workspace_ids=[1, 2],
        domain="example.com",
        start_date="2026-09-01",
        end_date="2026-09-08",
    )
)

postmaster = client.list_google_postmaster_spam_reports(
    ListGooglePostmasterSpamReportsParams(domain="example.com")
)

snds = client.list_snds_reports(ListSndsReportsParams(ip="203.0.113.5"))
```

## Webhook Handling

The library provides comprehensive webhook handling for email events:

```python
from laneful.webhooks import WebhookHandler, WebhookEvent

webhook_payload = dict()

# Initialize webhook handler
handler = WebhookHandler(webhook_secret="your-webhook-secret")

# Register event handlers
@handler.on("email.delivered")
def handle_delivered(event: WebhookEvent):
    print(f"Email {event.message_id} delivered to {event.email}")

@handler.on("email.opened")  
def handle_opened(event: WebhookEvent):
    print(f"Email {event.message_id} opened by {event.email}")

@handler.on("email.clicked")
def handle_clicked(event: WebhookEvent):
    url = event.data.get("url")
    print(f"Link clicked: {url}")

# Process webhook payload
handler.process_webhook(webhook_payload)
```

## Error Handling

The library provides specific exception types:

```python
from laneful.exceptions import LanefulError, LanefulAPIError, LanefulAuthError

try:
    response = client.send_email(email)
except LanefulAuthError:
    print("Authentication failed - check your token")
except LanefulAPIError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
except LanefulError as e:
    print(f"Client error: {e.message}")
```

## Development
### Running Tests

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=laneful

# Run type checking
mypy laneful/

# Run linting
ruff check laneful/
black --check laneful/
```

### Code Formatting

```bash
# Format code
black laneful/ tests/
isort laneful/ tests/

# Check formatting
ruff check laneful/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- 📖 [Documentation](https://github.com/lanefulhq/laneful-python#readme)
- 🐛 [Bug Reports](https://github.com/lanefulhq/laneful-python/issues)
