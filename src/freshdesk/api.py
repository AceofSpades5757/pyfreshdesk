"""APIs for Freshdesk."""

import logging.config
from typing import Any
from typing import Literal
from typing import Optional
from typing import TypedDict
from typing import Union

from requests import Response
from requests.exceptions import JSONDecodeError

from freshdesk.base import BaseAPI
from freshdesk.base import register_interface
from freshdesk.enumerators import HTTPRequestMethod
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
from freshdesk.models import SolutionCategory
from freshdesk.models import SolutionCategoryPayload
from freshdesk.models import SolutionFolder
from freshdesk.models import SolutionFolderPayload
from freshdesk.models import Ticket
from freshdesk.models import TicketConversation
from freshdesk.models import TicketField


Identifier = Union[int, str]


class SearchResults(TypedDict):
    """JSON returned by Ticket Search."""

    total: int
    results: list[Ticket]


# Logging
logging.config.dictConfig(get_config(__file__))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


ListAllTicketsFilter = Literal[
    "new_and_my_open", "watching", "spam", "deleted"
]  # type alias
ListAllTicketsSort = Literal[
    "created_at", "updated_at", "due_by", "status"
]  # type alias
ListAllTicketsEmbed = Literal[
    "stats", "requester", "description"
]  # type alias


class TicketAPI(BaseAPI):
    name = "tickets"
    path = "/tickets"

    def view(self, id: Identifier):
        """
        # Use 'include' to embed additional details in response
        # Each include will consume an additional credit.

        Embeds
        -----
        * conversations
        * requester
        * company
        * stats - closed_at, resolved_at, first_responded_at times
        """
        url = self.base_url + f"/{id}"
        response = self._request(url=url, method=HTTPRequestMethod.GET)

        try:
            data = response.json()
        except JSONDecodeError:
            raise NotFoundError(f"Ticket #{id} not found.")
        ticket: Ticket = Ticket.from_json(data)

        return ticket

    @register_interface
    def tickets(
        self,
        filter: Optional[ListAllTicketsFilter] = None,
        sort_by: Optional[ListAllTicketsSort] = None,
        ascending: Optional[bool] = None,
        embed: Optional[ListAllTicketsEmbed] = None,
        # Pagination
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ):
        """List all tickets.

        Parameters
        ----------
        filter : Optional[ListAllTicketsFilter]
            Filter tickets by a predefined filter (per Freshdesk)
        sort_by : Optional[ListAllTicketsSort]
            Sort tickets by a field.
            Default sort order is `created_at` (per Freshdesk)
        ascending : Optional[bool]
            Sort in ascending order.
            Default is descending order (per Freshdesk)
        embed : Optional[ListAllTicketsEmbed]
            Embed additional details in response.
            WARNING: Each include will consume an additional **2** credits.

        Pagination
        ==========
        page : Optional[int]
            The page number to retrieve.
            The default is 1 (per Freshdesk)
        per_page : Optional[int]
            The number of tickets per page.
            The default is 30 (per Freshdesk)
            The max is 100 (per Freshdesk)
        """
        url = self.base_url

        # Options
        if any([filter, sort_by, ascending, embed, page, per_page]):
            url += "?"

        # Options - Base
        if filter:
            url += f"filter={filter}&"
        if sort_by:
            url += f"order_by={sort_by}&"
        if ascending is not None:
            if ascending:
                url += "order_type=asc&"
            else:
                url += "order_type=desc&"
        if embed:
            url += f"include={embed}&"

        # Options - Pagination
        if page:
            url += f"page={page}&"
        if per_page:
            url += f"per_page={per_page}&"

        # Clean Up
        if url.endswith("&"):
            url = url[:-1]

        response = self._request(url, HTTPRequestMethod.GET)

        data = response.json()
        tickets = [Ticket.from_json(ticket_data) for ticket_data in data]

        return tickets

    @register_interface
    def filter_tickets(
        self, query: Optional[Union[str, Field]] = None, page: int = 1
    ) -> SearchResults:
        url = self.client.base_url + "/search" + self.path
        params = {}
        if query is not None:
            # Hotfix for queries already surrounded by quotes
            if str(query)[0] == '"' and str(query)[-1] == '"':
                params = {"query": str(query)}
            else:
                params = {"query": '"' + str(query) + '"'}

        params["page"] = str(page)

        method = HTTPRequestMethod.GET
        response = self._request(url=url, method=method, params=params)

        data: SearchResults = response.json()
        return data

    def list_conversations(self, ticket_id: int) -> list[TicketConversation]:
        url: str = (
            self.client.base_url
            + self.path
            + f"/{ticket_id}"
            + "/conversations"
        )
        response = self._request(method="GET", url=url)
        json_: list[dict[str, Any]] = response.json()
        conversations = [TicketConversation.from_json(c) for c in json_]

        return conversations

    def update_ticket_(self, ticket_id: int, data: dict[str, Any]) -> Ticket:
        """Update a ticket based on ID and data.

        For custom fields, use the following format:

            self.update_ticket(ticket.id, {'custom_fields': {'cf_issue_area': None}})
        """
        url = self.base_url + f"/{ticket_id}"
        method = HTTPRequestMethod.PUT
        headers = {"Content-Type": "application/json"}
        response = self._request(
            url=url, method=method, json=data, headers=headers
        )

        data = response.json()
        data["id"] = ticket_id
        updated_ticket: Ticket = Ticket.from_json(data)

        return updated_ticket

    @register_interface
    def update_ticket(self, ticket_id: int, data: dict[str, Any]) -> Ticket:
        """Update a ticket based on ID and data."""
        return self.update_ticket_(ticket_id, data)

    @register_interface
    def ticket(self, ticket_id: int) -> Ticket:
        logging.info(f"Getting ticket #{ticket_id}.")
        return self.view(ticket_id)


