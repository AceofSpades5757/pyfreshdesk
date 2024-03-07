import logging.config

from freshdesk.api import AgentAPI
from freshdesk.api import AutomationAPI
from freshdesk.api import CannedResponseAPI
from freshdesk.api import CannedResponseExtendedAPI
from freshdesk.api import CannedResponseFolderAPI
from freshdesk.api import GroupAPI
from freshdesk.api import ProductAPI
from freshdesk.api import ScenarioAutomationsAPI
from freshdesk.api import SearchResults
from freshdesk.api import SolutionAPI
from freshdesk.api import TicketAPI
from freshdesk.api import TicketFieldAPI
from freshdesk.client import LimitInfo
from freshdesk.client import UnregisteredClient
from freshdesk.constants import MAX_PAGES
from freshdesk.constants import MAX_SEARCH_RESULTS
from freshdesk.constants import RE_FRESHDESK_ARTICLE_URL
from freshdesk.constants import RESULTS_PER_PAGE
from freshdesk.errors import AuthenticationError
from freshdesk.errors import DraftLockedError
from freshdesk.errors import NotFoundError
from freshdesk.logger import get_config
from freshdesk.models import Agent
from freshdesk.models import AutomationRule
from freshdesk.models import AutomationRuleType
from freshdesk.models import CannedResponse
from freshdesk.models import CannedResponseFolder
from freshdesk.models import Field
from freshdesk.models import Group
from freshdesk.models import Product
from freshdesk.models import ScenarioAutomation
from freshdesk.models import SolutionArticle
from freshdesk.models import SolutionArticlePayload
from freshdesk.models import SolutionArticleStatus
from freshdesk.models import SolutionCategory
from freshdesk.models import SolutionCategoryPayload
from freshdesk.models import SolutionFolder
from freshdesk.models import SolutionFolderPayload
from freshdesk.models import SolutionFolderVisibility
from freshdesk.models import Ticket
from freshdesk.models import TicketConversation
from freshdesk.models import TicketStatus
from freshdesk.store import LimitStore
from freshdesk.store import SQLiteURI
from freshdesk.utilities import get_agent_by_name
from freshdesk.utilities import get_date_query
from freshdesk.utilities import get_date_range_query
from freshdesk.utilities import get_remaining_search_results
from freshdesk.utilities import get_ticket_agent


# Logging
logging.config.dictConfig(get_config(__file__))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Register API for Client
Client = UnregisteredClient
Client.register_api(TicketAPI)  # type: ignore
Client.register_api(TicketFieldAPI)  # type: ignore
Client.register_api(ProductAPI)  # type: ignore
Client.register_api(GroupAPI)  # type: ignore
Client.register_api(AgentAPI)  # type: ignore
Client.register_api(CannedResponseAPI)  # type: ignore
Client.register_api(CannedResponseFolderAPI)  # type: ignore
Client.register_api(CannedResponseExtendedAPI)  # type: ignore
Client.register_api(AutomationAPI)  # type: ignore
Client.register_api(SolutionAPI)  # type: ignore
Client.register_api(ScenarioAutomationsAPI)  # type: ignore


__all__ = (
    "Agent",
    "CannedResponse",
    "CannedResponseFolder",
    "Field",
    "Group",
    "Product",
    "ScenarioAutomation",
    "Ticket",
    "TicketStatus",
    "TicketConversation",
    "LimitInfo",
    "AutomationRule",
    "AutomationRuleType",
    "RESULTS_PER_PAGE",
    "MAX_PAGES",
    "MAX_SEARCH_RESULTS",
    "RE_FRESHDESK_ARTICLE_URL",
    # Models - Solutions (User Guides)
    "SolutionArticle",
    "SolutionArticlePayload",
    "SolutionArticleStatus",
    "SolutionCategory",
    "SolutionCategoryPayload",
    "SolutionFolder",
    "SolutionFolderPayload",
    "SolutionFolderVisibility",
    # Typing
    "SearchResults",
    # DB Access
    "LimitStore",
    "SQLiteURI",
    # Utilities
    "get_ticket_agent",
    "get_agent_by_name",
    "get_date_query",
    "get_date_range_query",
    "get_remaining_search_results",
    # Exceptions
    "AuthenticationError",
    "DraftLockedError",
    "NotFoundError",
)
