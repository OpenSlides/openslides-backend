from migrations import InvalidMigrationsException
from migrations import assert_migration_index as base_assert_migration_index

from ..shared.exceptions import View400Exception


def assert_migration_index() -> None:
    try:
        base_assert_migration_index()
    except InvalidMigrationsException as e:
        raise View400Exception(str(e))
