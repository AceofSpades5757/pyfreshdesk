"""Limit Information"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final

from freshdesk.models import Agent
from freshdesk.models import Ticket


ENCODING: Final[str] = "utf-8"


@dataclass
class LimitInfo:
    timestamp: datetime

    calls_per_minute: int
    calls_remaining: int
    calls_consumed: int
    retry_time: int  # seconds
