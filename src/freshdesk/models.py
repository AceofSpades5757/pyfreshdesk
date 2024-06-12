from __future__ import annotations

import enum
import inspect
import logging.config
from copy import deepcopy
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from datetime import datetime
from datetime import timezone
from enum import Enum
from enum import IntEnum
from pathlib import Path
from typing import Any
from typing import Optional
from typing import TypedDict
from typing import Union
from urllib.parse import ParseResult

from freshdesk.enumerators import LogicalOperator
from freshdesk.enumerators import SolutionArticleStatus
from freshdesk.enumerators import SolutionFolderVisibility
from freshdesk.logger import get_config
from freshdesk.typings import TimeDeltaString


# Logging
logging.config.dictConfig(get_config(__file__))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@dataclass
class Attachment:
    id: int
    name: Path
    content_type: str  # MIME Type
    size: int
    created_at: datetime
    updated_at: datetime
    attachment_url: ParseResult

    # catch any additional fields
    extras: dict[str, Any] = field(default_factory=dict)

    _json: Optional[dict] = field(default=None, repr=False)

    @classmethod
    def from_json(cls, data: dict) -> Attachment:
        obj = cls(
            id=data["id"],
            name=Path(data["name"]),
            content_type=data["content_type"],
            size=data["size"],
            created_at=datetime.fromisoformat(data["created_at"][:-1]),
            updated_at=datetime.fromisoformat(data["updated_at"][:-1]),
            attachment_url=data["attachment_url"],
            extras={key: value for key, value in data.items() if key not in cls.__dataclass_fields__},  # noqa: 501
        )
        obj._json = data

        return obj


class TicketStatus(IntEnum):
    """The status of a ticket."""
    OPEN = 2
    PENDING = 3
    RESOLVED = 4
    CLOSED = 5
    OTHER = 6


@dataclass
class Ticket:
    # Primary Key
    id: int

    # Ticket Properties
    type: str = ""
    source: Optional[int] = None
    status: Optional[TicketStatus] = None
    tags: list[str] = field(default_factory=list)
    priority: Optional[int] = None
    deleted: bool = False
    custom_fields: dict = field(default_factory=dict)

    # User/Email
    name: str = ""
    phone: str = ""
    email: str = ""

    support_email: Optional[str] = None
    associated_tickets_count: Optional[int] = None

    nr_due_by: Optional[datetime] = None
    nr_escalated: bool = False

    subject: str = ""
    attachments: list[Attachment] = field(default_factory=list)
    to_emails: list[str] = field(default_factory=list)
    cc_emails: list[str] = field(default_factory=list)
    ticket_cc_emails: list[str] = field(default_factory=list)
    reply_cc_emails: list[str] = field(default_factory=list)
    fwd_emails: list[str] = field(default_factory=list)
    description: str = ""
    description_text: str = ""

    # Foreign Keys
    email_config_id: Optional[int] = None

    company_id: Optional[int] = None
    group_id: Optional[int] = None
    product_id: Optional[int] = None
    requester_id: Optional[int] = None
    responder_id: Optional[int] = None

    twitter_id: str = ""
    facebook_id: str = ""
    form_id: Optional[int] = None

    # Datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    due_by: Optional[datetime] = None

    fr_due_by: Optional[datetime] = None

    # Bools
    fr_escalated: bool = False
    is_escalated: bool = False
    spam: bool = False

    # Other Fields
    urgent: bool = False
    association_type: Optional[int] = None
    # List of ids for associated tickets
    associated_tickets_list: list[int] = field(default_factory=list)
    source_additional_info: Optional[None] = None

    _json: Optional[dict] = field(default=None, repr=False)

    # Any extra arguments should be put in here.
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data) -> Ticket:
        copied = deepcopy(data)

        # Extras
        copied["extras"] = {}
        for key in list(copied.keys()):
            if key not in cls.__dataclass_fields__:
                copied["extras"][key] = copied.pop(key)

        obj = cls(**copied)

        # Parse datetime strings into datetime objects
        for attr in ["created_at", "updated_at", "due_by", "fr_due_by"]:
            if copied.get(attr):
                setattr(obj, attr, datetime.fromisoformat(copied[attr][:-1]))
        # Parse Status
        if copied.get("status"):
            obj.status = TicketStatus(copied["status"])
        # Parse Attachments
        if copied.get("attachments"):
            obj.attachments = [
                Attachment.from_json(a) for a in copied["attachments"]
            ]

        obj._json = data

        return obj

    def to_json(self):
        raise NotImplementedError(f"{self} is not yet JSON serializable.")

    def __hash__(self):
        return hash(self.id)


