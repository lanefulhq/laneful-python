#!/usr/bin/env python3
"""Send a sandbox email with mail settings and a visible From header."""

import os
import sys

from laneful import Address, Email, LanefulClient, MailSettings, TrackingSettings


def main() -> None:
    base_url = os.environ.get("LANEFUL_BASE_URL")
    auth_token = os.environ.get("LANEFUL_AUTH_TOKEN")
    from_email = os.environ.get("LANEFUL_FROM_EMAIL")
    to_emails = os.environ.get("LANEFUL_TO_EMAILS")

    if not all([base_url, auth_token, from_email, to_emails]):
        print(
            "Missing LANEFUL_BASE_URL, LANEFUL_AUTH_TOKEN, "
            "LANEFUL_FROM_EMAIL, LANEFUL_TO_EMAILS"
        )
        sys.exit(1)

    to_email = to_emails.split(",")[0].strip()
    client = LanefulClient(base_url, auth_token)
    email = Email(
        from_address=Address(email=from_email, name="Your Name"),
        to=[Address(email=to_email, name="Recipient Name")],
        subject="Sandbox email",
        text_content="This email is sent with sandbox mode and returns message IDs.",
        from_header=Address(email=from_email, name="Newsletter"),
        tracking=TrackingSettings(
            opens=True,
            clicks=True,
            unsubscribes=False,
            unsubscribe_group_name="Newsletters",
        ),
    )

    response = client.send_email(
        email,
        MailSettings(sandbox_mode=True, return_message_ids=True),
    )
    print(f"Status: {response.status}")
    print(f"Message IDs: {response.message_ids}")


if __name__ == "__main__":
    main()
