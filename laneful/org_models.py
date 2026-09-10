"""Organization API models (domains, unsubscribe groups, analytics)."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

QueryItems = List[Tuple[str, str]]


def _query_value(key: str, value: Optional[Any]) -> QueryItems:
    if value is None or value == "":
        return []
    return [(key, str(value))]


def _query_limit(limit: Optional[int]) -> QueryItems:
    if limit is not None and limit > 0:
        return [("limit", str(limit))]
    return []


@dataclass
class UnsubscribeGroup:
    """An unsubscribe group in a workspace."""

    unsubscribe_group_id: int
    name: str
    created_at: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnsubscribeGroup":
        """Create from API response data."""
        return cls(
            unsubscribe_group_id=int(data.get("unsubscribe_group_id") or 0),
            name=str(data.get("name") or ""),
            created_at=int(data.get("created_at") or 0),
        )


@dataclass
class ListUnsubscribeGroupsResponse:
    """Paginated list of unsubscribe groups."""

    unsubscribe_groups: List[UnsubscribeGroup] = field(default_factory=list)
    next_cursor: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ListUnsubscribeGroupsResponse":
        """Create from API response data."""
        groups = [
            UnsubscribeGroup.from_dict(item)
            for item in data.get("unsubscribe_groups") or []
        ]
        return cls(unsubscribe_groups=groups, next_cursor=data.get("next_cursor"))


@dataclass
class ListUnsubscribeGroupsParams:
    """Query parameters for listing unsubscribe groups."""

    cursor: Optional[str] = None
    limit: Optional[int] = None
    search: Optional[str] = None

    def to_query(self) -> QueryItems:
        """Build query string items."""
        return (
            _query_value("cursor", self.cursor)
            + _query_limit(self.limit)
            + _query_value("search", self.search)
        )


@dataclass
class Domain:
    """A sending domain and its verification state."""

    domain: str
    tracking: str = ""
    return_path: str = ""
    verified: bool = False
    tracking_verified: bool = False
    return_path_verified: bool = False
    dkim1_verified: bool = False
    dkim2_verified: bool = False
    dmarc_verified: bool = False
    require_tls: bool = False
    email_track_id: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Domain":
        """Create from API response data."""
        payload = data.get("domain") if isinstance(data.get("domain"), dict) else data
        if not isinstance(payload, dict):
            payload = data
        return cls(
            domain=str(payload.get("domain") or ""),
            tracking=str(payload.get("tracking") or ""),
            return_path=str(payload.get("return_path") or ""),
            verified=payload.get("verified") is True,
            tracking_verified=payload.get("tracking_verified") is True,
            return_path_verified=payload.get("return_path_verified") is True,
            dkim1_verified=payload.get("dkim1_verified") is True,
            dkim2_verified=payload.get("dkim2_verified") is True,
            dmarc_verified=payload.get("dmarc_verified") is True,
            require_tls=payload.get("require_tls") is True,
            email_track_id=str(payload.get("email_track_id") or ""),
        )


@dataclass
class ListDomainsResponse:
    """Paginated list of sending domains."""

    domains: List[Domain] = field(default_factory=list)
    next_cursor: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ListDomainsResponse":
        """Create from API response data."""
        pagination = data.get("pagination") or {}
        return cls(
            domains=[Domain.from_dict(item) for item in data.get("domains") or []],
            next_cursor=pagination.get("next_cursor"),
        )


@dataclass
class ListDomainsParams:
    """Query parameters for listing domains."""

    cursor: Optional[str] = None
    limit: Optional[int] = None
    filter_domain: Optional[str] = None

    def to_query(self) -> QueryItems:
        """Build query string items."""
        return (
            _query_value("cursor", self.cursor)
            + _query_limit(self.limit)
            + _query_value("filter[domain]", self.filter_domain)
        )


@dataclass
class CreateDomainRequest:
    """Request body for creating a sending domain."""

    domain: str
    tracking: str
    return_path: str
    require_tls: Optional[bool] = None
    email_track_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        result: Dict[str, Any] = {
            "domain": self.domain,
            "tracking": self.tracking,
            "return_path": self.return_path,
        }
        if self.require_tls is not None:
            result["require_tls"] = self.require_tls
        if self.email_track_id:
            result["email_track_id"] = self.email_track_id
        return result


@dataclass
class UpdateDomainRequest:
    """Request body for updating a domain's mutable settings.

    Pass a track ID to set the email track, an empty string to clear it,
    or None to leave it unchanged.
    """

    email_track_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        if self.email_track_id is None:
            return {}
        return {"email_track_id": self.email_track_id}


@dataclass
class SuccessResponse:
    """Generic success message from mutating endpoints."""

    message: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SuccessResponse":
        """Create from API response data."""
        return cls(message=str(data.get("message") or ""))


@dataclass
class DomainSpamRatioRadar:
    """A sending domain whose spam complaint ratio reached a critical level."""

    workspace_id: int
    domain: str
    esp: str
    spam_ratio: float
    date: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainSpamRatioRadar":
        """Create from API response data."""
        return cls(
            workspace_id=int(data.get("workspace_id") or 0),
            domain=str(data.get("domain") or ""),
            esp=str(data.get("esp") or ""),
            spam_ratio=float(data.get("spam_ratio") or 0),
            date=str(data.get("date") or ""),
        )


@dataclass
class ListDomainSpamRatioRadarResponse:
    """Paginated list of domain spam-ratio radar entries."""

    radar: List[DomainSpamRatioRadar] = field(default_factory=list)
    next_cursor: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ListDomainSpamRatioRadarResponse":
        """Create from API response data."""
        return cls(
            radar=[
                DomainSpamRatioRadar.from_dict(item) for item in data.get("radar") or []
            ],
            next_cursor=data.get("next_cursor"),
        )


@dataclass
class ListDomainSpamRatioRadarParams:
    """Query parameters for listing domain spam-ratio radar entries."""

    workspace_ids: List[int] = field(default_factory=list)
    domain: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    cursor: Optional[str] = None
    limit: Optional[int] = None

    def to_query(self) -> QueryItems:
        """Build query string items (repeated workspace_ids keys)."""
        items: QueryItems = [
            ("workspace_ids", str(workspace_id)) for workspace_id in self.workspace_ids
        ]
        return (
            items
            + _query_value("domain", self.domain)
            + _query_value("start_date", self.start_date)
            + _query_value("end_date", self.end_date)
            + _query_value("cursor", self.cursor)
            + _query_limit(self.limit)
        )


@dataclass
class GooglePostmasterSpamReport:
    """A daily Gmail spam-rate report from Google Postmaster Tools."""

    workspace_id: int
    domain: str
    date: str
    spam_ratio: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GooglePostmasterSpamReport":
        """Create from API response data."""
        return cls(
            workspace_id=int(data.get("workspace_id") or 0),
            domain=str(data.get("domain") or ""),
            date=str(data.get("date") or ""),
            spam_ratio=float(data.get("spam_ratio") or 0),
        )


@dataclass
class ListGooglePostmasterSpamReportsResponse:
    """Paginated list of Google Postmaster spam reports."""

    spam_reports: List[GooglePostmasterSpamReport] = field(default_factory=list)
    next_cursor: Optional[str] = None

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any]
    ) -> "ListGooglePostmasterSpamReportsResponse":
        """Create from API response data."""
        return cls(
            spam_reports=[
                GooglePostmasterSpamReport.from_dict(item)
                for item in data.get("spam_reports") or []
            ],
            next_cursor=data.get("next_cursor"),
        )


@dataclass
class ListGooglePostmasterSpamReportsParams:
    """Query parameters for listing Google Postmaster spam reports."""

    workspace_ids: List[int] = field(default_factory=list)
    domain: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    cursor: Optional[str] = None
    limit: Optional[int] = None

    def to_query(self) -> QueryItems:
        """Build query string items (repeated workspace_ids keys)."""
        items: QueryItems = [
            ("workspace_ids", str(workspace_id)) for workspace_id in self.workspace_ids
        ]
        return (
            items
            + _query_value("domain", self.domain)
            + _query_value("start_date", self.start_date)
            + _query_value("end_date", self.end_date)
            + _query_value("cursor", self.cursor)
            + _query_limit(self.limit)
        )


@dataclass
class SndsReport:
    """A daily Microsoft SNDS report for a sending IP."""

    FILTER_UNKNOWN = ""
    FILTER_GREEN = "GREEN"
    FILTER_YELLOW = "YELLOW"
    FILTER_RED = "RED"

    ip: str
    date: str
    rcpt_commands: int
    data_commands: int
    message_recipients: int
    filter_result: str
    complaint_rate: float
    trap_hits: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SndsReport":
        """Create from API response data."""
        return cls(
            ip=str(data.get("ip") or ""),
            date=str(data.get("date") or ""),
            rcpt_commands=int(data.get("rcpt_commands") or 0),
            data_commands=int(data.get("data_commands") or 0),
            message_recipients=int(data.get("message_recipients") or 0),
            filter_result=str(data.get("filter_result") or cls.FILTER_UNKNOWN),
            complaint_rate=float(data.get("complaint_rate") or 0),
            trap_hits=int(data.get("trap_hits") or 0),
        )


@dataclass
class ListSndsReportsResponse:
    """Paginated list of Microsoft SNDS reports."""

    snds_reports: List[SndsReport] = field(default_factory=list)
    next_cursor: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ListSndsReportsResponse":
        """Create from API response data."""
        return cls(
            snds_reports=[
                SndsReport.from_dict(item) for item in data.get("snds_reports") or []
            ],
            next_cursor=data.get("next_cursor"),
        )


@dataclass
class ListSndsReportsParams:
    """Query parameters for listing Microsoft SNDS reports."""

    ip: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    cursor: Optional[str] = None
    limit: Optional[int] = None

    def to_query(self) -> QueryItems:
        """Build query string items."""
        return (
            _query_value("ip", self.ip)
            + _query_value("start_date", self.start_date)
            + _query_value("end_date", self.end_date)
            + _query_value("cursor", self.cursor)
            + _query_limit(self.limit)
        )
