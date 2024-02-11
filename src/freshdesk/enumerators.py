from enum import auto
from enum import Enum
from enum import IntEnum
from types import SimpleNamespace


class RelationalOperator(Enum):
    EQUALS = ":"
    # date and numeric ONLY
    GREATER_THAN = ":>"
    # date and numeric ONLY
    LESS_THAN = ":<"


class LogicalOperator(Enum):
    AND = "AND"
    OR = "OR"

    def __str__(self):
        return self.value


class APIVersion(IntEnum):
    V1 = auto()
    V2 = auto()

    def __init__(self, value):
        self.path = f"/v{value}"


class HTTPRequestMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class Plan(Enum):
    BLOSSOM = dict(
        per_minute=100,
        ticket_create=40,
        ticket_update=40,
        ticket_list=40,
        contacts_list=40,
    )

    GARDEN = dict(
        per_minute=200,
        ticket_create=80,
        ticket_update=60,
        ticket_list=60,
        contacts_list=60,
    )

    ESTATE = dict(
        per_minute=400,
        ticket_create=160,
        ticket_update=160,
        ticket_list=100,
        contacts_list=100,
    )

    FOREST = dict(
        per_minute=700,
        ticket_create=280,
        ticket_update=280,
        ticket_list=200,
        contacts_list=200,
    )

    def __init__(self, value):
        self.rates = SimpleNamespace(**self.value)


class Resource(Enum):
    TICKET = "/tickets"
    TICKET_FIELDS = "/admin/ticket_fields"


class TicketSource(IntEnum):
    EMAIL = 1
    PORTAL = 2
    PHONE = 3
    CHAT = 7
    FEEDBACK_WIDGET = 9
    OUTBOUND_EMAIL = 10


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class AssociationType(IntEnum):
    PARENT = 1
    CHILD = 2
    TRACKER = 3
    RELATED = 4


class ConversationSource(IntEnum):
    REPLY = 0
    NOTE = 2
    TWEETS = 5
    SURVEY_FEEDBACK = 6
    FACEBOOK = 7
    FORWARDED_EMAIL = 8
    PHONE = 9
    ECOMMERCE = 11


class SolutionFolderVisibility(IntEnum):
    """Visibliity of a Folder resource, related to Solutions."""

    ALL_USERS = 1
    LOGGED_IN_USERS = 2
    AGENTS = 3
    SELECTED_COMPANIES = 4
    BOTS = 5
    SELECTED_CONTACT_SEGMENTS = 6
    SELECTED_COMPANY_SEGMENTS = 7


class SolutionArticleStatus(IntEnum):
    """Article Status, related to Solutions."""

    DRAFT = 1
    PUBLISHED = 2