class TicketFieldAPI(BaseAPI):
    name = "ticket_fields"
    path = "/admin/ticket_fields"

    def list_all(self):
        logger.info("Getting all ticket fields.")

        uri = self.base_url
        url = uri
        method = HTTPRequestMethod.GET
        response = self._request(url=url, method=method)
        data = response.json()
        logger.info("Getting all ticket fields.")
        ticket_fields = []
        for field in data:
            logger.info(f"Iterating with {field}.")
            ticket_fields.append(TicketField(**field))

        return ticket_fields

    @register_interface
    def ticket_fields(self) -> list[TicketField]:
        return self.list_all()


class ProductAPI(BaseAPI):
    """API for Products."""

    name = "products"
    path = "/products"

    def list_all(self) -> list[Product]:
        """List all Products."""
        url = self.base_url
        response = self._request(url, HTTPRequestMethod.GET)

        data = response.json()
        products: list[Product] = [
            Product.from_json(product_data) for product_data in data
        ]

        return products


class GroupAPI(BaseAPI):
    """API for Groups."""

    name = "groups"
    path = "/groups"

    def list_all(self) -> list[Group]:
        """List all Groups."""
        url = self.base_url
        response = self._request(url, HTTPRequestMethod.GET)

        data = response.json()
        groups: list[Group] = [
            Group.from_json(group_data) for group_data in data
        ]

        return groups


class AgentAPI(BaseAPI):
    """API for Agents."""

    name = "agents"
    path = "/agents"

    def list_all(self) -> list[Agent]:
        """List all Agents."""
        url = self.base_url
        method = HTTPRequestMethod.GET
        response = self._request(method=method, url=url)

        data = response.json()
        groups: list[Agent] = [
            Agent.from_json(agent_data) for agent_data in data
        ]

        return groups

    @register_interface
    def agents(self) -> list[Agent]:
        return self.list_all()


class CannedResponseAPI(BaseAPI):
    """API for Canned Responses."""

    name = "canned_responses"
    path = "/canned_responses"

    def view(self, id: Identifier) -> CannedResponse:
        """View a Canned Response."""
        url = self.base_url + f"/{id}"
        response = self._request(method=HTTPRequestMethod.GET, url=url)

        data = response.json()
        canned_response: CannedResponse = CannedResponse.from_json(data)

        return canned_response

    def update(
        self, id: Identifier, payload: dict[str, Any]
    ) -> CannedResponse:
        """Update a Canned Response."""
        url = self.base_url + f"/{id}"
        response = self._request(
            method=HTTPRequestMethod.PUT, url=url, json=payload
        )

        data = response.json()
        canned_response: CannedResponse = CannedResponse.from_json(data)

        return canned_response

    @register_interface
    def canned_response(self, id: Identifier) -> CannedResponse:
        return self.view(id)

    @register_interface
    def update_canned_response(
        self, id: Identifier, payload: dict[str, Any]
    ) -> CannedResponse:
        return self.update(id, payload)