@dataclass
class TicketConversation:
    """Conversational item for a ticket. Can be a Note or Reply."""

    id: int
    ticket_id: int
    user_id: int
    thread_id: Optional[int]
    thread_message_id: Optional[int]
    automation_id: Optional[int]
    automation_type_id: Optional[int]
    source: int
    source_additional_info: None  # What is this?
    category: int  # What is this?

    body: str
    body_text: str

    to_emails: list[str]
    cc_emails: list[str]
    bcc_emails: Optional[list[str]]
    from_email: Optional[str]
    support_email: Optional[str]

    attachments: list[Attachment]

    incoming: bool
    private: bool
    auto_response: bool

    email_failure_count: Optional[int]
    outgoing_failures: Optional[int]

    created_at: datetime
    updated_at: datetime
    last_edited_at: Optional[datetime]
    last_edited_user_id: Optional[int]

    _json: Optional[dict] = field(default=None, repr=False)

    @classmethod
    def from_json(cls, data):
        obj = cls(**data)
        obj._json = data
        return obj


@dataclass
class CannedResponseFolder:
    """A Freshdesk _Folder_ of Canned Responses."""

    id: int
    name: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    personal: Optional[bool] = None
    responses_count: Optional[int] = None
    canned_responses: Optional[list[CannedResponse]] = field(
        default=None, repr=False
    )

    def __len__(self) -> int:
        return self.responses_count if self.responses_count is not None else len(self.canned_responses)  # type: ignore

    @classmethod
    def from_json(cls, data) -> CannedResponseFolder:
        # Parse Datetimes
        for key in ("created_at", "updated_at"):
            if data.get(key):
                data[key] = datetime.fromisoformat(data[key][:-1])

        obj = cls(**data)
        obj._json = data  # type: ignore

        if data.get("canned_responses"):
            obj.canned_responses = [
                CannedResponse.from_json(canned_response)
                for canned_response in data.get("canned_responses")
            ]

        return obj

    def to_json(self) -> dict:
        return self._json


class CannedResponseVisibility(enum.IntEnum):
    """Visibility of a Canned Response."""

    ALL_AGENTS = 0
    PERSONAL = 1
    SELECT_GROUPS = 2


@dataclass
class CannedResponse:
    """Canned Response in Freshdesk.

    This is like a code snippet, but for a support ticket.

    There's a simple version, supplied by the Canned Response Folder API that
    only provides the ID and title.
    """

    id: int
    title: str

    content: str = field(repr=False)
    content_html: str = field(repr=False)

    responses_count: Optional[int] = None
    folder_id: Optional[int] = None
    # Groups for which the canned response is visible. Use only if visibility
    # is set to 2.
    group_ids: Optional[list[int]] = None
    visibility: Optional[CannedResponseVisibility] = None

    personal: Optional[bool] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    attachments: list[Attachment] = field(default_factory=list)

    _json: Optional[dict] = field(default=None, repr=False)

    @classmethod
    def from_json(cls, data: dict):
        # Parse Datetimes
        for key in ["created_at", "updated_at"]:
            if data.get(key):
                data[key] = datetime.fromisoformat(data[key][:-1]).astimezone(
                    timezone.utc
                )

        if data.get("visibility"):
            data["visibility"] = CannedResponseVisibility(data["visibility"])

        if data.get("attachments"):
            data["attachments"] = [
                Attachment.from_json(attachment)
                for attachment in data.get("attachments", [])
            ]

        obj = cls(**data)
        obj._json = data
        return obj

    def to_json(self) -> dict[Any, Any]:
        return self._json


