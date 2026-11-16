import pytest

from openslides_backend.migrations.migrations.base import MigrationCursor


def test_migration_cursor_does_not_expose_connection() -> None:
    cursor = object.__new__(MigrationCursor)

    with pytest.raises(RuntimeError, match="do not expose their connection"):
        cursor.connection
