import datetime
import os
from sqlalchemy import create_engine
from db import Session as TblSession

from sqlalchemy.orm import Session
from dataclasses import dataclass
from typing import Optional

DB_USER = os.environ.get("DB_USER", "user")
DB_PASS = os.environ.get("DB_PASS", "pass")
DB_HOST = os.environ.get("DB_HOST", "products-database")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "products")

products_engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_size=20,
    max_overflow=0,
)


@dataclass
class SessionResult:
    session: Optional[TblSession]
    error: Optional[str]


def getAndValidateSession(session_id: str, products_session: Session):
    try:
        session = (
            products_session.query(TblSession).filter_by(id=int(session_id)).first()
        )
    except Exception as e:
        return SessionResult(None, f"Database error: {e}")

    if session is None:
        return SessionResult(None, "Session not found")

    if is_older_than_5_minutes(session.last_activity):
        return SessionResult(None, "Session no longer valid")

    try:
        session.last_activity = datetime.datetime.now(datetime.timezone.utc)
        products_session.commit()
    except Exception as e:
        products_session.rollback()
        return SessionResult(None, f"Database error: {e}")

    return SessionResult(session, None)


def is_older_than_5_minutes(event_time):
    # Get the current time, ensuring it is timezone-aware (UTC is a good default)
    current_time = datetime.datetime.now(datetime.timezone.utc)

    # If event_time is naive (no tzinfo), assume UTC to make it timezone-aware
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=datetime.timezone.utc)

    # Define the 5-minute threshold
    time_threshold = datetime.timedelta(minutes=5)

    # Calculate the difference
    time_difference = current_time - event_time

    # Check if the difference is greater than the threshold
    return time_difference > time_threshold
