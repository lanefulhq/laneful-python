"""Tests for Laneful data models."""

import pytest

from laneful.models import (
    Address,
    Attachment,
    Email,
    EmailResponse,
    MailSettings,
    TrackingSettings,
)
from laneful.org_models import (
    CreateDomainRequest,
    Domain,
    ListDomainSpamRatioRadarParams,
    ListDomainsParams,
    UpdateDomainRequest,
)


class TestAddress:
    """Test cases for Address model."""

    def test_address_with_email_only(self):
        """Test creating address with email only."""
        addr = Address(email="test@example.com")
        assert addr.email == "test@example.com"
        assert addr.name == ""

    def test_address_with_name(self):
        """Test creating address with name."""
        addr = Address(email="test@example.com", name="Test User")
        assert addr.email == "test@example.com"
        assert addr.name == "Test User"

    def test_address_to_dict(self):
        """Test converting address to dictionary."""
        addr = Address(email="test@example.com", name="Test User")
        expected = {"email": "test@example.com", "name": "Test User"}
        assert addr.to_dict() == expected

    def test_address_to_dict_no_name(self):
        """Test converting address to dictionary without name."""
        addr = Address(email="test@example.com")
        expected = {"email": "test@example.com"}
        assert addr.to_dict() == expected


class TestAttachment:
    """Test cases for Attachment model."""

    def test_attachment_creation(self):
        """Test creating attachment."""
        att = Attachment(
            file_name="test.txt",
            content="dGVzdCBjb250ZW50",  # base64 encoded "test content"
            content_type="text/plain",
        )
        assert att.file_name == "test.txt"
        assert att.content == "dGVzdCBjb250ZW50"
        assert att.content_type == "text/plain"

    def test_attachment_to_dict(self):
        """Test converting attachment to dictionary."""
        att = Attachment(
            file_name="test.txt", content="dGVzdCBjb250ZW50", content_type="text/plain"
        )
        expected = {
            "file_name": "test.txt",
            "content": "dGVzdCBjb250ZW50",
            "content_type": "text/plain",
        }
        assert att.to_dict() == expected

    def test_attachment_validation_failure(self):
        """Test attachment validation fails without file_name or inline_id."""
        with pytest.raises(ValueError) as exc_info:
            Attachment(content_type="text/plain", content="content")
        assert "Either file_name or inline_id is required" in str(exc_info.value)

    def test_attachment_with_inline_id(self):
        """Test creating attachment with inline_id."""
        att = Attachment(
            content_type="image/png", inline_id="img1", content="base64content"
        )
        expected = {
            "content_type": "image/png",
            "inline_id": "img1",
            "content": "base64content",
        }
        assert att.to_dict() == expected


class TestTrackingSettings:
    """Test cases for TrackingSettings model."""

    def test_tracking_settings_defaults(self):
        """Test default tracking settings."""
        tracking = TrackingSettings()
        assert tracking.opens is True
        assert tracking.clicks is True
        assert tracking.unsubscribes is True
        assert tracking.unsubscribe_group_id is None

    def test_tracking_settings_custom(self):
        """Test custom tracking settings."""
        tracking = TrackingSettings(opens=True, clicks=True, unsubscribes=True)
        assert tracking.opens is True
        assert tracking.clicks is True
        assert tracking.unsubscribes is True

    def test_tracking_settings_to_dict(self):
        """Test converting tracking settings to dictionary."""
        tracking = TrackingSettings(opens=True, clicks=False, unsubscribes=True)
        expected = {"opens": True, "clicks": False, "unsubscribes": True}
        assert tracking.to_dict() == expected

    def test_tracking_settings_with_unsubscribe_group(self):
        """Test tracking settings with unsubscribe group ID."""
        tracking = TrackingSettings(unsubscribe_group_id=123)
        result = tracking.to_dict()
        assert result["unsubscribe_group_id"] == 123

    def test_tracking_settings_with_unsubscribe_group_name(self):
        """Test tracking settings with unsubscribe group name."""
        tracking = TrackingSettings(unsubscribe_group_name="Newsletters")
        result = tracking.to_dict()
        assert result["unsubscribe_group_name"] == "Newsletters"


class TestMailSettings:
    """Test cases for MailSettings model."""

    def test_mail_settings_omits_unset(self):
        """Unset fields are omitted from the payload."""
        assert MailSettings().to_dict() == {}

    def test_mail_settings_sends_false(self):
        """Explicit false values are serialized."""
        settings = MailSettings(sandbox_mode=False, return_message_ids=False)
        assert settings.to_dict() == {
            "sandbox_mode": False,
            "return_message_ids": False,
        }


