from collections.abc import Generator

import pytest
from psycopg import Connection
from psycopg.rows import DictRow

from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)

OLD_TABLES = (
    "models",
    "events",
    "positions",
    "id_sequences",
    "collectionfields",
    "events_to_collectionfields",
    "migration_keyframes",
    "migration_keyframe_models",
    "migration_events",
    "migration_positions",
)


@pytest.fixture(scope="session", autouse=True)
def setup_pytest_session() -> Generator[None]:
    """
    Does nothing. Just an override for the parent directories conftest.
    """
    yield None


@pytest.fixture(autouse=True)
def db_connection() -> Generator[Connection[DictRow], None, None]:
    """Generates and yields a Connection object for setting up initial test data."""
    with get_new_os_conn() as conn:
        yield conn