@dataclass
class TicketField:
    id: int
    name: str
    type: Optional[str] = None
    description: str = ""
    label: Optional[str] = None
    position: Optional[int] = None

    portal_cc: Optional[bool] = None
    portal_cc_to: Optional[list[str]] = None

    choices: Optional[list[str]] = None
    dependent_fields: None = None
    section_mappings: None = None

    default: Optional[bool] = None
    archived: Optional[bool] = None
    has_section: Optional[bool] = None
    is_fsm: Optional[bool] = None
    field_update_in_progress: Optional[bool] = None

    displayed_to_customers: Optional[bool] = None
    customers_can_edit: Optional[bool] = None
    label_for_customers: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    required_for_closure: bool = False
    required_for_agents: bool = False
    required_for_customers: bool = False

    def __post_init__(self):
        signature = inspect.signature(self.__init__)
        default_values = {
            key: value.default for key, value in signature.parameters.items()
        }

        logger.info(
            f'{self.__class__.__name__} __init__() missing {len(default_values)} required positional arguments: {", ".join(default_values.keys())}'
        )  # noqa: 501

        for key, value in default_values.items():
            if getattr(self, key) is None:
                logger.info(
                    f"{self.__class__.__name__} __init__() has None for {key} with default value {value}."  # noqa: 501
                )


CustomFieldName = str
CustomFieldValue = Union[str, int, bool]


@dataclass
class TicketFilter:
    """

    [Documentation](https://developers.freshdesk.com/api/#filter_tickets)


    Paramaters
    -----
    custom_fields: Optional[dict[CustomFieldName, CustomFieldValue]]
        Single line text: string
        Number: integer
        Checkbox: boolean
        Dropdown: string
    
    Specs
    -----

    * Archived tickets are not included.
    * Dates: YYYY-MM-DD (UTC)
    * Must be URL Encoded - e.g. ' ' -> '%20'
    * <= 512 characters, including surrounding double quotes

    Types
    =====

    * null
    * string
    * integer
    * boolean
    * date (YYYY-MM-DD)
        * surrounded by single quotes
        * e.g. '2018-01-01'

    Operators
    =========

    Logical Operators

    * `AND`
    * `OR`
    * `(...)`

    Relational Operators

    `:`
    : Equals

    `:>`
    : Greater than
    : date and numeric ONLY

    `:<`
    : Less than
    : date and numeric ONLY

    Returns
    -------

    Up to 30 tickets with appropriate pagination infromation

    Prototype
    ---------

    >>> from pyfreshdesk.filters import Field

    >>> ticket_filter = TicketFilter(...)

    >>> field_1 = Field(agent_id=None)
    "agent_id:null"

    >>> field_1 = Field(agent_id=1)
    >>> field_2 = Field(created_at='2021-11-09')
    >>>
    >>> field_1 & field_2
    "agent_id:1 AND created_at:'2021-11-09'"

    >>> field_1 = Field(agent_id=1)
    >>> field_2 = Field(created_at='2021-11-09')
    >>> field_3 = Field(created_at='2020-09-08')
    >>>
    >>> Parenthesize(field_1 & field_2) | field_3
    "(agent_id:1 AND created_at:'2021-11-09') OR created_at:'2020-09-08'"

    """

    agent_id: Optional[int] = None
    group_id: Optional[int] = None
    priority: Optional[int] = None
    status: Optional[int] = None
    tag: Optional[str] = None
    type: Optional[str] = None
    due_by: Optional[date] = None
    fr_due_by: Optional[date] = None
    created_at: Optional[date] = None
    updated_at: Optional[date] = None

    custom_fields: Optional[dict[CustomFieldName, CustomFieldValue]] = None


