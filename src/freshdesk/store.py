"""Store Limit Information"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from typing import Final
from typing import Iterable
from typing import Iterator
from typing import Tuple
from typing import Union

from freshdesk.models import Agent
from freshdesk.models import Ticket


ENCODING: Final[str] = "utf-8"


# URI to SQLite database, such as "sqlite:///db.sqlite3" or "sqlite:///:memory:"
SQLiteURI = str  # Type Alias
ID = int  # Type Alias
StoreRow = tuple[ID, Agent, Ticket, datetime]  # Type Alias


def get_column_names(cursor: sqlite3.Cursor, table_name: str) -> tuple[str]:
    headers: tuple[str] = tuple(
        i[1]
        for i in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    )  # type: ignore
    return headers


@dataclass
class LimitInfo:
    # CUSTOM (to keep datetime info)
    timestamp: datetime

    calls_per_minute: int
    calls_remaining: int
    calls_consumed: int
    retry_time: int  # seconds

    @classmethod
    def from_bytes(cls, data: bytes) -> LimitInfo:
        (
            timestamp,
            calls_per_minute,
            calls_remaining,
            calls_consumed,
            retry_time,
        ) = data.decode(ENCODING).split(
            ";"
        )  # noqa: E501
        return cls(
            timestamp=datetime.fromtimestamp(float(timestamp)),
            calls_per_minute=int(calls_per_minute),
            calls_remaining=int(calls_remaining),
            calls_consumed=int(calls_consumed),
            retry_time=int(retry_time),
        )

    def to_bytes(self) -> bytes:
        return ";".join(
            map(
                str,
                [
                    self.timestamp.timestamp(),
                    self.calls_per_minute,
                    self.calls_remaining,
                    self.calls_consumed,
                    self.retry_time,
                ],
            )
        ).encode(ENCODING)


class LimitStore:
    """Store Freshdesk Limit Information in a SQLite database.

    WARNING: LIMIT is a keyword in SQLite. DO NOT USE LIMIT. You can use
    LIMIT_INFO/limit_info instead.
    """

    TABLE_NAME: Final[str] = "limit_info"

    def __init__(self, database_uri: SQLiteURI = ":memory:") -> None:
        self._uri: SQLiteURI = database_uri
        self.connection: sqlite3.Connection = sqlite3.connect(
            database_uri, detect_types=sqlite3.PARSE_DECLTYPES
        )
        try:
            self._create_table()
        except sqlite3.OperationalError:
            # table already exists
            pass

    def close(self) -> None:
        self.connection.close()

    def insert(
        self,
        limits: Union[LimitInfo, Iterable[LimitInfo]],
    ) -> None:
        if isinstance(limits, Iterable):
            for limit in limits:
                self.insert(limits=limit)
            return

        limit: LimitInfo = limits
        sent_at: datetime = limit.timestamp
        self.connection.execute(
            f"""
            INSERT INTO {self.TABLE_NAME}
            (sent_at, limit_info)
            VALUES (?, ?)
            """,
            (sent_at, limit),
        )
        self.connection.commit()

    @property
    def columns(self) -> tuple[str]:
        cursor: sqlite3.Cursor = self.connection.cursor()
        headers: tuple[str] = get_column_names(cursor, self.TABLE_NAME)
        cursor.close()
        return headers

    def __iter__(self) -> Iterator[Tuple[StoreRow]]:
        cursor: sqlite3.Cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {self.TABLE_NAME}")
        results = iter(cursor.fetchall())
        cursor.close()

        return results

    def _create_table(self) -> None:
        cursor: sqlite3.Cursor = self.connection.cursor()
        cursor.execute(
            f"""
            CREATE TABLE
            {self.TABLE_NAME}
            (
                id INTEGER PRIMARY KEY,
                sent_at DATETIME NOT NULL,
                limit_info LIMIT_INFO NOT NULL
            );
            """
        )
        cursor.close()
        self.connection.commit()

    @staticmethod
    def _adapt_timestamp(timestamp: datetime) -> bytes:
        if timestamp.tzinfo is None:
            aware_timestamp = timestamp.astimezone()
        else:
            aware_timestamp = timestamp
        utc_timestamp = aware_timestamp.astimezone(timezone.utc)
        return str(utc_timestamp.timestamp()).encode(ENCODING)

    @staticmethod
    def _convert_timestamp(value: bytes) -> datetime:
        local_timestamp: datetime = datetime.fromtimestamp(
            float(value.decode(ENCODING))
        ).astimezone()
        return local_timestamp


sqlite3.register_adapter(LimitInfo, LimitInfo.to_bytes)
sqlite3.register_converter("LIMIT_INFO", LimitInfo.from_bytes)

sqlite3.register_adapter(datetime, LimitStore._adapt_timestamp)
sqlite3.register_converter("DATETIME", LimitStore._convert_timestamp)
