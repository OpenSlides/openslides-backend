from psycopg import Cursor
from psycopg.rows import DictRow


class BaseMigration:
    """Interface class for all migrations"""

    @staticmethod
    def check_prerequisites(curs: Cursor[DictRow]) -> str:
        """
        This function should be overridden by subclasses to implement the desired behavior.
        Purpose:
            Checks all prerequisites for the migration.
        Input:
            cursor
        Returns:
            All errors collected. Empty string otherwise.
        """
        return ""

    @staticmethod
    def data_definition(curs: Cursor[DictRow]) -> None:
        """
        This function should be overridden by subclasses to implement the desired behavior.
        Purpose:
            Applies all manual SQL DDL changes necessary.
            (Triggers and views are automatically recreated by the framework.)
        Input:
            cursor
        """

    @staticmethod
    def data_manipulation(curs: Cursor[DictRow]) -> None:
        """
        This function should be overridden by subclasses to implement the desired behavior.
        Purpose:
            Writes all data changes necessary after the DDL changes.
        Input:
            cursor
        """

    @staticmethod
    def cleanup(curs: Cursor[DictRow]) -> None:
        """
        This function should be overridden by subclasses to implement the desired behavior.
        Purpose:
            Deletes leftovers of the migration.
        Input:
            cursor
        """