class Field:
    """A single field to filter on."""

    DATE_FORMAT = "%Y-%m-%d"

    supported_types = (type(None), str, int, bool, date)

    builtin_field_types = {
        "agent_id": int,
        "group_id": int,
        "priority": int,
        "status": int,
        "tag": str,
        "type": str,
        "due_by": date,
        "fr_due_by": date,
        "created_at": date,
        "updated_at": date,
    }

    def __init__(self, **kwargs):
        self._validate_kwargs(kwargs)

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        # agent_id:1
        kwargs = {
            key: getattr(self, key)
            for key in vars(self)
            if not key.startswith("_")
        }
        self._validate_kwargs(kwargs)

        key = list(kwargs.keys())[0]
        value = self._resolve_value(list(kwargs.values())[0])

        return f"{key}:{value}"

    def __and__(self, other):
        return f"{self!s} {LogicalOperator.AND!s} {other!s}"

    def __or__(self, other):
        return f"{self!s} {LogicalOperator.OR!s} {other!s}"

    def _validate_kwargs(self, kwargs):
        # 1 key:value pair only
        self._validate_kwargs_length(kwargs)
        self._validate_kwargs_type(kwargs)

        # Validate Type

    def _validate_kwargs_length(self, kwargs):
        # Specific Supported Types
        if len(kwargs) > 1 or len(kwargs) == 0:
            raise ValueError(
                f"{self.__class__.__name__} requires one field. Got {len(kwargs)}."  # noqa: 501
            )

    def _validate_kwargs_type(self, kwargs):
        logger.info(f"Validating kwargs type: {kwargs=}.")
        key = list(kwargs.keys())[0]
        value = list(kwargs.values())[0]

        # All Supported Types
        if not isinstance(value, self.supported_types):
            raise TypeError(
                f"{self.__class__.__name__} requires a string, integer, boolean, or date. Got {type(value)}."  # noqa: 501
            )

        # Built-In Supported Types
        if key in self.builtin_field_types:
            if not isinstance(
                value, (self.builtin_field_types[key], type(None))
            ):
                raise TypeError(
                    f"{self.__class__.__name__} requires a {self.builtin_field_types[key]}. Got {type(value)}."  # noqa: 501
                )

    def _resolve_value(self, value):
        """Will try to convert value to appropriate format/type."""

        if value is None:
            return "null"

        if isinstance(value, date):
            return "'" + value.strftime(self.DATE_FORMAT) + "'"

        return value


class Parenthesize:
    def __call__(self, arguments):
        return f"({arguments})"


@dataclass
class Product:
    """A Freshdesk Product."""

    id: int
    name: str
    description: str
    primary_email: str
    created_at: date
    updated_at: date

    @classmethod
    def from_json(cls, data):
        obj = cls(**data)
        return obj


@dataclass
class Group:
    """A Freshdesk Group."""

    id: int
    business_hour_id: int
    name: str  # unique
    created_at: date
    updated_at: date

    group_type: str = ""
    agent_ids: list[int] = field(default_factory=list)
    auto_ticket_assign: int = 0
    description: str = ""
    escalate_to: Optional[int] = None

    unassigned_for: TimeDeltaString = ""

    @classmethod
    def from_json(cls, data):
        obj = cls(**data)
        return obj


class SolutionCategoryPayload(TypedDict):
    """Used to create or update a solution category using the API."""

    name: str
    description: Optional[str]
    visible_in_portals: Optional[list[int]]  # List of portal IDs


@dataclass
class SolutionCategory:
    """Solutions: A Freshdesk Category.

    Categories broadly classify your solutions page into several sections.
    """

    id: int  # unique
    name: str
    description: Optional[str]
    visible_in_portals: list[int]  # portal_ids
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_json(cls, data):
        obj = cls(**data)
        return obj


