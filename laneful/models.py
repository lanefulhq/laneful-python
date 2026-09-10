"""
Data models for the Laneful API.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Address:
    """Email address with optional display name."""

    email: str
    name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {"email": self.email}
        if self.name:
            result["name"] = self.name
        return result


@dataclass
class Attachment:
    """Email attachment."""

    content_type: str
    file_name: str = ""
    content: str = ""  # Base64 encoded content
    inline_id: str = ""

    def __post_init__(self) -> None:
        """Validate the attachment after initialization."""
        if not self.file_name and not self.inline_id:
            raise ValueError(
                "Either file_name or inline_id is required for attachments"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        result = {"content_type": self.content_type}

        if self.file_name:
            result["file_name"] = self.file_name
        if self.content:
            result["content"] = self.content
        if self.inline_id:
            result["inline_id"] = self.inline_id

        return result


@dataclass
class TrackingSettings:
    """Email tracking settings."""

    opens: bool = True
    clicks: bool = True
    unsubscribes: bool = True
    unsubscribe_group_id: Optional[int] = None
    unsubscribe_group_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        result: Dict[str, Any] = {
            "opens": self.opens,
            "clicks": self.clicks,
            "unsubscribes": self.unsubscribes,
        }
        if self.unsubscribe_group_id is not None:
            result["unsubscribe_group_id"] = self.unsubscribe_group_id
        if self.unsubscribe_group_name is not None:
            result["unsubscribe_group_name"] = self.unsubscribe_group_name
        return result


@dataclass
class MailSettings:
    """Request-level mail settings (sandbox mode, return message IDs)."""

    sandbox_mode: Optional[bool] = None
    return_message_ids: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Omit unset fields; send false when explicitly set."""
        result: Dict[str, Any] = {}
        if self.sandbox_mode is not None:
            result["sandbox_mode"] = self.sandbox_mode
        if self.return_message_ids is not None:
            result["return_message_ids"] = self.return_message_ids
        return result


@dataclass
class Email:
    """Email message data."""

    from_address: Address
    subject: str
    to: List[Address] = field(default_factory=list)
    cc: List[Address] = field(default_factory=list)
    bcc: List[Address] = field(default_factory=list)
    text_content: str = ""
    html_content: str = ""
    template_id: str = ""
    template_data: Dict[str, Any] = field(default_factory=dict)
    attachments: List[Attachment] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    reply_to: Optional[Address] = None
    send_time: int = 0  # Unix timestamp
    webhook_data: Dict[str, str] = field(default_factory=dict)
    tag: str = ""
    tracking: Optional[TrackingSettings] = None
    from_header: Optional[Address] = None

    def __post_init__(self) -> None:
        """Validate the email after initialization."""
        if not self.text_content and not self.html_content and not self.template_id:
            raise ValueError(
                "Email must have either text_content, html_content, or template_id"
            )

        if not self.to and not self.cc and not self.bcc:
            raise ValueError("Email must have at least one recipient (to, cc, or bcc)")

        if self.webhook_data:
            if len(self.webhook_data) > 20:
                raise ValueError("Webhook data cannot have more than 20 keys")
            for key, value in self.webhook_data.items():
                if len(str(key)) > 50:
                    raise ValueError("Webhook data keys cannot exceed 50 characters")
                if len(str(value)) > 100:
                    raise ValueError("Webhook data values cannot exceed 100 characters")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        result: Dict[str, Any] = {
            "from": self.from_address.to_dict(),
            "subject": self.subject,
        }
        if self.to:
            result["to"] = [addr.to_dict() for addr in self.to]

        if self.from_header:
            result["from_header"] = self.from_header.to_dict()
        if self.cc:
            result["cc"] = [addr.to_dict() for addr in self.cc]
        if self.bcc:
            result["bcc"] = [addr.to_dict() for addr in self.bcc]
        if self.text_content:
            result["text_content"] = self.text_content
        if self.html_content:
            result["html_content"] = self.html_content
        if self.template_id:
            result["template_id"] = self.template_id
        if self.template_data:
            result["template_data"] = self.template_data
        if self.attachments:
            result["attachments"] = [att.to_dict() for att in self.attachments]
        if self.headers:
            result["headers"] = self.headers
        if self.reply_to:
            result["reply_to"] = self.reply_to.to_dict()
        if self.send_time:
            result["send_time"] = self.send_time
        if self.webhook_data:
            result["webhook_data"] = self.webhook_data
        if self.tag:
            result["tag"] = self.tag
        if self.tracking:
            result["tracking"] = self.tracking.to_dict()

        return result


@dataclass
class EmailResponse:
    """Response from sending an email."""

    status: str
    message_id: Optional[str] = None
    message: Optional[str] = None
    message_ids: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailResponse":
        """Create from API response data."""
        message_ids = data.get("message_ids")
        message_id = data.get("message_id")
        if message_id is None and isinstance(message_ids, list) and message_ids:
            message_id = message_ids[0]
        return cls(
            status=data.get("status", "unknown"),
            message_id=message_id,
            message=data.get("message"),
            message_ids=message_ids if isinstance(message_ids, list) else None,
        )


# Type aliases for backward compatibility
EmailList = List[Email]
EmailResponseList = List[EmailResponse]
