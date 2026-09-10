#!/usr/bin/env python3
"""List deliverability analytics from the organization API."""

import os
import sys
from datetime import date, timedelta

from laneful import (
    LanefulClient,
    ListDomainSpamRatioRadarParams,
    ListGooglePostmasterSpamReportsParams,
    ListSndsReportsParams,
)


def main() -> None:
    base_url = (
        os.environ.get("LANEFUL_ORG_BASE_URL")
        or os.environ.get("LANEFUL_BASE_URL")
        or "https://api.laneful.net"
    )
    auth_token = os.environ.get("LANEFUL_AUTH_TOKEN")

    if not auth_token:
        print("Missing LANEFUL_AUTH_TOKEN")
        sys.exit(1)

    client = LanefulClient(base_url, auth_token)
    today = date.today()
    radar = client.list_domain_spam_ratio_radar(
        ListDomainSpamRatioRadarParams(
            start_date=(today - timedelta(days=7)).isoformat(),
            end_date=today.isoformat(),
        )
    )
    for entry in radar.radar:
        print(f"{entry.date} {entry.domain} @{entry.esp}: {entry.spam_ratio}%")

    postmaster = client.list_google_postmaster_spam_reports(
        ListGooglePostmasterSpamReportsParams(domain="example.com")
    )
    for report in postmaster.spam_reports:
        print(f"{report.date} {report.domain}: {report.spam_ratio}%")

    snds = client.list_snds_reports(ListSndsReportsParams())
    for report in snds.snds_reports:
        print(
            f"{report.date} {report.ip}: filter={report.filter_result} "
            f"complaint={report.complaint_rate}%"
        )


if __name__ == "__main__":
    main()
