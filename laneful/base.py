"""
Base client functionality shared between sync and async clients.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from urllib.parse import quote, urljoin

from ._version import __version__
from .exceptions import LanefulAPIError, LanefulAuthError
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
    SuccessResponse,
    UnsubscribeGroup,
    UpdateDomainRequest,
)


class BaseLanefulClient(ABC):
    """
    Base class for Laneful API clients.

    This abstract base class provides common functionality for both sync and async clients.
    Email sending uses a send host (https://your-endpoint.send.laneful.net).
    Domain, unsubscribe-group, and analytics endpoints use the organization
    API host (https://api.laneful.net).
    """

    def __init__(
        self,
        base_url: str,
        auth_token: str,
        timeout: float = 30.0,
        verify_ssl: bool = True,
    ) -> None:
        """
        Initialize the base client.

        Args:
            base_url: The base URL for the Laneful API endpoint
            auth_token: Your authentication token
            timeout: Request timeout in seconds (default: 30.0)
            verify_ssl: Whether to verify SSL certificates (default: True)
        """
        if not (base_url or "").strip():
            raise ValueError("Base URL cannot be empty")
        if not (auth_token or "").strip():
            raise ValueError("Auth token cannot be empty")

        self.base_url = base_url.strip().rstrip("/")
        self.auth_token = auth_token.strip()
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": f"laneful-python/{__version__}",
        }

    def _build_url(self, endpoint: str) -> str:
        """Build the full URL for an API endpoint."""
        return urljoin(self.base_url + "/v1/", endpoint.lstrip("/"))

    def _encode_path(self, value: str) -> str:
        """URL-encode a path segment (matches rawurlencode)."""
        return quote(value, safe="-._~")

    def _build_send_payload(
        self, emails: EmailList, mail_settings: Optional[MailSettings] = None
    ) -> Dict[str, Any]:
        """Build the JSON body for /email/send."""
        payload: Dict[str, Any] = {"emails": [email.to_dict() for email in emails]}
        if mail_settings is not None:
            payload["mail_settings"] = mail_settings.to_dict()
        return payload

    def _process_response_data(
        self, response_data: Dict[str, Any], status_code: int
    ) -> Dict[str, Any]:
        """
        Process response data and handle errors.

        Args:
            response_data: The parsed response data
            status_code: HTTP status code

        Returns:
            Processed response data

        Raises:
            LanefulAuthError: If authentication fails
            LanefulAPIError: If the API returns an error
        """
        # Handle authentication errors
        if status_code == 401:
            raise LanefulAuthError("Invalid authentication token")

        # Handle API errors
        if status_code >= 400:
            error_message = (
                response_data.get("error")
                or response_data.get("message")
                or f"HTTP {status_code}"
            )
            raise LanefulAPIError(
                message=str(error_message),
                status_code=status_code,
                response_data=response_data,
            )

        return response_data

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response text, handling decode errors."""
        try:
            result = json.loads(response_text)
            # Ensure we return a dict, even if the JSON is valid but not a dict
            if isinstance(result, dict):
                return result
            return {"data": result}
        except json.JSONDecodeError:
            return {"message": response_text}

    def _process_email_response(self, response_data: Dict[str, Any]) -> EmailResponse:
        """Process a single email response."""
        return EmailResponse.from_dict(response_data)

    def _process_emails_response(
        self, response_data: Dict[str, Any], email_count: int
    ) -> EmailResponseList:
        """Process bulk email response."""
        # Handle both single response and list of responses
        # Check if the API returned a list wrapped in "data" field
        if "data" in response_data and isinstance(response_data["data"], list):
            return [EmailResponse.from_dict(item) for item in response_data["data"]]
        elif "responses" in response_data:
            return [
                EmailResponse.from_dict(item) for item in response_data["responses"]
            ]
        else:
            # Fallback: create responses for each email
            return [EmailResponse.from_dict(response_data) for _ in range(email_count)]

    def _validate_emails_list(self, emails: EmailList) -> None:
        """Validate that emails list is not empty."""
        if not emails:
            raise ValueError("Email list cannot be empty")

    def _parse_unsubscribe_group(self, data: Dict[str, Any]) -> UnsubscribeGroup:
        """Parse a create/update unsubscribe-group response."""
        payload = data.get("unsubscribe_group")
        if isinstance(payload, dict):
            return UnsubscribeGroup.from_dict(payload)
        return UnsubscribeGroup.from_dict(data)

    @abstractmethod
    def send_email(
        self, email: Email, mail_settings: Optional[MailSettings] = None
    ) -> EmailResponse:
        """Send a single email. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def send_emails(
        self, emails: EmailList, mail_settings: Optional[MailSettings] = None
    ) -> EmailResponseList:
        """Send multiple emails. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def get_email_status(self, message_id: str) -> Dict[str, Any]:
        """Get email status. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def list_unsubscribe_groups(
        self, workspace_id: int, params: Optional[ListUnsubscribeGroupsParams] = None
    ) -> ListUnsubscribeGroupsResponse:
        """List unsubscribe groups for a workspace."""
        pass

    @abstractmethod
    def create_unsubscribe_group(
        self, workspace_id: int, name: str
    ) -> UnsubscribeGroup:
        """Create an unsubscribe group in a workspace."""
        pass

    @abstractmethod
    def update_unsubscribe_group(
        self, workspace_id: int, unsubscribe_group_id: int, name: str
    ) -> UnsubscribeGroup:
        """Update an unsubscribe group."""
        pass

    @abstractmethod
    def list_domains(
        self, workspace_id: int, params: Optional[ListDomainsParams] = None
    ) -> ListDomainsResponse:
        """List sending domains for a workspace."""
        pass

    @abstractmethod
    def get_domain(self, workspace_id: int, domain: str) -> Domain:
        """Get a single sending domain by name."""
        pass

    @abstractmethod
    def create_domain(self, workspace_id: int, request: CreateDomainRequest) -> Domain:
        """Create a sending domain in a workspace."""
        pass

    @abstractmethod
    def update_domain(
        self, workspace_id: int, domain: str, request: UpdateDomainRequest
    ) -> Domain:
        """Update a domain's mutable settings."""
        pass

    @abstractmethod
    def verify_domain(self, workspace_id: int, domain: str) -> Domain:
        """Trigger DNS verification for a domain."""
        pass

    @abstractmethod
    def delete_domain(self, workspace_id: int, domain: str) -> SuccessResponse:
        """Delete a sending domain from a workspace."""
        pass

    @abstractmethod
    def list_domain_spam_ratio_radar(
        self, params: Optional[ListDomainSpamRatioRadarParams] = None
    ) -> ListDomainSpamRatioRadarResponse:
        """List domains whose spam complaint ratio reached a critical level."""
        pass

    @abstractmethod
    def list_google_postmaster_spam_reports(
        self, params: Optional[ListGooglePostmasterSpamReportsParams] = None
    ) -> ListGooglePostmasterSpamReportsResponse:
        """List daily Google Postmaster Tools spam-rate reports."""
        pass

    @abstractmethod
    def list_snds_reports(
        self, params: Optional[ListSndsReportsParams] = None
    ) -> ListSndsReportsResponse:
        """List daily Microsoft SNDS reports for the organization's sending IPs."""
        pass