class SolutionFolderPayload(TypedDict):
    """Used to create or update a solution folder using the API."""

    name: str
    visibility: SolutionFolderVisibility
    description: Optional[str]
    parent_folder_id: Optional[int]
    company_ids: Optional[list[int]]
    contact_segment_ids: Optional[list[int]]
    company_segment_ids: Optional[list[int]]


@dataclass
class SolutionFolder:
    """Solutions: A Freshdesk Folder.

    Related Solutions Articles are organized into Folders.
    """

    id: int  # unique
    category_id: int
    name: str
    description: str
    visibility: SolutionFolderVisibility
    created_at: datetime
    updated_at: datetime
    articles_count: int

    company_ids: list[int] = field(default_factory=list)
    contact_segment_ids: list[int] = field(default_factory=list)
    company_segment_ids: list[int] = field(default_factory=list)

    @classmethod
    def from_json(cls, data):
        obj = cls(**data)
        return obj


class SolutionArticlePayload(TypedDict):
    """Used to create or update a solution article using the API.

    Doesn't _require_ anything when updating an article.
    """

    title: str
    description: str
    status: SolutionArticleStatus
    tags: Optional[list[str]]
    seo_data: Optional[dict]  # meta_title, meta_description, meta_keywords


@dataclass
class SolutionArticle:
    """Solutions: A Freshdesk Article.

    WARNING: There is a large difference between create/update and search
    results.
    """

    id: int  # unique
    type: int
    status: SolutionArticleStatus

    category_id: int
    folder_id: int
    agent_id: int  # Author/Creator

    title: str
    description: str = field(repr=False)
    description_text: str = field(repr=False)

    created_at: datetime

    collaboration: dict = field(default_factory=dict)

    hits: Optional[int] = None
    thumbs_up: Optional[int] = None
    thumbs_down: Optional[int] = None
    suggested: Optional[int] = None
    feedback_count: Optional[int] = None

    # Meta Data for SEO: meta_title, meta_description, meta_keywords
    seo_data: Optional[dict] = None  # noqa: 501
    attachments: Optional[list[Attachment]] = None
    cloud_files: Optional[list] = None

    tags: Optional[list[str]] = None
    folder_visibility: Optional[SolutionFolderVisibility] = None
    path: Optional[str] = None  # Path of the URL (e.g. 123456-article-title)
    modified_at: Optional[datetime] = None  # '2023-03-13T16:09:22Z'
    modified_by: Optional[int] = None  # UserID
    updated_at: Optional[datetime] = None  # '2023-03-13T16:09:22Z'
    language_id: Optional[int] = None  # Language ID
    language: Optional[str] = None  # e.g. 'en'
    category_name: Optional[str] = None
    folder_name: Optional[str] = None

    # Custom
    _json: Optional[dict] = field(default=None, repr=False)

    @classmethod
    def from_json(cls, data):
        # Parse Datetime strings
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(
                data["created_at"][:-1]
            ).astimezone(timezone.utc)
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(
                data["updated_at"][:-1]
            ).astimezone(timezone.utc)
        if data.get("modified_at"):
            data["modified_at"] = datetime.fromisoformat(
                data["modified_at"][:-1]
            ).astimezone(timezone.utc)

        # Convert SolutionArticleStatus
        data["status"] = SolutionArticleStatus(int(data["status"]))

        obj = cls(**data)
        obj._json = data
        return obj


@dataclass
class Contact:
    """A Freshdesk Contact."""

    active: bool
    email: str
    job_title: Optional[str]
    language: str  # Literal['en', ...]
    last_login_at: datetime
    mobile: Optional[str]  # Phone Number
    name: str
    phone: Optional[str]  # Phone Number
    time_zone: str  # Literal['Central Time (US & Canada)', ...]
    created_at: datetime
    updated_at: datetime

    avatar: Optional[dict] = None

    _json: Optional[dict] = field(default=None, repr=False)

    @classmethod
    def from_json(cls, data):
        obj = cls(**data)
        obj._json = data
        return obj


