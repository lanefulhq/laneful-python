"""
Synchronous Laneful API client implementation.

Requires: pip install laneful (included by default)
"""

from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    raise ImportError(
        "LanefulClient requires requests. "
        "Install with: pip install laneful[sync] or pip install laneful"
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


class LanefulClient(BaseLanefulClient):
    """
    Laneful API client for sending emails and managing organization resources.

    Email sending uses a send host (https://your-endpoint.send.laneful.net).
    Domain, unsubscribe-group, and analytics endpoints use the organization
    API host (https://api.laneful.net).

    Example:
        client = LanefulClient("https://custom-endpoint.send.laneful.net", "your-auth-token")

        email = Email(
            from_address=Address(email="sender@example.com", name="Your Name"),
            to=[Address(email="recipient@example.com", name="Recipient Name")],
            subject="Hello from Laneful",
            text_content="This is a test email.",
            html_content="<h1>This is a test email.</h1>",
        )

        response = client.send_email(email)
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
        Initialize the synchronous Laneful client.

        Args:
            base_url: The base URL for the Laneful API endpoint
            auth_token: Your authentication token
            timeout: Request timeout in seconds (default: 30.0)
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        super().__init__(base_url, auth_token, timeout, verify_ssl)

        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[QueryItems] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.

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

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers=self.headers,
            )

            # Parse JSON response
            response_data = self._parse_json_response(response.text)

            # Process response and handle errors
            return self._process_response_data(response_data, response.status_code)

        except requests.exceptions.Timeout:
            raise LanefulError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise LanefulError("Failed to connect to Laneful API")
        except requests.exceptions.RequestException as e:
            raise LanefulError(f"Request failed: {str(e)}")

    def send_email(
        self, email: Email, mail_settings: Optional[MailSettings] = None
    ) -> EmailResponse:
        """
        Send a single email.

        Args:
            email: Email object to send
            mail_settings: Optional request-level mail settings

        Returns:
            EmailResponse with send status and message ID

        Raises:
            LanefulError: If sending fails
        """
        response_data = self._make_request(
            "POST", "/email/send", self._build_send_payload([email], mail_settings)
        )
        return self._process_email_response(response_data)

    def send_emails(
        self, emails: EmailList, mail_settings: Optional[MailSettings] = None
    ) -> EmailResponseList:
        """
        Send multiple emails.

        Args:
            emails: List of Email objects to send
            mail_settings: Optional request-level mail settings

        Returns:
            List of EmailResponse objects

        Raises:
            LanefulError: If sending fails
        """
        self._validate_emails_list(emails)

        response_data = self._make_request(
            "POST", "/email/send", self._build_send_payload(emails, mail_settings)
        )

        return self._process_emails_response(response_data, len(emails))

    def get_email_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get the status of a sent email.

        Args:
            message_id: The message ID returned when sending the email

        Returns:
            Dictionary with email status information

        Raises:
            LanefulError: If the request fails
        """
        return self._make_request("GET", f"/email/{message_id}/status")

    def list_unsubscribe_groups(
        self, workspace_id: int, params: Optional[ListUnsubscribeGroupsParams] = None
    ) -> ListUnsubscribeGroupsResponse:
        """List unsubscribe groups for a workspace.

        Uses the organization API host (https://api.laneful.net).
        """
        query = params.to_query() if params else None
        return ListUnsubscribeGroupsResponse.from_dict(
            self._make_request(
                "GET", f"/workspaces/{workspace_id}/unsubscribe-groups", params=query
            )
        )

    def create_unsubscribe_group(
        self, workspace_id: int, name: str
    ) -> UnsubscribeGroup:
        """Create an unsubscribe group in a workspace.

        Uses the organization API host (https://api.laneful.net).
        """
        return self._parse_unsubscribe_group(
            self._make_request(
                "POST",
                f"/workspaces/{workspace_id}/unsubscribe-groups",
                {"name": name},
            )
        )

    def update_unsubscribe_group(
        self, workspace_id: int, unsubscribe_group_id: int, name: str
    ) -> UnsubscribeGroup:
        """Update an unsubscribe group.

        Uses the organization API host (https://api.laneful.net).
        """
        return self._parse_unsubscribe_group(
            self._make_request(
                "PATCH",
                f"/workspaces/{workspace_id}/unsubscribe-groups/{unsubscribe_group_id}",
                {"name": name},
            )
        )

    def list_domains(
        self, workspace_id: int, params: Optional[ListDomainsParams] = None
    ) -> ListDomainsResponse:
        """List sending domains for a workspace.

        Uses the organization API host (https://api.laneful.net).
        """
        query = params.to_query() if params else None
        return ListDomainsResponse.from_dict(
            self._make_request(
                "GET", f"/workspaces/{workspace_id}/domains", params=query
            )
        )

    def get_domain(self, workspace_id: int, domain: str) -> Domain:
        """Get a single sending domain by name.

        Uses the organization API host (https://api.laneful.net).
        """
        encoded = self._encode_path(domain)
        return Domain.from_dict(
            self._make_request("GET", f"/workspaces/{workspace_id}/domains/{encoded}")
        )

    def create_domain(self, workspace_id: int, request: CreateDomainRequest) -> Domain:
        """Create a sending domain in a workspace.

        Uses the organization API host (https://api.laneful.net).
        """
        return Domain.from_dict(
            self._make_request(
                "POST", f"/workspaces/{workspace_id}/domains", request.to_dict()
            )
        )

    def update_domain(
        self, workspace_id: int, domain: str, request: UpdateDomainRequest
    ) -> Domain:
        """Update a domain's mutable settings (currently the email track).

        Uses the organization API host (https://api.laneful.net).
        """
        encoded = self._encode_path(domain)
        return Domain.from_dict(
            self._make_request(
                "PATCH",
                f"/workspaces/{workspace_id}/domains/{encoded}",
                request.to_dict(),
            )
        )

    def verify_domain(self, workspace_id: int, domain: str) -> Domain:
        """Trigger DNS verification for a domain.

        Uses the organization API host (https://api.laneful.net).
        """
        encoded = self._encode_path(domain)
        return Domain.from_dict(
            self._make_request(
                "POST", f"/workspaces/{workspace_id}/domains/{encoded}/verify"
            )
        )

    def delete_domain(self, workspace_id: int, domain: str) -> SuccessResponse:
        """Delete a sending domain from a workspace.

        Uses the organization API host (https://api.laneful.net).
        """
        encoded = self._encode_path(domain)
        return SuccessResponse.from_dict(
            self._make_request(
                "DELETE", f"/workspaces/{workspace_id}/domains/{encoded}"
            )
        )

    def list_domain_spam_ratio_radar(
        self, params: Optional[ListDomainSpamRatioRadarParams] = None
    ) -> ListDomainSpamRatioRadarResponse:
        """List domains whose spam complaint ratio reached a critical level.

        Uses the organization API host (https://api.laneful.net).
        """
        query = params.to_query() if params else None
        return ListDomainSpamRatioRadarResponse.from_dict(
            self._make_request(
                "GET", "/analytics/radar/domain-spam-ratio", params=query
            )
        )

    def list_google_postmaster_spam_reports(
        self, params: Optional[ListGooglePostmasterSpamReportsParams] = None
    ) -> ListGooglePostmasterSpamReportsResponse:
        """List daily Google Postmaster Tools spam-rate reports.

        Uses the organization API host (https://api.laneful.net).
        """
        query = params.to_query() if params else None
        return ListGooglePostmasterSpamReportsResponse.from_dict(
            self._make_request(
                "GET", "/analytics/google-postmaster/spam-reports", params=query
            )
        )

    def list_snds_reports(
        self, params: Optional[ListSndsReportsParams] = None
    ) -> ListSndsReportsResponse:
        """List daily Microsoft SNDS reports for the organization's sending IPs.

        Uses the organization API host (https://api.laneful.net).
        """
        query = params.to_query() if params else None
        return ListSndsReportsResponse.from_dict(
            self._make_request("GET", "/analytics/microsoft-snds/reports", params=query)
        )

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self) -> "LanefulClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
