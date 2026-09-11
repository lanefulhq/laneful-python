"""
Asynchronous Laneful API client implementation.

Requires: pip install laneful[async]
"""

import warnings

import asyncio
from typing import Any, Dict, Optional

try:
    import aiohttp
except ImportError:
    raise ImportError(
        "AsyncLanefulClient requires aiohttp. Install with: pip install laneful[async]"
    )

from .base import BaseLanefulClient
from .exceptions import LanefulError
from .models import Email, EmailList, EmailResponse, EmailResponseList, MailSettings
from .org_models import (
    CreateDomainRequest,
    Domain,
    ListDomainSpamRatioRadarParams,
    ListDomainSpamRatioRadarResponse,
    ListDomainsParams,
    ListDomainsResponse,
    ListGooglePostmasterSpamReportsParams,
    ListGooglePostmasterSpamReportsResponse,
    ListSndsReportsParams,
    ListSndsReportsResponse,
    ListUnsubscribeGroupsParams,
    ListUnsubscribeGroupsResponse,
    QueryItems,
    SuccessResponse,
    UnsubscribeGroup,
    UpdateDomainRequest,
)


class AsyncLanefulClient(BaseLanefulClient):
    """
    Asynchronous Laneful API client for sending emails and managing organization resources.

    Email sending uses a send host (https://your-endpoint.send.laneful.net).
    Domain, unsubscribe-group, and analytics endpoints use the organization
    API host (https://api.laneful.net).

    Example:
        async with AsyncLanefulClient("https://api.laneful.net", "your-token") as client:
            email = Email(
                from_address=Address(email="sender@example.com", name="Your Name"),
                to=[Address(email="recipient@example.com", name="Recipient Name")],
                subject="Hello from Laneful",
                text_content="This is a test email.",
                html_content="<h1>This is a test email.</h1>",
            )

            response = await client.send_email(email)
            print(f"Email sent successfully: {response.status}")
    """

    def __init__(
        self,
        base_url: str,
        auth_token: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ) -> None:
        """
        Initialize the asynchronous Laneful client.

        Args:
            base_url: The base URL for the Laneful API endpoint
            auth_token: Your authentication token
            timeout: Request timeout in seconds (default: 30.0)
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        super().__init__(base_url, auth_token, timeout, verify_ssl)

        # Create timeout object for aiohttp
        self.aiohttp_timeout = aiohttp.ClientTimeout(total=timeout)

        # Configure SSL context
        self.ssl_context = True if verify_ssl else False

        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            self._session = aiohttp.ClientSession(
                headers=self.headers, timeout=self.aiohttp_timeout, connector=connector
            )
        return self._session

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[QueryItems] = None,
    ) -> Dict[str, Any]:
        """
        Make an async HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request data to send as JSON
            params: Query string items (repeated keys supported)

        Returns:
            Response data as dictionary

        Raises:
            LanefulAuthError: If authentication fails
            LanefulAPIError: If the API returns an error
            LanefulError: For other client errors
        """
        url = self._build_url(endpoint)
        session = await self._get_session()

        try:
            async with session.request(
                method=method,
                url=url,
                json=data,
                params=params,
            ) as response:
                # Get response text
                response_text = await response.text()

                # Parse JSON response
                response_data = self._parse_json_response(response_text)

                # Process response and handle errors
                return self._process_response_data(response_data, response.status)

        except asyncio.TimeoutError:
            raise LanefulError("Request timed out")
        except aiohttp.ClientConnectorError:
            raise LanefulError("Failed to connect to Laneful API")
        except aiohttp.ClientError as e:
            raise LanefulError(f"Request failed: {str(e)}")

    async def send_email(  # type: ignore[override]
        self, email: Email, mail_settings: Optional[MailSettings] = None
    ) -> EmailResponse:
        """
        Send a single email asynchronously.

        Args:
            email: Email object to send
            mail_settings: Optional request-level mail settings

        Returns:
            EmailResponse with send status and message ID

        Raises:
            LanefulError: If sending fails
        """
        response_data = await self._make_request(
            "POST", "/email/send", self._build_send_payload([email], mail_settings)
        )
        return self._process_email_response(response_data)

    async def send_emails(  # type: ignore[override]
        self, emails: EmailList, mail_settings: Optional[MailSettings] = None
    ) -> EmailResponseList:
        """
        Send multiple emails asynchronously.

        Args:
            emails: List of Email objects to send
            mail_settings: Optional request-level mail settings

        Returns:
            List of EmailResponse objects

        Raises:
            LanefulError: If sending fails
        """
        self._validate_emails_list(emails)

        response_data = await self._make_request(
            "POST", "/email/send", self._build_send_payload(emails, mail_settings)
        )

        return self._process_emails_response(response_data, len(emails))

    async def get_email_status(self, message_id: str) -> Dict[str, Any]:  # type: ignore[override]
        """
        Get the status of a sent email asynchronously.

        Args:
            message_id: The message ID returned when sending the email

        Returns:
            Dictionary with email status information

        Raises:
            LanefulError: If the request fails
        """
        return await self._make_request("GET", f"/email/{message_id}/status")

    async def list_unsubscribe_groups(  # type: ignore[override]
        self, workspace_id: int, params: Optional[ListUnsubscribeGroupsParams] = None
    ) -> ListUnsubscribeGroupsResponse:
        """List unsubscribe groups for a workspace.

        Uses the organization API host (https://api.laneful.net).
        """
        query = params.to_query() if params else None
        return ListUnsubscribeGroupsResponse.from_dict(
            await self._make_request(
                "GET", f"/workspaces/{workspace_id}/unsubscribe-groups", params=query
            )
        )

    async def create_unsubscribe_group(  # type: ignore[override]
        self, workspace_id: int, name: str
    ) -> UnsubscribeGroup:
        """Create an unsubscribe group in a workspace.

        Uses the organization API host (https://api.laneful.net).
        """
        return self._parse_unsubscribe_group(
            await self._make_request(
                "POST",
                f"/workspaces/{workspace_id}/unsubscribe-groups",
                {"name": name},
            )
        )

    async def update_unsubscribe_group(  # type: ignore[override]
        self, workspace_id: int, unsubscribe_group_id: int, name: str
    ) -> UnsubscribeGroup:
        """Update an unsubscribe group.

        Uses the organization API host (https://api.laneful.net).
        """
        return self._parse_unsubscribe_group(
            await self._make_request(
                "PATCH",
                f"/workspaces/{workspace_id}/unsubscribe-groups/{unsubscribe_group_id}",
                {"name": name},
            )
        )

    async def list_domains(  # type: ignore[override]
        self, workspace_id: int, params: Optional[ListDomainsParams] = None
    ) -> ListDomainsResponse:
        """List sending domains for a workspace.

        Uses the organization API host (https://api.laneful.net).
        """
        query = params.to_query() if params else None
        return ListDomainsResponse.from_dict(
            await self._make_request(
                "GET", f"/workspaces/{workspace_id}/domains", params=query
            )
        )

    async def get_domain(  # type: ignore[override]
        self, workspace_id: int, domain: str
    ) -> Domain:
        """Get a single sending domain by name.

        Uses the organization API host (https://api.laneful.net).
        """
        encoded = self._encode_path(domain)
        return Domain.from_dict(
            await self._make_request(
                "GET", f"/workspaces/{workspace_id}/domains/{encoded}"
            )
        )

    async def create_domain(  # type: ignore[override]
        self, workspace_id: int, request: CreateDomainRequest
    ) -> Domain:
        """Create a sending domain in a workspace.

        Uses the organization API host (https://api.laneful.net).
        """
        return Domain.from_dict(
            await self._make_request(
                "POST", f"/workspaces/{workspace_id}/domains", request.to_dict()
            )
        )

    async def update_domain(  # type: ignore[override]
        self, workspace_id: int, domain: str, request: UpdateDomainRequest
    ) -> Domain:
        """Update a domain's mutable settings (currently the email track).

        Uses the organization API host (https://api.laneful.net).
        """
        encoded = self._encode_path(domain)
        return Domain.from_dict(
            await self._make_request(
                "PATCH",
                f"/workspaces/{workspace_id}/domains/{encoded}",
                request.to_dict(),
            )
        )

    async def verify_domain(  # type: ignore[override]
        self, workspace_id: int, domain: str
    ) -> Domain:
        """Trigger DNS verification for a domain.

        Uses the organization API host (https://api.laneful.net).
        """
        encoded = self._encode_path(domain)
        return Domain.from_dict(
            await self._make_request(
                "POST", f"/workspaces/{workspace_id}/domains/{encoded}/verify"
            )
        )

    async def delete_domain(  # type: ignore[override]
        self, workspace_id: int, domain: str
    ) -> SuccessResponse:
        """Delete a sending domain from a workspace.

        Uses the organization API host (https://api.laneful.net).
        """
        encoded = self._encode_path(domain)
        return SuccessResponse.from_dict(
            await self._make_request(
                "DELETE", f"/workspaces/{workspace_id}/domains/{encoded}"
            )
        )

    async def list_domain_spam_ratio_radar(  # type: ignore[override]
        self, params: Optional[ListDomainSpamRatioRadarParams] = None
    ) -> ListDomainSpamRatioRadarResponse:
        """List domains whose spam complaint ratio reached a critical level.

        Uses the organization API host (https://api.laneful.net).
        """
        query = params.to_query() if params else None
        return ListDomainSpamRatioRadarResponse.from_dict(
            await self._make_request(
                "GET", "/analytics/radar/domain-spam-ratio", params=query
            )
        )

    async def list_google_postmaster_spam_reports(  # type: ignore[override]
        self, params: Optional[ListGooglePostmasterSpamReportsParams] = None
    ) -> ListGooglePostmasterSpamReportsResponse:
        """List daily Google Postmaster Tools spam-rate reports.

        Uses the organization API host (https://api.laneful.net).
        """
        query = params.to_query() if params else None
        return ListGooglePostmasterSpamReportsResponse.from_dict(
            await self._make_request(
                "GET", "/analytics/google-postmaster/spam-reports", params=query
            )
        )

    async def list_snds_reports(  # type: ignore[override]
        self, params: Optional[ListSndsReportsParams] = None
    ) -> ListSndsReportsResponse:
        """List daily Microsoft SNDS reports for the organization's sending IPs.

        Uses the organization API host (https://api.laneful.net).
        """
        query = params.to_query() if params else None
        return ListSndsReportsResponse.from_dict(
            await self._make_request(
                "GET", "/analytics/microsoft-snds/reports", params=query
            )
        )

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "AsyncLanefulClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
        return None

    def __del__(self) -> None:
        """Cleanup when object is garbage collected."""
        if self._session and not self._session.closed:
            # Don't await in __del__, just warn
            warnings.warn(
                "AsyncLanefulClient session was not closed properly. "
                "Use 'async with client:' or call 'await client.close()' explicitly.",
                ResourceWarning,
                stacklevel=2,
            )