@dataclass
class Agent:
    """A Freshdesk Agent."""

    available: bool
    available_since: datetime
    id: int  # unique
    occasional: bool  # True: occasional, False: full-time
    signature: str  = field(repr=False)  # HTML
    ticket_scope: int  # Permissions: 1 - Global, 2 - Group, 3 - Restricted
    # support_agent -> Support Agent
    # field_agent -> Field Agent
    # collaborator -> Collaborator
    type: str
    created_at: datetime
    updated_at: datetime
    last_active_at: datetime
    contact: Contact

    freshcaller_agent: bool

    # Skill IDs
    skill_ids: list[int] = field(default_factory=list)
    # Group IDs
    group_ids: list[int] = field(default_factory=list)
    # Role IDs
    role_ids: list[int] = field(default_factory=list)

    _json: Optional[dict] = field(default=None, repr=False)

    # Any extra arguments get put in here.
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Agent:
        copied_data = deepcopy(data)

        # Parse Data Structures
        copied_data["contact"] = Contact.from_json(data["contact"])

        # Remove any keys that are not in the dataclass, putting them into extras
        extras: dict[str, Any] = {}
        for key in list(copied_data.keys()):
            if key not in cls.__dataclass_fields__:
                extras[key] = copied_data.pop(key)

        obj = cls(**copied_data, extras=extras)
        obj._json = data

        return obj

    def __hash__(self):
        return hash(self.id)


@dataclass
class Event:
    """

    Parameters
    ----------
    field_name : str
        Name of the field.
    from_ : str
        Value of the field before the event.
    to : str
        Value of the field after the event.
    """

    field_name: str
    from_: str
    to: str

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Event:
        # We cannot use keywords as attribute names.
        data["from_"] = data.pop("from")
        return cls(**data)

    def to_json(self) -> dict[str, Any]:
        data = self.__dict__
        data["from"] = data.pop("from_")
        return data


class PerformerType(IntEnum):
    """
    enum of PerformerType
    1- Agent
    2- Requester
    3- Agent or Requester
    4- System
    """

    AGENT = 1
    REQUESTER = 2
    AGENT_OR_REQUESTER = 3
    SYSTEM = 4


@dataclass
class Performer:
    """

    Parameters
    ----------
    type : PerformerType
        The type of performer
    members : Optional[list[str]], optional
        Only applicable if type is PerformerType.Agent
        IDs of the agents
    """

    type: PerformerType
    members: Optional[list[str]] = None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Performer:
        obj = cls(**data)
        return obj

    def to_json(self) -> dict[str, Any]:
        data = self.__dict__
        return data


class ConditionMatchType(Enum):
    ALL = "all"
    ANY = "any"

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)


class PropertyResourceType(Enum):
    """Resoure type for a Property for a Condition.

    contacts, tickets, companies, custom_object
    """

    CONTACTS = "contacts"
    TICKETS = "tickets"
    COMPANIES = "companies"
    CUSTOM_OBJECT = "custom_object"

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)


class Operator(Enum):
    """An AND/OR operator for a Property.

    True - AND
    False - OR
    """

    AND = True
    OR = False

    def __bool__(self) -> bool:
        return self.value

    def __eq__(self, other):
        if isinstance(other, bool):
            return self.value == other
        return super().__eq__(other)


@dataclass
class Property:
    """Propery of a Condition.

    resource_type : str
        Type of the resource.
    field_name : str
        Name of the field.
    operator : bool
        AND/OR operator to combine multiple conditions in a rule.
    value : str
        Value sest on the selected field.
    object_reference : str
        Ticket's look up field value.
    """

    resource_type: PropertyResourceType
    field_name: str
    operator: Operator
    value: str
    object_reference: str

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Property:
        obj = cls(**data)
        return obj


@dataclass
class Condition:
    name: str
    match_type: ConditionMatchType
    properties: list[Property]