class TestEmail:
    """Test cases for Email model."""

    def setup_method(self):
        """Set up test fixtures."""
        self.from_addr = Address(email="sender@test.com", name="Sender")
        self.to_addr = Address(email="recipient@test.com", name="Recipient")

    def test_email_minimal(self):
        """Test creating minimal email."""
        email = Email(
            from_address=self.from_addr,
            to=[self.to_addr],
            subject="Test Subject",
            text_content="Test content",
        )
        assert email.from_address == self.from_addr
        assert email.to == [self.to_addr]
        assert email.subject == "Test Subject"
        assert email.text_content == "Test content"
        assert email.html_content == ""

    def test_email_validation_no_content(self):
        """Test email validation fails without content."""
        with pytest.raises(ValueError) as exc_info:
            Email(
                from_address=self.from_addr, to=[self.to_addr], subject="Test Subject"
            )
        assert "must have either text_content, html_content, or template_id" in str(
            exc_info.value
        )

    def test_email_validation_no_recipients(self):
        """Test email validation fails without recipients."""
        with pytest.raises(ValueError) as exc_info:
            Email(
                from_address=self.from_addr,
                to=[],
                cc=[],
                bcc=[],
                subject="Test Subject",
                text_content="Test content",
            )
        assert "must have at least one recipient" in str(exc_info.value)

    def test_email_with_template(self):
        """Test email with template ID passes validation."""
        email = Email(
            from_address=self.from_addr,
            to=[self.to_addr],
            subject="Test Subject",
            template_id="welcome-template",
        )
        assert email.template_id == "welcome-template"

    def test_email_to_dict_minimal(self):
        """Test converting minimal email to dictionary."""
        email = Email(
            from_address=self.from_addr,
            to=[self.to_addr],
            subject="Test Subject",
            text_content="Test content",
        )

        result = email.to_dict()
        expected_keys = {
            "from": {"email": "sender@test.com", "name": "Sender"},
            "to": [{"email": "recipient@test.com", "name": "Recipient"}],
            "subject": "Test Subject",
            "text_content": "Test content",
            "cc": [],
            "bcc": [],
            "html_content": "",
            "template_id": "",
            "template_data": {},
            "attachments": [],
            "headers": {},
            "send_time": 0,
            "webhook_data": {},
            "tag": "",
        }

        # Check required fields match exactly
        for key, value in expected_keys.items():
            if key in result:
                assert result[key] == value

    def test_email_to_dict_full(self):
        """Test converting full email to dictionary."""
        cc_addr = Address(email="cc@test.com")
        bcc_addr = Address(email="bcc@test.com")
        reply_addr = Address(email="reply@test.com")
        attachment = Attachment(
            file_name="file.txt", content="content", content_type="text/plain"
        )
        tracking = TrackingSettings(opens=True, clicks=True)

        email = Email(
            from_address=self.from_addr,
            to=[self.to_addr],
            subject="Test Subject",
            text_content="Test content",
            html_content="<p>Test content</p>",
            cc=[cc_addr],
            bcc=[bcc_addr],
            reply_to=reply_addr,
            attachments=[attachment],
            headers={"X-Custom": "value"},
            template_id="template-123",
            template_data={"name": "John"},
            send_time=1640995200,
            tracking=tracking,
            webhook_data={"user_id": "123"},
        )

        result = email.to_dict()

        # Check that all fields are present
        assert "from" in result
        assert "to" in result
        assert "subject" in result
        assert "text_content" in result
        assert "html_content" in result
        assert "cc" in result
        assert "bcc" in result
        assert "reply_to" in result
        assert "attachments" in result
        assert "headers" in result
        assert "template_id" in result
        assert "template_data" in result
        assert "send_time" in result
        assert "tracking" in result
        assert "webhook_data" in result

        # Check specific values
        assert result["template_id"] == "template-123"
        assert result["send_time"] == 1640995200
        assert result["headers"]["X-Custom"] == "value"

    def test_email_from_header(self):
        """Test from_header is serialized when set."""
        email = Email(
            from_address=self.from_addr,
            to=[self.to_addr],
            subject="Test Subject",
            text_content="Test content",
            from_header=Address(email="newsletter@test.com", name="Newsletter"),
        )
        result = email.to_dict()
        assert result["from_header"] == {
            "email": "newsletter@test.com",
            "name": "Newsletter",
        }

    def test_email_omits_empty_optional_fields(self):
        """Empty optional collections are omitted from the payload."""
        email = Email(
            from_address=self.from_addr,
            to=[self.to_addr],
            subject="Test Subject",
            text_content="Test content",
        )
        result = email.to_dict()
        assert "cc" not in result
        assert "bcc" not in result
        assert "attachments" not in result
        assert "webhook_data" not in result
        assert "send_time" not in result

    def test_webhook_data_max_keys(self):
        """Webhook data cannot have more than 20 keys."""
        with pytest.raises(ValueError, match="more than 20 keys"):
            Email(
                from_address=self.from_addr,
                to=[self.to_addr],
                subject="Test Subject",
                text_content="Test content",
                webhook_data={f"k{i}": "v" for i in range(21)},
            )

    def test_webhook_data_key_length(self):
        """Webhook data keys cannot exceed 50 characters."""
        with pytest.raises(ValueError, match="50 characters"):
            Email(
                from_address=self.from_addr,
                to=[self.to_addr],
                subject="Test Subject",
                text_content="Test content",
                webhook_data={"k" * 51: "value"},
            )

    def test_webhook_data_value_length(self):
        """Webhook data values cannot exceed 100 characters."""
        with pytest.raises(ValueError, match="100 characters"):
            Email(
                from_address=self.from_addr,
                to=[self.to_addr],
                subject="Test Subject",
                text_content="Test content",
                webhook_data={"key": "v" * 101},
            )