class CannedResponseFolderAPI(BaseAPI):
    """API for Canned Response Folders."""

    name = "canned_response_folders"
    path = "/canned_response_folders"

    def list_all(self) -> list[CannedResponseFolder]:
        """List all Canned Response Folders."""

        url = self.base_url
        method = HTTPRequestMethod.GET
        response = self._request(method=method, url=url)

        data = response.json()
        canned_response_folders: list[CannedResponseFolder] = [
            CannedResponseFolder.from_json(folder_data) for folder_data in data
        ]

        return canned_response_folders

    def view(self, id: Identifier) -> CannedResponseFolder:
        """View a Canned Response Folder in a simple form."""

        logger.info(f"Getting Canned Response Folder #{id}.")
        url = self.base_url + f"/{id}"
        response = self._request(method=HTTPRequestMethod.GET, url=url)

        data = response.json()
        canned_response_folder: CannedResponseFolder = (
            CannedResponseFolder.from_json(data)
        )

        return canned_response_folder

    def view_canned_responses(self, id: Identifier) -> list[CannedResponse]:
        """View the canned responses in a Canned Response Folder."""

        url = self.base_url + f"/{id}/responses"
        response = self._request(method=HTTPRequestMethod.GET, url=url)

        data = response.json()
        canned_responses: list[CannedResponse] = [
            CannedResponse.from_json(canned_response_data)
            for canned_response_data in data
        ]

        return canned_responses

    @register_interface
    def canned_response_folder(self, id: Identifier) -> CannedResponseFolder:
        return self.view(id)

    @register_interface
    def canned_response_folders(self) -> list[CannedResponseFolder]:
        return self.list_all()

    @register_interface
    def canned_responses(self, folder_id: Identifier) -> list[CannedResponse]:
        return self.view_canned_responses(folder_id)


class CannedResponseExtendedAPI(BaseAPI):
    """Custom extension for the Canned Response and Canned Response Folder APIs.

    Utilizes APIs from CannedResponseAPI and CannedResponseFolderAPI.
    """

    name = "canned_response_extended"

    @register_interface
    def all_canned_responses(self) -> list[CannedResponse]:
        """List all Canned Responses in all Canned Response Folders.

        Uses (1 + n) API calls, where n is the number of Canned Response
        Folders.
        """

        canned_response_folders: list[CannedResponseFolder] = self.client.api.canned_response_folders.canned_response_folders()  # type: ignore
        canned_responses: list[CannedResponse] = []
        folder: CannedResponseFolder
        for folder in canned_response_folders:
            canned_responses += self.client.api.canned_response_folders.canned_responses(folder.id)  # type: ignore

        return canned_responses


