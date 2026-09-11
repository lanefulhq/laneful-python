"""Tests for the Laneful client."""

import json
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import ConnectionError, Timeout

from laneful import (
    Address,
    CreateDomainRequest,
    Email,
    EmailResponse,
    LanefulClient,
    ListDomainSpamRatioRadarParams,
    ListDomainsParams,
    MailSettings,
    UpdateDomainRequest,
    __version__,
)
from laneful.exceptions import LanefulAPIError, LanefulAuthError, LanefulError


class TestLanefulClient:
    """Test cases for LanefulClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = LanefulClient(
            base_url="https://test.laneful.net", auth_token="test-token"
        )

        self.sample_email = Email(
            from_address=Address(email="sender@test.com", name="Test Sender"),
            to=[Address(email="recipient@test.com", name="Test Recipient")],
            subject="Test Subject",
            text_content="Test content",
        )

    def test_client_initialization(self):
        """Test client initialization."""
        assert self.client.base_url == "https://test.laneful.net"
        assert self.client.auth_token == "test-token"
        assert "Bearer test-token" in self.client.session.headers["Authorization"]
        assert self.client.headers["User-Agent"] == f"laneful-python/{__version__}"
        assert self.client.headers["Accept"] == "application/json"

    def test_client_rejects_empty_config(self):
        """Empty base URL or token is rejected."""
        with pytest.raises(ValueError, match="Base URL"):
            LanefulClient("  ", "token")
        with pytest.raises(ValueError, match="Auth token"):
            LanefulClient("https://test.laneful.net", "")

    def test_client_initialization_strips_trailing_slash(self):
        """Test that trailing slashes are stripped from base URL."""
        client = LanefulClient("https://test.laneful.net/", "token")
        assert client.base_url == "https://test.laneful.net"

    @patch("requests.Session.request")
    def test_send_email_success(self, mock_request):
        """Test successful email sending."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = '{"status": "sent", "message_id": "msg_123"}'
        mock_response.json.return_value = {"status": "sent", "message_id": "msg_123"}
        mock_request.return_value = mock_response

        response = self.client.send_email(self.sample_email)

        assert isinstance(response, EmailResponse)
        assert response.status == "sent"
        assert response.message_id == "msg_123"

        # Verify the request was made correctly
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/email" in call_args[1]["url"]
        assert call_args[1]["json"] == {"emails": [self.sample_email.to_dict()]}

    @patch("requests.Session.request")
    def test_send_email_with_mail_settings(self, mock_request):
        """Mail settings are included on the send payload."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = '{"status": "accepted", "message_ids": ["msg_123"]}'
        mock_request.return_value = mock_response

        response = self.client.send_email(
            self.sample_email,
            MailSettings(sandbox_mode=True, return_message_ids=True),
        )

        assert response.status == "accepted"
        assert response.message_ids == ["msg_123"]
        assert response.message_id == "msg_123"
        assert mock_request.call_args[1]["json"] == {
            "emails": [self.sample_email.to_dict()],
            "mail_settings": {
                "sandbox_mode": True,
                "return_message_ids": True,
            },
        }

    @patch("requests.Session.request")
    def test_send_emails_success(self, mock_request):
        """Test successful bulk email sending."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = '{"responses": [{"status": "sent", "message_id": "msg_123"}, {"status": "sent", "message_id": "msg_124"}]}'
        mock_response.json.return_value = {
            "responses": [
                {"status": "sent", "message_id": "msg_123"},
                {"status": "sent", "message_id": "msg_124"},
            ]
        }
        mock_request.return_value = mock_response

        emails = [self.sample_email, self.sample_email]
        responses = self.client.send_emails(emails)

        assert len(responses) == 2
        assert all(isinstance(r, EmailResponse) for r in responses)
        assert responses[0].message_id == "msg_123"
        assert responses[1].message_id == "msg_124"

    @patch("requests.Session.request")
    def test_send_email_auth_error(self, mock_request):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = '{"message": "Unauthorized"}'
        mock_response.json.return_value = {"message": "Unauthorized"}
        mock_request.return_value = mock_response

        with pytest.raises(LanefulAuthError) as exc_info:
            self.client.send_email(self.sample_email)

        assert "Invalid authentication token" in str(exc_info.value)

    @patch("requests.Session.request")
    def test_send_email_api_error(self, mock_request):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = '{"message": "Invalid email format"}'
        mock_response.json.return_value = {"message": "Invalid email format"}
        mock_request.return_value = mock_response

        with pytest.raises(LanefulAPIError) as exc_info:
            self.client.send_email(self.sample_email)

        assert exc_info.value.status_code == 400
        assert "Invalid email format" in exc_info.value.message

    @patch("requests.Session.request")
    def test_send_email_connection_error(self, mock_request):
        """Test connection error handling."""
        mock_request.side_effect = ConnectionError("Connection failed")

        with pytest.raises(LanefulError) as exc_info:
            self.client.send_email(self.sample_email)

        assert "Failed to connect to Laneful API" in str(exc_info.value)

    @patch("requests.Session.request")
    def test_send_email_timeout(self, mock_request):
        """Test timeout error handling."""
        mock_request.side_effect = Timeout("Request timed out")

        with pytest.raises(LanefulError) as exc_info:
            self.client.send_email(self.sample_email)

        assert "Request timed out" in str(exc_info.value)

    @patch("requests.Session.request")
    def test_send_email_json_decode_error(self, mock_request):
        """Test handling of invalid JSON responses."""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Internal Server Error"
        mock_request.return_value = mock_response

        with pytest.raises(LanefulAPIError) as exc_info:
            self.client.send_email(self.sample_email)

        assert exc_info.value.status_code == 500
        assert "Internal Server Error" in exc_info.value.message

    def test_send_emails_empty_list(self):
        """Test that sending empty email list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            self.client.send_emails([])

        assert "Email list cannot be empty" in str(exc_info.value)

    @patch("requests.Session.request")
    def test_get_email_status(self, mock_request):
        """Test getting email status."""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = '{"status": "delivered", "delivered_at": 1640995200}'
        mock_response.json.return_value = {
            "status": "delivered",
            "delivered_at": 1640995200,
        }
        mock_request.return_value = mock_response

        status = self.client.get_email_status("msg_123")

        assert status["status"] == "delivered"
        assert status["delivered_at"] == 1640995200

        # Verify the request was made correctly
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]["method"] == "GET"
        assert "/email/msg_123/status" in call_args[1]["url"]

    def test_context_manager(self):
        """Test client as context manager."""
        with patch.object(self.client, "close") as mock_close:
            with self.client as client:
                assert client is self.client
            mock_close.assert_called_once()

    def test_close(self):
        """Test client close method."""
        with patch.object(self.client.session, "close") as mock_close:
            self.client.close()
            mock_close.assert_called_once()

    def _ok(self, mock_request, body):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.text = json.dumps(body)
        mock_request.return_value = mock_response
        return mock_response

    @patch("requests.Session.request")
    def test_list_unsubscribe_groups(self, mock_request):
        """List unsubscribe groups parses the response."""
        self._ok(
            mock_request,
            {
                "unsubscribe_groups": [
                    {
                        "unsubscribe_group_id": 9,
                        "name": "Newsletters",
                        "created_at": 1,
                    }
                ]
            },
        )
        result = self.client.list_unsubscribe_groups(42)
        assert result.unsubscribe_groups[0].name == "Newsletters"
        assert "/workspaces/42/unsubscribe-groups" in mock_request.call_args[1]["url"]

    @patch("requests.Session.request")
    def test_list_domains_query(self, mock_request):
        """List domains sends filter[domain] and pagination."""
        self._ok(
            mock_request,
            {
                "domains": [{"domain": "example.com", "verified": True}],
                "pagination": {"next_cursor": "next"},
            },
        )
        result = self.client.list_domains(
            42, ListDomainsParams(limit=25, filter_domain="example.com")
        )
        assert result.domains[0].domain == "example.com"
        assert result.next_cursor == "next"
        assert mock_request.call_args[1]["params"] == [
            ("limit", "25"),
            ("filter[domain]", "example.com"),
        ]

    @patch("requests.Session.request")
    def test_get_and_mutate_domain(self, mock_request):
        """Domain get/create/update/verify/delete hit the encoded path."""
        self._ok(mock_request, {"domain": "example.com", "verified": True})
        domain = self.client.get_domain(42, "example.com")
        assert domain.domain == "example.com"
        assert "/workspaces/42/domains/example.com" in mock_request.call_args[1]["url"]

        self.client.create_domain(
            42,
            CreateDomainRequest(domain="example.com", tracking="t", return_path="rp"),
        )
        assert mock_request.call_args[1]["method"] == "POST"
        assert mock_request.call_args[1]["json"] == {
            "domain": "example.com",
            "tracking": "t",
            "return_path": "rp",
        }

        self.client.update_domain(42, "example.com", UpdateDomainRequest(""))
        assert mock_request.call_args[1]["method"] == "PATCH"
        assert mock_request.call_args[1]["json"] == {"email_track_id": ""}

        self.client.verify_domain(42, "example.com")
        assert mock_request.call_args[1]["url"].endswith("/verify")

        self._ok(mock_request, {"message": "deleted"})
        deleted = self.client.delete_domain(42, "example.com")
        assert deleted.message == "deleted"
        assert mock_request.call_args[1]["method"] == "DELETE"

    @patch("requests.Session.request")
    def test_create_and_update_unsubscribe_group(self, mock_request):
        """Create and update unwrap the unsubscribe_group payload."""
        self._ok(
            mock_request,
            {"unsubscribe_group": {"unsubscribe_group_id": 9, "name": "Newsletters"}},
        )
        created = self.client.create_unsubscribe_group(42, "Newsletters")
        assert created.unsubscribe_group_id == 9
        assert created.name == "Newsletters"
        assert mock_request.call_args[1]["method"] == "POST"
        assert mock_request.call_args[1]["json"] == {"name": "Newsletters"}

        self._ok(mock_request, {"unsubscribe_group_id": 9, "name": "Weekly"})
        updated = self.client.update_unsubscribe_group(42, 9, "Weekly")
        assert updated.name == "Weekly"
        assert mock_request.call_args[1]["method"] == "PATCH"
        assert "/unsubscribe-groups/9" in mock_request.call_args[1]["url"]

    @patch("requests.Session.request")
    def test_analytics_repeated_workspace_ids(self, mock_request):
        """Analytics radar repeats workspace_ids query keys."""
        self._ok(mock_request, {"radar": []})
        self.client.list_domain_spam_ratio_radar(
            ListDomainSpamRatioRadarParams(workspace_ids=[1, 2])
        )
        assert mock_request.call_args[1]["params"] == [
            ("workspace_ids", "1"),
            ("workspace_ids", "2"),
        ]
        assert "/analytics/radar/domain-spam-ratio" in mock_request.call_args[1]["url"]

        self._ok(mock_request, {"spam_reports": []})
        self.client.list_google_postmaster_spam_reports()
        assert (
            "/analytics/google-postmaster/spam-reports"
            in mock_request.call_args[1]["url"]
        )

        self._ok(mock_request, {"snds_reports": []})
        self.client.list_snds_reports()
        assert "/analytics/microsoft-snds/reports" in mock_request.call_args[1]["url"]
