#!/usr/bin/env python3
"""Create, update, and list unsubscribe groups."""

import os
import sys

from laneful import LanefulClient, ListUnsubscribeGroupsParams


def main() -> None:
    base_url = (
        os.environ.get("LANEFUL_ORG_BASE_URL")
        or os.environ.get("LANEFUL_BASE_URL")
        or "https://api.laneful.net"
    )
    auth_token = os.environ.get("LANEFUL_AUTH_TOKEN")
    workspace_id = int(os.environ.get("LANEFUL_WORKSPACE_ID", "1"))

    if not auth_token:
        print("Missing LANEFUL_AUTH_TOKEN")
        sys.exit(1)

    client = LanefulClient(base_url, auth_token)
    created = client.create_unsubscribe_group(workspace_id, "Newsletters")
    print(f"Created group {created.unsubscribe_group_id}: {created.name}")

    updated = client.update_unsubscribe_group(
        workspace_id, created.unsubscribe_group_id, "Weekly Newsletters"
    )
    print(f"Updated name: {updated.name}")

    listing = client.list_unsubscribe_groups(
        workspace_id, ListUnsubscribeGroupsParams(limit=50)
    )
    for group in listing.unsubscribe_groups:
        print(f"- {group.unsubscribe_group_id} {group.name}")


if __name__ == "__main__":
    main()