class AutomationAPI(BaseAPI):
    """API for Automations."""

    name = "automations"
    path = "/automations"

    def list_all(
        self, type: AutomationRuleType, page: int = 1
    ) -> list[AutomationRule]:
        """List all Automation Rules by type.

        WARNING: There is an undocumented ?page= query parameter that
        paginates the list by 30.
        """

        url = self.base_url + f"/{int(type)}/rules"
        url += f"?page={page}"
        method = HTTPRequestMethod.GET
        response = self._request(method=method, url=url)

        data = response.json()
        rules: list[AutomationRule] = []
        rule_data: dict[str, Any]
        for rule_data in data:
            rule: AutomationRule = AutomationRule.from_json(rule_data)
            # Fix missing type
            rule.type = type
            rules.append(rule)

        return rules

    def view(self, id: Identifier, type: AutomationRuleType) -> AutomationRule:
        """View an Automation Rule."""

        logger.info(f"Getting automation rule for #{id} of type {type}")
        url = self.base_url + f"/{int(type)}/rules/{id}"
        response = self._request(method=HTTPRequestMethod.GET, url=url)

        data = response.json()
        automation_rule: AutomationRule = AutomationRule.from_json(data)
        # Fix missing type
        automation_rule.type = type

        return automation_rule

    def update(
        self, id: Identifier, type: AutomationRuleType, payload: dict[str, Any]
    ) -> AutomationRule:
        """Update an Automation Rule.

        Parameters
        ----------
        id : Identifier
        type : AutomationRuleType
        payload : dict[str, Any]
            These are the changes you'll be making.
            For example, give `{"name": "New Name"}` to change the name.
        """

        logger.info(f"Updating automation rule for #{id} of type {type}")

        url = self.base_url + f"/{int(type)}/rules/{id}"
        method = HTTPRequestMethod.PUT
        response = self._request(method=method, url=url, json=payload)

        if response.status_code != 200:
            raise Exception(
                f"Failed to update automation rule #{id} of type {type}: {response.text}"
            )

        data = response.json()
        automation_rule: AutomationRule = AutomationRule.from_json(data)

        # Fix missing type
        automation_rule.type = type

        return automation_rule

    @register_interface
    def automation(
        self, id: Identifier, type: AutomationRuleType
    ) -> AutomationRule:
        return self.view(id, type)

    @register_interface
    def automations(self) -> list[AutomationRule]:
        """List all automation rules."""
        rules: list[AutomationRule] = []
        for type_ in AutomationRuleType:
            new_rules: list[AutomationRule] = self.list_all(type_)
            rules.extend(new_rules)

            # Paginate
            page: int = 1
            while len(new_rules) == 30:
                page += 1
                new_rules = self.list_all(type_, page=page)
                rules.extend(new_rules)

        return rules

    @register_interface
    def update_automation(
        self, id: Identifier, type: AutomationRuleType, payload: dict[str, Any]
    ) -> AutomationRule:
        return self.update(id, type, payload)


