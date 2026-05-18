from psycopg import Cursor
from psycopg.rows import DictRow

from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.migrations.migrations.base import BaseMigration


class Migration(BaseMigration):
    ORIGIN_COLLECTIONS = ["meeting"]

    @staticmethod
    def data_definition(curs: Cursor[DictRow]) -> None:
        MigrationHelper.delete_field(curs, "meeting", "motion_poll_default_backend")

    @staticmethod
    def data_manipulation(curs: Cursor[DictRow]) -> None:
        pass

    @staticmethod
    def cleanup(curs: Cursor[DictRow]) -> None:
        pass
