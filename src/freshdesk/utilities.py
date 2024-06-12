import logging.config
import math
from datetime import date
from datetime import datetime
from datetime import timezone
from typing import Optional

import dateutil.parser

from freshdesk.api import SearchResults
from freshdesk.client import UnregisteredClient as FreshdeskClient
from freshdesk.constants import MAX_PAGES
from freshdesk.constants import RESULTS_PER_PAGE
from freshdesk.logger import get_config
from freshdesk.models import Agent
from freshdesk.models import Field
from freshdesk.models import Ticket
from freshdesk.typings import TicketJSON


# YYYY-MM-DDTHH:MM:SSZ
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"  # UTC


# Logging
logging.config.dictConfig(get_config(__file__))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_agent_by_name(agents: list[Agent], name: str) -> Agent:
    """; Get Agent, given name."""
    agent: Agent
    for agent in agents:
        agent_name: str = agent.contact.name
        if name.lower() in agent_name.lower():
            return agent
    raise Exception(
        f"Agent {name} not found: {[a.contact.name for a in agents]}"
    )


def get_date_query(date_: date) -> str:
    """Get date query, for a specific date.

    Includes updated and created dates.
    """

    date_str: str = date_.strftime(Field.DATE_FORMAT)

    query: str = f"""
    (
        created_at:'{date_str}' OR updated_at:'{date_str}'
    )
    """  # noqa: E501
    query = "".join([line.strip() for line in query.splitlines() if line])

    return query


def get_date_range_query(start_date: date, end_date: date) -> str:
    """Given a start and end date, return a query string for the date range."""

    if start_date == end_date:
        return get_date_query(start_date)

    start_date_str: str = start_date.strftime(Field.DATE_FORMAT)
    end_date_str: str = end_date.strftime(Field.DATE_FORMAT)

    query: str = f"""
    (
        (
            created_at:>'{start_date_str}' AND created_at:<'{end_date_str}'
        ) OR (
            updated_at:>'{start_date_str}' AND updated_at:<'{end_date_str}'
        )
    )
    """  # noqa: E501
    query = "".join([line.strip() for line in query.splitlines() if line])

    return query


def get_remaining_search_results(
    client: "FreshdeskClient",
    query: str,
    search_results: SearchResults,
    strict: bool = False,
) -> list["TicketJSON"]:
    logger.info(f"Retrieving remaining search results: {query=}.")

    # params: dict = {'query': query}
    # url: str = client.base_url + '/search/tickets'

    total: int = int(search_results["total"])
    pages: int = math.ceil(total / RESULTS_PER_PAGE)
    results: list["TicketJSON"] = search_results["results"]

    logger.info(f"There are {pages=} of results.")

    # Whether or not to allow an error with more than available pages.
    if strict:
        page_range = range(2, pages + 1)
    elif not strict:
        page_range = range(2, min(pages + 1, MAX_PAGES))

    for page in page_range:
        logger.info(f"Going to page {page}.")
        # params['page'] = page
        # response = client._request(method='GET', url=url, params=params)
        # sr: SearchResults = response.json()
        sr: SearchResults = client.api.tickets.filter_tickets(
            query=query, page=page
        )

        results.extend(sr["results"])

    return results


def get_ticket_agent(ticket: Ticket, agents: list[Agent]) -> Optional[Agent]:
    """Get the agent associated with the ticket, given all avialable agents."""

    agent: Agent
    for agent in agents:
        if ticket.responder_id == agent.id:
            return agent
    else:
        return None


def parse_timestamp(timestamp: str) -> datetime:
    # timestamp.astimezone(timezone.utc).strftime(TIMESTAMP_FORMAT)
    return datetime.strptime(timestamp, TIMESTAMP_FORMAT).replace(
        tzinfo=timezone.utc
    )


def parse_datetime(dt: str) -> datetime:
    parsed = dateutil.parser.parse(dt)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
