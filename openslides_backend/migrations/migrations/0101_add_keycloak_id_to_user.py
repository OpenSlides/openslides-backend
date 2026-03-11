"""
Migration 0101: Add keycloak_id column to user table.

Adds the keycloak_id column to user_t. The user VIEW uses SELECT * and
automatically picks up new columns, so no view change is needed.
This must run before the Keycloak user migration (0102) which reads/writes keycloak_id.
"""

from psycopg import Cursor
from psycopg.rows import DictRow

from openslides_backend.migrations.migration_helper import (
    MigrationHelper,
    MigrationState,
)

ORIGIN_COLLECTIONS: list[str] = []


def data_definition(curs: Cursor[DictRow]) -> None:
    """Add keycloak_id column to user_t."""
    curs.execute("""
        ALTER TABLE user_t ADD COLUMN IF NOT EXISTS keycloak_id VARCHAR(256) DEFAULT NULL;
    """)

    curs.connection.commit()

    MigrationHelper.set_database_migration_info(
        curs, 101, MigrationState.FINALIZATION_REQUIRED
    )
