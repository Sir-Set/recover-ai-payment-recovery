import sqlite3
from datetime import datetime, timezone


DATABASE_PATH = "recover_ai.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            action TEXT,
            decision TEXT,
            recovery_probability REAL,
            expected_recovery REAL,
            reason TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def record_event(
    payment_id: str,
    event_type: str,
    action: str | None = None,
    decision: str | None = None,
    recovery_probability: float | None = None,
    expected_recovery: float | None = None,
    reason: str | None = None,
):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO audit_events (
            payment_id,
            event_type,
            action,
            decision,
            recovery_probability,
            expected_recovery,
            reason,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payment_id,
            event_type,
            action,
            decision,
            recovery_probability,
            expected_recovery,
            reason,
            datetime.now(timezone.utc).isoformat(),
        ),
    )

    connection.commit()
    connection.close()


def get_events(payment_id: str | None = None):
    connection = get_connection()

    if payment_id:
        cursor = connection.execute(
            """
            SELECT *
            FROM audit_events
            WHERE payment_id = ?
            ORDER BY created_at ASC
            """,
            (payment_id,),
        )
    else:
        cursor = connection.execute(
            """
            SELECT *
            FROM audit_events
            ORDER BY created_at DESC
            """
        )

    events = [dict(row) for row in cursor.fetchall()]

    connection.close()

    return events