class TestEmailResponse:
    """Test cases for EmailResponse model."""

    def test_email_response_creation(self):
        """Test creating email response."""
        response = EmailResponse(
            status="sent", message_id="msg_123", message="Email sent successfully"
        )
        assert response.status == "sent"
        assert response.message_id == "msg_123"
        assert response.message == "Email sent successfully"

    def test_email_response_from_dict(self):
        """Test creating email response from dictionary."""
        data = {
            "status": "sent",
            "message_id": "msg_123",
            "message": "Email sent successfully",
        }
        response = EmailResponse.from_dict(data)
        assert response.status == "sent"
        assert response.message_id == "msg_123"
        assert response.message == "Email sent successfully"

    def test_email_response_from_dict_minimal(self):
        """Test creating email response from minimal dictionary."""
        data = {}
        response = EmailResponse.from_dict(data)
        assert response.status == "unknown"
        assert response.message_id is None
        assert response.message is None
        assert response.message_ids is None

    def test_email_response_from_message_ids(self):
        """message_ids is parsed and message_id falls back to the first ID."""
        response = EmailResponse.from_dict(
            {"status": "accepted", "message_ids": ["msg_1", "msg_2"]}
        )
        assert response.message_ids == ["msg_1", "msg_2"]
        assert response.message_id == "msg_1"


class TestOrgModels:
    """Test cases for organization API models."""

    def test_update_domain_three_way(self):
        """Omit, clear, or set email_track_id."""
        assert UpdateDomainRequest().to_dict() == {}
        assert UpdateDomainRequest("").to_dict() == {"email_track_id": ""}
        assert UpdateDomainRequest("track-id").to_dict() == {
            "email_track_id": "track-id"
        }

    def test_create_domain_omits_empty_track(self):
        """Empty email_track_id is omitted on create."""
        request = CreateDomainRequest(
            domain="example.com",
            tracking="tracking",
            return_path="return-path",
            require_tls=True,
        )
        assert request.to_dict() == {
            "domain": "example.com",
            "tracking": "tracking",
            "return_path": "return-path",
            "require_tls": True,
        }

    def test_list_domains_filter_query(self):
        """Domain list uses filter[domain]."""
        params = ListDomainsParams(cursor="abc", limit=10, filter_domain="ex.com")
        assert params.to_query() == [
            ("cursor", "abc"),
            ("limit", "10"),
            ("filter[domain]", "ex.com"),
        ]

    def test_radar_repeats_workspace_ids(self):
        """Radar query repeats workspace_ids keys."""
        params = ListDomainSpamRatioRadarParams(
            workspace_ids=[1, 2],
            domain="example.com",
            start_date="2026-09-01",
            end_date="2026-09-08",
        )
        query = params.to_query()
        assert query[:2] == [("workspace_ids", "1"), ("workspace_ids", "2")]
        assert ("domain", "example.com") in query

    def test_domain_from_wrapped_payload(self):
        """Domain parser unwraps a nested domain object."""
        domain = Domain.from_dict(
            {"domain": {"domain": "example.com", "verified": True}}
        )
        assert domain.domain == "example.com"
        assert domain.verified is True
