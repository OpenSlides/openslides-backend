from psycopg import Cursor
from psycopg.rows import DictRow


class BaseMigration:
    """Interface class for all migrations"""

    @staticmethod
    def check_prerequisites(curs: Cursor[DictRow]) -> str:
        """
        Checks all prerequisites for the migration.
        Returns:
            All errors collected. Empty string otherwise.
        """
        return ""

    @staticmethod
    def data_definition(curs: Cursor[DictRow]) -> None:
        """
        Apllies all manual SQL DDL changes necessary.
        Triggers are automatically recreated.
        """

    @staticmethod
    def data_manipulation(curs: Cursor[DictRow]) -> None:
        """
        Purpose:
            Writes all data changes necessary after the DDL changes.
        Input:
            cursor
        """

    @staticmethod
    def cleanup(curs: Cursor[DictRow]) -> None:
        """
        Purpose:
            Deletes leftovers of the migration.
        Input:
            cursor
        """
