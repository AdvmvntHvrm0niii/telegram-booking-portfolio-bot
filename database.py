"""SQLite storage for bookings and leads (standard-library sqlite3 only).

Blocking sqlite3 calls run in worker threads via asyncio.to_thread, using a
short-lived connection per operation. All SQL is parameterized.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

CancelResult = Literal["cancelled", "not_found", "already_cancelled"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS bookings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    username     TEXT,
    full_name    TEXT NOT NULL,
    phone        TEXT NOT NULL,
    service      TEXT NOT NULL,
    booking_date TEXT NOT NULL,
    booking_time TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled')),
    created_at   TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_bookings_active_slot
    ON bookings (service, booking_date, booking_time) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS ix_bookings_user ON bookings (user_id);

CREATE TABLE IF NOT EXISTS leads (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    username   TEXT,
    question   TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    """Return the current UTC time as a string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class Database:
    """Async-friendly wrapper around a SQLite database file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    # -- setup ------------------------------------------------------------- #
    def _init_sync(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(SCHEMA)

    async def init(self) -> None:
        """Create the database file and tables if they don't exist."""
        await asyncio.to_thread(self._init_sync)
        logger.info("Database ready at %s", self.path)

    # -- bookings ---------------------------------------------------------- #
    def _booked_times_sync(self, service: str, booking_date: str) -> set[str]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT booking_time FROM bookings "
                "WHERE service = ? AND booking_date = ? AND status = 'active'",
                (service, booking_date),
            ).fetchall()
        return {row["booking_time"] for row in rows}

    async def get_booked_times(self, service: str, booking_date: str) -> set[str]:
        """Return active booked times for a service on a date."""
        return await asyncio.to_thread(self._booked_times_sync, service, booking_date)

    def _create_booking_sync(
        self,
        user_id: int,
        username: str | None,
        full_name: str,
        phone: str,
        service: str,
        booking_date: str,
        booking_time: str,
    ) -> int | None:
        try:
            with closing(self._connect()) as conn, conn:
                cur = conn.execute(
                    "INSERT INTO bookings (user_id, username, full_name, phone, service, "
                    "booking_date, booking_time, status, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)",
                    (user_id, username, full_name, phone, service, booking_date, booking_time, _now()),
                )
                return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

    async def create_booking(
        self,
        user_id: int,
        username: str | None,
        full_name: str,
        phone: str,
        service: str,
        booking_date: str,
        booking_time: str,
    ) -> int | None:
        """Insert a booking. Returns its ID, or None if the slot is already taken."""
        return await asyncio.to_thread(
            self._create_booking_sync,
            user_id, username, full_name, phone, service, booking_date, booking_time,
        )

    def _latest_bookings_sync(self, limit: int) -> list[sqlite3.Row]:
        with closing(self._connect()) as conn:
            return conn.execute(
                "SELECT * FROM bookings ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    async def get_latest_bookings(self, limit: int = 10) -> list[sqlite3.Row]:
        """Return the newest bookings."""
        return await asyncio.to_thread(self._latest_bookings_sync, limit)

    def _cancel_booking_sync(self, booking_id: int) -> CancelResult:
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT status FROM bookings WHERE id = ?", (booking_id,)
            ).fetchone()
            if row is None:
                return "not_found"
            if row["status"] == "cancelled":
                return "already_cancelled"
            conn.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
            return "cancelled"

    async def cancel_booking(self, booking_id: int) -> CancelResult:
        """Cancel a booking by ID, freeing its slot."""
        return await asyncio.to_thread(self._cancel_booking_sync, booking_id)

    # -- leads ------------------------------------------------------------- #
    def _create_lead_sync(self, user_id: int, username: str | None, question: str) -> int:
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(
                "INSERT INTO leads (user_id, username, question, status, created_at) "
                "VALUES (?, ?, ?, 'new', ?)",
                (user_id, username, question, _now()),
            )
            return int(cur.lastrowid or 0)

    async def create_lead(self, user_id: int, username: str | None, question: str) -> int:
        """Store a question as a lead and return its ID."""
        return await asyncio.to_thread(self._create_lead_sync, user_id, username, question)

    def _latest_leads_sync(self, limit: int) -> list[sqlite3.Row]:
        with closing(self._connect()) as conn:
            return conn.execute(
                "SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    async def get_latest_leads(self, limit: int = 10) -> list[sqlite3.Row]:
        """Return the newest leads."""
        return await asyncio.to_thread(self._latest_leads_sync, limit)