class SolutionAPI(BaseAPI):
    """API for Solutions."""

    name = "solutions"
    path = "/solutions"

    @register_interface
    def create_solution_category(
        self, solution_category_dict: SolutionCategoryPayload
    ) -> SolutionCategory:
        """Create a Solution Category."""

        logger.info(
            "Creating solution category: %s", solution_category_dict["name"]
        )

        url = self.base_url + "/categories"
        method = HTTPRequestMethod.POST
        response = self._request(
            method=method, url=url, json=solution_category_dict
        )

        data: dict = response.json()
        solution_category: SolutionCategory = SolutionCategory.from_json(data)

        return solution_category

    def update_solution_category(
        self, id: Identifier, solution_category_dict: SolutionCategoryPayload
    ) -> SolutionCategory:
        """Update a Solution Category."""
        logger.info(
            "Updating solution category: %s", solution_category_dict["name"]
        )

        url = self.base_url + f"/categories/{id}"
        method = HTTPRequestMethod.PUT
        response = self._request(
            method=method, url=url, json=solution_category_dict
        )

        data: dict = response.json()
        solution_category: SolutionCategory = SolutionCategory.from_json(data)

        return solution_category

    def view_solution_category(self, id: Identifier) -> SolutionCategory:
        """View a Solution Category."""
        logger.info("Viewing solution category: %s", id)

        url = self.base_url + f"/categories/{id}"
        method = HTTPRequestMethod.GET
        response = self._request(method=method, url=url)

        data: dict = response.json()
        solution_category: SolutionCategory = SolutionCategory.from_json(data)

        return solution_category

    def list_all_solution_categories(self) -> list[SolutionCategory]:
        """List all Solution Categories."""

        logger.info("Listing all solution categories")

        url = self.base_url + "/categories"
        method = HTTPRequestMethod.GET
        response = self._request(method=method, url=url)

        data: list[dict] = response.json()
        solution_categories: list[SolutionCategory] = []
        solution_category_data: dict
        for solution_category_data in data:
            solution_category: SolutionCategory = SolutionCategory.from_json(
                solution_category_data
            )
            solution_categories.append(solution_category)

        return solution_categories

    def delete_solution_category(self, id: Identifier) -> None:
        """Delete a Solution Category."""
        logger.info("Deleting solution category: %s", id)

        url = self.base_url + f"/categories/{id}"
        method = HTTPRequestMethod.DELETE
        response = self._request(method=method, url=url)

        if response.status_code != 204:
            raise Exception(
                f"Failed to delete solution category #{id}: {response.text}"
            )

    def create_solution_folder(
        self,
        category_id: Identifier,
        solution_folder_dict: SolutionFolderPayload,
    ) -> SolutionFolder:
        """Create a Solution Folder."""

        logger.info(
            "Creating solution folder: %s", solution_folder_dict["name"]
        )

        url = self.base_url + f"/categories/{category_id}/folders"
        method = HTTPRequestMethod.POST
        response = self._request(
            method=method, url=url, json=solution_folder_dict
        )

        if response.status_code != 201:
            raise Exception(
                f"Failed to create solution folder: {response.text}"
            )

        data: dict = response.json()
        solution_folder: SolutionFolder = SolutionFolder.from_json(data)

        return solution_folder

    def update_solution_folder(
        self, id: Identifier, solution_folder_dict: SolutionFolderPayload
    ) -> SolutionFolder:
        """Update a Solution Folder."""

        logger.info(
            "Updating solution folder: %s", solution_folder_dict["name"]
        )

        url = self.base_url + f"/folders/{id}"
        method = HTTPRequestMethod.PUT
        response = self._request(
            method=method, url=url, json=solution_folder_dict
        )

        data: dict = response.json()
        solution_folder: SolutionFolder = SolutionFolder.from_json(data)

        return solution_folder

    def view_solution_folder(self, id: Identifier) -> SolutionFolder:
        """View a Solution Folder."""
        logger.info("Viewing solution folder: %s", id)

        url = self.base_url + f"/folders/{id}"
        method = HTTPRequestMethod.GET
        response = self._request(method=method, url=url)

        data: dict = response.json()
        solution_folder: SolutionFolder = SolutionFolder.from_json(data)

        return solution_folder

    def list_all_solution_folders(
        self, category_id: Identifier
    ) -> list[SolutionFolder]:
        """List all Solution Folders."""

        logger.info("Listing all solution folders")

        url = self.base_url + f"/categories/{category_id}/folders"
        method = HTTPRequestMethod.GET
        response = self._request(method=method, url=url)

        data: list[dict] = response.json()
        solution_folders: list[SolutionFolder] = []
        solution_folder_data: dict
        for solution_folder_data in data:
            # Fix missing category_id
            solution_folder_data["category_id"] = category_id

            solution_folder: SolutionFolder = SolutionFolder.from_json(
                solution_folder_data
            )
            solution_folders.append(solution_folder)

        return solution_folders

    def list_all_folders_in_folder(
        self, id: Identifier
    ) -> list[SolutionFolder]:
        """List all the Solution Folders found in a Solution Folder."""

        logger.info("Listing all solution folders in folder: %s", id)

        url = self.base_url + f"/folders/{id}/subfolders"
        method = HTTPRequestMethod.GET
        response = self._request(method=method, url=url)

        if response.status_code != 200:
            raise Exception(
                f"Failed to list all solution folders in folder #{id}: {response.text}"
            )

        data: list[dict] = response.json()
        solution_folders: list[SolutionFolder] = []
        solution_folder_data: dict
        for solution_folder_data in data:
            solution_folder: SolutionFolder = SolutionFolder.from_json(
                solution_folder_data
            )
            solution_folders.append(solution_folder)

        return solution_folders

    def delete_solution_folder(self, id: Identifier) -> None:
        """Delete a Solution Folder."""
        logger.info("Deleting solution folder: %s", id)

        url = self.base_url + f"/folders/{id}"
        method = HTTPRequestMethod.DELETE
        response = self._request(method=method, url=url)

        if response.status_code != 204:
            raise Exception(
                f"Failed to delete solution folder #{id}: {response.text}"
            )

    def create_solution_article(
        self,
        folder_id: Identifier,
        solution_article_dict: SolutionArticlePayload,
    ) -> SolutionArticle:
        """Create a Solution Article."""

        logger.info(
            "Creating solution article: %s", solution_article_dict["title"]
        )

        url = self.base_url + f"/folders/{folder_id}/articles"
        method = HTTPRequestMethod.POST
        response = self._request(
            method=method, url=url, json=solution_article_dict
        )

        if response.status_code != 201:
            raise Exception(
                f"Failed to create solution article: {response.text}"
            )

        data: dict = response.json()
        solution_article: SolutionArticle = SolutionArticle.from_json(data)

        return solution_article

    def update_solution_article(
        self, id: Identifier, solution_article_dict: SolutionArticlePayload
    ) -> SolutionArticle:
        """Update a Solution Article."""

        logger.info("Updating solution article: %s", solution_article_dict)

        url = self.base_url + f"/articles/{id}"
        method = HTTPRequestMethod.PUT
        response = self._request(
            method=method, url=url, json=solution_article_dict
        )

        data: dict = response.json()
        # The draft is locked for editing
        if data.get("code") == "draft_locked":
            raise DraftLockedError

        solution_article: SolutionArticle = SolutionArticle.from_json(data)

        return solution_article

    def view_solution_article(self, id: Identifier) -> SolutionArticle:
        """View a Solution Article."""
        logger.info("Viewing solution article: %s", id)

        url = self.base_url + f"/articles/{id}"
        method = HTTPRequestMethod.GET
        response = self._request(method=method, url=url)

        data: dict = response.json()
        solution_article: SolutionArticle = SolutionArticle.from_json(data)

        return solution_article

    def list_all_solution_articles(
        self, folder_id: Identifier
    ) -> list[SolutionArticle]:
        """List all Solution Articles."""

        logger.info("Listing all solution articles")

        url = self.base_url + f"/folders/{folder_id}/articles"
        method = HTTPRequestMethod.GET
        response = self._request(method=method, url=url)

        data: list[dict] = response.json()
        solution_articles: list[SolutionArticle] = []
        solution_article_data: dict
        for solution_article_data in data:
            solution_article: SolutionArticle = SolutionArticle.from_json(
                solution_article_data
            )
            solution_articles.append(solution_article)

        return solution_articles

    def delete_solution_article(self, id: Identifier) -> None:
        """Delete a Solution Article."""
        logger.info("Deleting solution article: %s", id)

        url = self.base_url + f"/articles/{id}"
        method = HTTPRequestMethod.DELETE
        response = self._request(method=method, url=url)

        if response.status_code != 204:
            raise Exception(
                f"Failed to delete solution article #{id}: {response.text}"
            )

    def search_solution_articles(self, keyword: str) -> list[SolutionArticle]:
        """Search for Solution Articles."""

        logger.info("Searching for solution articles: %s", keyword)

        url = self.client.base_url + f"/search/solutions?term={keyword}"
        method = HTTPRequestMethod.GET
        response = self._request(method=method, url=url)

        if response.status_code != 200:
            raise Exception(
                f"Failed to search solution articles: {response.text}"
            )

        data: list[dict] = response.json()
        solution_articles: list[SolutionArticle] = []
        solution_article_data: dict
        for solution_article_data in data:
            solution_article: SolutionArticle = SolutionArticle.from_json(
                solution_article_data
            )
            solution_articles.append(solution_article)

        return solution_articles

    @register_interface
    def create_category(
        self, solution_category_dict: SolutionCategoryPayload
    ) -> SolutionCategory:
        """Create a Solution Category."""
        return self.create_solution_category(solution_category_dict)

    @register_interface
    def update_category(
        self, id: Identifier, solution_category_dict: SolutionCategoryPayload
    ) -> SolutionCategory:
        """Update a Solution Category."""
        return self.update_solution_category(id, solution_category_dict)

    @register_interface
    def category(self, id: Identifier) -> SolutionCategory:
        """Get a Solution Category."""
        return self.view_solution_category(id)

    @register_interface
    def categories(self) -> list[SolutionCategory]:
        """List all Solution Categories."""
        return self.list_all_solution_categories()

    @register_interface
    def delete_category(self, id: Identifier) -> None:
        """Delete a Solution Category."""
        return self.delete_solution_category(id)

    @register_interface
    def create_folder(
        self,
        category_id: Identifier,
        solution_folder_dict: SolutionFolderPayload,
    ) -> SolutionFolder:
        """Create a Solution Folder"""
        return self.create_solution_folder(category_id, solution_folder_dict)

    @register_interface
    def update_folder(
        self, id: Identifier, solution_folder_dict: SolutionFolderPayload
    ) -> SolutionFolder:
        """Update a Solution Folder"""
        return self.update_solution_folder(id, solution_folder_dict)

    @register_interface
    def folder(self, id: Identifier) -> SolutionFolder:
        """Get a Solution Folder."""
        return self.view_solution_folder(id)

    @register_interface
    def folders(self, category_id: Identifier) -> list[SolutionFolder]:
        """List all Solution Folders for a Solution Category."""
        return self.list_all_solution_folders(category_id)

    @register_interface
    def all_folders(self) -> list[SolutionFolder]:
        """List all Solution Folders.

        Uses (1 + category_count) API requests.
        """
        categories: list[SolutionCategory] = self.list_all_solution_categories()  # type: ignore
        folders: list[SolutionFolder] = []
        for category in categories:
            category_folders: list[
                SolutionFolder
            ] = self.list_all_solution_folders(
                category.id
            )  # type: ignore
            folders.extend(category_folders)

        return folders

    @register_interface
    def subfolders(self, id: Identifier) -> list[SolutionFolder]:
        """List all Solution Folders found in a Solution Folder."""
        return self.list_all_folders_in_folder(id)

    @register_interface
    def delete_folder(self, id: Identifier) -> None:
        """Delete a Solution Folder."""
        return self.delete_solution_folder(id)

    @register_interface
    def create_article(
        self,
        folder_id: Identifier,
        solution_article_dict: SolutionArticlePayload,
    ) -> SolutionArticle:
        """Create a Solution Article."""
        return self.create_solution_article(folder_id, solution_article_dict)

    @register_interface
    def update_article(
        self, id: Identifier, solution_article_dict: SolutionArticlePayload
    ) -> SolutionArticle:
        """Update a Solution Article."""
        return self.update_solution_article(id, solution_article_dict)

    @register_interface
    def article(self, id: Identifier) -> SolutionArticle:
        """View a Solution Article."""
        return self.view_solution_article(id)

    @register_interface
    def articles(self, folder_id: Identifier) -> list[SolutionArticle]:
        """List all Solution Articles in an Solution Folder."""
        return self.list_all_solution_articles(folder_id)

    @register_interface
    def all_articles(self) -> list[SolutionArticle]:
        """List all Solution Articles.

        Uses (1 + category_count + all_folders_count) API requests.
        """
        # Gather Folders
        folders: list[SolutionFolder] = self.all_folders()

        # Gather Articles
        articles: list[SolutionArticle] = []
        for folder in folders:
            folder_articles: list[SolutionArticle] = self.list_all_solution_articles(folder.id)  # type: ignore
            articles.extend(folder_articles)

        return articles

    @register_interface
    def delete_article(self, id: Identifier) -> None:
        """Delete a Solution Article."""
        return self.delete_solution_article(id)

    @register_interface
    def search_articles(self, keyword: str) -> list[SolutionArticle]:
        """Search for Solution Articles."""
        return self.search_solution_articles(keyword)


class ScenarioAutomationsAPI(BaseAPI):
    """API for Scenario Automations."""

    name = "scenario_automations"

    def list_all(self) -> list[ScenarioAutomation]:
        """List all Scenario Automations."""

        url: str = self.base_url + "scenario_automations.json"
        method: HTTPRequestMethod = HTTPRequestMethod.GET
        response: Response = self._request(method=method, url=url)

        if response.status_code != 200:
            raise Exception(
                f"Failed to list all scenario automations: {response.text}"
            )

        data: dict = response.json()
        scenario_automations: list[ScenarioAutomation] = []
        scenario_automation_data: dict
        for scenario_automation_data in data:
            scenario_automation: ScenarioAutomation = (
                ScenarioAutomation.from_json(scenario_automation_data)
            )
            scenario_automations.append(scenario_automation)

        return scenario_automations

    @register_interface
    def scenarios(self) -> list[ScenarioAutomation]:
        """List all Scenario Automations."""
        return self.list_all()
