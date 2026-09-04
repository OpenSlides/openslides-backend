from typing import Any

from psycopg import Cursor
from psycopg.rows import DictRow

from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.migrations.patterns import Renames, Table

from ..shared.filters import Filter
from ..shared.patterns import Collection, Field


class BaseMigration:
    """Interface class for all migrations"""

    # -- Defined by developer --
    renames: Renames

    # Contains tables and fields that should be saved for retrieving data
    # in `data_manipulation`:
    #   * Collection or field gets removed but data for it is used
    #     to create/update other entries
    #   * Data from the field should be moved (with or without transformation)
    #     to the other table
    #   * Field type changes (usually it should lead to dropping
    #     old field and creating new)
    migration_tables: dict[Collection, list[Field]]

    # -- Internal --
    # Stores names of tables created from `migration_tables` and `switched_writing_side` for cleanup
    copied_tables: list[Table]

    # -- Defined in DiffMixin --
    # TODO: Implement here and in diff generator
    # Describes relations in which write field becomes a view field
    # due to rename (data should be moved).
    # Used in:
    #   * data_preparation: to save old writing side
    #   * data_manipulation: to perform move
    switched_writing_side: Any

    # Also include the new type of the field if it has to be transformed
    typed_migration_tables: dict[Collection, tuple[list[Field], dict[Field, str]]]

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

    @classmethod
    def data_preparation(cls, curs: Cursor[DictRow]) -> dict[str, Any] | None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Save data in helper tables or return it in a dict.
        Input:
            cursor
        """
        # TODO: after implementing switched_writing_side extend `migration_tables`
        # with collections and old writing side fields from `switched_writing_side``
        if cls.typed_migration_tables:
            cls.copied_tables = MigrationHelper.copy_tables(
                curs, cls.typed_migration_tables
            )
        return None

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
    def replace_from_filters_map(
        curs: Cursor[DictRow],
        collection: Collection,
        update_field: Field,
        lookup_map: list[tuple[Filter, Any]],
    ) -> str:
        """
        Helper method for using in data_manipulation.
        Purpose:
            Creates mass update statements for each item in lookup_map.
        Input:
            cursor
            collection: name of collection to update.
            update_field: name of the field to update.
            lookup_map: list of combinations filter + replace value.
        """
        # Check that update_field is a table field
        # for filter, replace_value in lookup_map:
        #       UPDATE table_name SET update_field = replace_value WHERE SqlQueryHelper.build_filter_str(filter);
        return ""

    @staticmethod
    def replace_from_plain_values_map(
        curs: Cursor[DictRow],
        collection: Collection,
        update_field: Field,
        lookup_map: list[tuple[Field, Any, Any]],
    ) -> str:
        """
        Helper method for using in data_manipulation.
        Purpose:
            Creates mass update statements for each item in lookup_map.
        Input:
            cursor
            collection: name of collection to update.
            update_field: name of the field to update.
            lookup_map: list of combinations: lookup field + lookup value + replace value.
        """
        # Check that update_field is a table field
        # for lookup_field, lookup_value, replace_value in lookup_map:
        #       filter = lookup_field '=' lookup_value
        #       UPDATE table_name SET update_field = value WHERE SqlQueryHelper.build_filter_str(condition);
        # Too similar with previous, make a base method for them.
        # TODO: already define option WHERE TRUE if condition not given.
        return ""

    @staticmethod
    def cleanup(curs: Cursor[DictRow]) -> None:
        """
        This function can be overridden by subclasses in order to implement the desired behavior.
        Purpose:
            Deletes leftovers of the migration.
        Input:
            cursor
        """
        # If the corresponding maps are defined:
        #   Drop tables from copied_tables
        #
        # Move to migration handler with cleanup statements:
        #   Set NOT NULL for added_required_fields - Done
        #   Apply enum types for fields from enum_types_to_apply
