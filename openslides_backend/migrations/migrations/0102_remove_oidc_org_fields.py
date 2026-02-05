"""
Migration 0102: Remove OIDC fields from organization table.

OIDC configuration is now exclusively via environment variables.
The following columns are dropped from organization_t:
- oidc_enabled
- oidc_provider_url
- oidc_client_id
- oidc_client_secret
- oidc_login_button_text
- oidc_attr_mapping
- oidc_admin_api_enabled
- oidc_admin_api_url
"""

from psycopg import Cursor
from psycopg.rows import DictRow

from openslides_backend.migrations.migration_helper import (
    MigrationHelper,
    MigrationState,
)

# No data migration needed - just dropping columns
ORIGIN_COLLECTIONS: list[str] = []


def data_definition(curs: Cursor[DictRow]) -> None:
    """Drop OIDC columns from organization_t table."""
    columns = [
        "oidc_enabled",
        "oidc_provider_url",
        "oidc_client_id",
        "oidc_client_secret",
        "oidc_login_button_text",
        "oidc_attr_mapping",
        "oidc_admin_api_enabled",
        "oidc_admin_api_url",
    ]
    for col in columns:
        curs.execute(f"ALTER TABLE organization_t DROP COLUMN IF EXISTS {col};")
    curs.connection.commit()

    MigrationHelper.set_database_migration_info(
        curs, 102, MigrationState.FINALIZATION_REQUIRED
    )
