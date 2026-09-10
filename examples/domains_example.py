#!/usr/bin/env python3
"""List and manage sending domains on the organization API."""

import os
import sys

from laneful import (
    CreateDomainRequest,
    LanefulClient,
    ListDomainsParams,
    UpdateDomainRequest,
)


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
    listing = client.list_domains(workspace_id, ListDomainsParams(limit=50))
    print(f"Domains: {len(listing.domains)}")

    domain = client.create_domain(
        workspace_id,
        CreateDomainRequest(
            domain="mydomain.com",
            tracking="tracking",
            return_path="return-path",
        ),
    )
    print(f"Created {domain.domain}, verified={domain.verified}")

    domain = client.verify_domain(workspace_id, "mydomain.com")
    print(f"Verification: dmarc={domain.dmarc_verified}")

    domain = client.update_domain(
        workspace_id,
        "mydomain.com",
        UpdateDomainRequest("e59f0a35-05bc-4516-b585-c06f69c3e67e"),
    )
    print(f"Email track: {domain.email_track_id}")


if __name__ == "__main__":
    main()
