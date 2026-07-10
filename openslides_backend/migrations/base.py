from typing import Any

from psycopg import Cursor
from psycopg.rows import DictRow


class BaseMigration:
    """Interface class for all migrations"""

    @staticmethod
    def check_prerequisites(curs: Cursor[DictRow]) -> str:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Checks all prerequisites for the migration.
        Input:
            cursor
        Returns:
            All errors collected. Empty string otherwise.
        """
        return ""

    @staticmethod
    def data_preparation(curs: Cursor[DictRow]) -> dict[str, Any] | None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Save data in helper tables or return it in a dict.
        Input:
            cursor
        """

    @staticmethod
    def data_definition(curs: Cursor[DictRow]) -> None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Applies all manual SQL DDL changes necessary.
            (Triggers and views are automatically recreated by the framework.)
        Input:
            cursor
        """

    @staticmethod
    def data_manipulation(curs: Cursor[DictRow], stash: dict[str, Any] | None) -> None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Writes all data changes necessary after the DDL changes.
        Input:
            cursor
            stash: data that was previously stashed by data_preparation.
        """

    @staticmethod
    def cleanup(curs: Cursor[DictRow]) -> None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Deletes leftovers of the migration.
        Input:
            cursor
        """