class AutomationRuleActionResourceType(Enum):

    SAME_TICKET = "Same_ticket"
    PARENT_TICKET = "parent_ticket"
    TRACKER_TICKET = "tracker_ticket"
    CUSTOM_OBJECT = "custom_object"

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)


class PushToType:
    """Channel which the message should be sent with."""

    SLACK = "Slack"
    OFFICE = "Office365"

    def __str__(self) -> str:
        return self.value  # type: ignore


@dataclass
class AutomationRuleAction:
    field_name: str
    value: str
    email_to: int
    email_body: str
    api_key: str
    auth_header: str
    custom_headers: str
    request_type: str
    url: str
    note_body: str
    notify_agents: list[int]  # Agent IDs
    fwd_to: str
    fwd_cc: str
    fwd_bcc: str
    fwd_note_body: str
    push_to: PushToType
    slack_text: str
    office365_text: str
    resource_type: AutomationRuleActionResourceType
    object_reference: str


class AutomationRuleType(IntEnum):
    TICKET_CREATION = 1
    TIME_TRIGGERS = 3
    TICKET_UPDATES = 4


@dataclass
class AutomationRule:
    """A Freshdesk Automation Rule.

    Parameters
    ----------
    outdated : bool
        Whether the rule is outdated or not. The automation service gets
        changed over time and may make older ruled outdated. These get updated
        after editing and saving.
    last_updated_by : int
        ID of the agent who last updated the rule.
    id : int
        ID of the rule.
    summary : dict
        A summary of the rule. Keys include 'conditions' and 'actions'.
    created_at : datetime
    updated_at : datetime
    affected_tickets_count : int
        Number of tickets affected by the rule, in the given time frame (7
        days).
    meta : dict
        Found when using `view` endpoint.
        total_active_count: int
        total_count: int
    """

    id: int
    position: int
    name: str
    summary: dict[str, Any] = field(repr=False)
    active: bool
    outdated: bool
    last_updated_by: int
    created_at: datetime
    updated_at: datetime
    affected_tickets_count: int
    conditions: list[Condition] = field(repr=False)
    actions: list[AutomationRuleAction] = field(repr=False)

    operator: str = ""
    performer: list[Performer] = field(default_factory=list)
    events: list[str] = field(default_factory=list, repr=False)
    # Some interfaces don't include this
    automation_type_id: Optional[AutomationRuleType] = None
    meta: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def type(self) -> Optional[AutomationRuleType]:
        """Get the automation type."""
        return self.automation_type_id

    @type.setter
    def type(self, value: AutomationRuleType) -> None:
        """Set the automation type."""
        self.automation_type_id = value

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> AutomationRule:
        # Copy Data to avoid mutating the original
        data = data.copy()
        # Parse datetimes
        data["created_at"] = datetime.fromisoformat(
            data["created_at"][:-1]
        ).astimezone(timezone.utc)
        data["updated_at"] = datetime.fromisoformat(
            data["updated_at"][:-1]
        ).astimezone(timezone.utc)
        obj = cls(**data)
        return obj

    def to_json(self) -> dict[str, Any]:
        data = self.__dict__
        # Serialize datetimes
        data["created_at"] = data["created_at"].isoformat()[:-6] + "Z"
        data["updated_at"] = data["updated_at"].isoformat()[:-6] + "Z"
        # Serialize enums
        data["automation_type_id"] = int(data["automation_type_id"])
        return data


@dataclass
class ScenarioAutomationAction:
    """An action to be performed by an automation rule."""

    name: str
    value: Optional[str] = None


@dataclass
class ScenarioAutomation:
    id: int
    name: str
    description: str
    actions: list[ScenarioAutomationAction] = field(repr=False)
    private: bool

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ScenarioAutomation:
        # Copy Data to avoid mutating the original
        data = data.copy()

        # Parse Actions
        actions = []
        for action in data["actions"]:
            actions.append(ScenarioAutomationAction(**action))

        obj = cls(**data)
        return obj

