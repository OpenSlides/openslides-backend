from datetime import datetime
from decimal import Decimal
from json import dumps as json_dumps
from math import ceil
from typing import Any

from psycopg import Cursor
from psycopg.rows import DictRow
from psycopg.types.json import Jsonb

from meta.dev.src.helper_get_names import HelperGetNames  # type: ignore # noqa
from openslides_backend.migrations.migration_helper import (
    MigrationHelper,
    MigrationState,
)
from openslides_backend.models.base import Model, model_registry
from openslides_backend.models.fields import (
    DecimalField,
    Field,
    GenericRelationListField,
    JSONField,
    OrganizationField,
    RelationListField,
    TimestampField,
)
from openslides_backend.models.models import *  # type: ignore # noqa # necessary to fill model_registry
from openslides_backend.shared.patterns import (
    FullQualifiedId,
    fqid_from_collection_and_id,
)
from openslides_backend.shared.typing import Collection

RELATION_LIST_FIELD_CLASSES = [RelationListField, GenericRelationListField]
READ_MODELS = ["models"]
WRITE_MODELS = ["all"]


class Sql_helper:
    """
    Purpose:
        Helper class containing multiple functions to make sql handling easier.
    """

    offset: int = 0
    LIMIT: int = 100
    cursor: Cursor[DictRow]

    @staticmethod
    def get_row_count() -> int:
        """
        Purpose:
            Returns the number of rows in the DB table models.
        Input:
            n/a
        Returns:
        - integer : number of fqid in sql models table
        """
        Sql_helper.cursor.execute("SELECT COUNT(fqid) FROM models;")
        result = Sql_helper.cursor.fetchone()
        if result is not None:
            if len(result) > 0:
                return int(result.get("count", "0"))
        return 0

    # END OF FUNCTION

    @staticmethod
    def raise_offset() -> None:
        """
        Purpose:
            Raises Sql_helper.offset by LIMIT
        Input:
            n/a
        Returns:
            n/a
        """
        Sql_helper.offset += Sql_helper.LIMIT

    # END OF FUNCTION

    @staticmethod
    def get_next_data_row_chunk() -> list[dict[str, Any]]:
        """
        Purpose:
            Fetches the next data chunk from sql models table depending on Sql_helper.limit and Sql_helper.offset.
            Also raises the offset after getting the chunk.
        Input:
            n/a
        Returns:
            - data_rows: fetched sql table data rows as tuple
        """

        Sql_helper.cursor.execute(
            f"SELECT fqid, data FROM models WHERE deleted='f' ORDER BY fqid LIMIT {str(Sql_helper.LIMIT)} OFFSET {str(Sql_helper.offset)};"
        )
        data_rows = Sql_helper.cursor.fetchall()
        assert data_rows is not None, "No data was found in sql table models"
        Sql_helper.raise_offset()
        return data_rows

    # END OF FUNCTION

    @staticmethod
    def transform_data(data: Any, field: Field | None = None) -> Any:
        """
        Purpose:
            Casts data so it is psycopg friendly in case it is not parsable by psycopg.
            Known and implemented cases:
                - Decimals
                - json (mostly Dictionaries)
                - Timestamps
        Input:
            - data: python formatted data
        Returns:
            - data: psycopg friendly data
        """

        if field is None:
            return data
        elif isinstance(field, DecimalField):
            if field.constraints.get("minimum") == "0.000001" and data == "0.000000":
                data = field.constraints["minimum"]
            else:
                data = Decimal(data)
        elif isinstance(field, TimestampField):
            data = datetime.fromtimestamp(data)
        elif isinstance(field, JSONField):
            data = json_dumps(data)

        return data

    # END OF FUNCTION

    @staticmethod
    def is_non_writable_sql_field(collection: str, field: str) -> bool:
        """
        Purpose:
            Checks wether the field needs to be skipped or not.
        Input:
            - collection: collection to get the necessary model
            - field: name of the field that will be checked
        Returns:
            - True / False: Boolean value dictating if field will be skipped.
        """
        model: Model
        field_class: Field

        model = model_registry[collection]()
        field_class = model.get_field(field)

        # 1.1) OrganizationFields are always generated on DB side
        if isinstance(field_class, OrganizationField):
            return True

        # 1.2) ViewFields are solely for the DB table view
        elif field_class.is_view_field:
            return True

        return False

    # END OF FUNCTION

    @staticmethod
    def get_insert_intermediate_t_commands(
        field: Field, data: dict[str, Any]
    ) -> list[tuple[str, list[Any]]]:
        """
        Purpose:
            Parses the dictionary data into a sql friendly string format.
        Input:
            - field: field that will be checked for relational dependencies
            - data: dictionary containing the data of the collection
        Returns:
            - insert_intermediate_t_commands: list containing one or several insert_intermediate_t_commands built during the method
        """
        insert_intermediate_t_commands: list = []
        values: Any
        collection_id: str
        intermediate_table: str
        field1: str
        field2: str

        values = data.get(field.own_field_name)
        collection_id = data.get("id", "")

        assert field.write_fields is not None  # error code here

        intermediate_table = field.write_fields[0]
        field1 = field.write_fields[1]
        field2 = field.write_fields[2]

        intermediate_table = HelperGetNames.get_table_name(intermediate_table)

        # 1) Add sql command
        for data_item in values:
            insert_intermediate_t_commands.append(
                (
                    f"INSERT INTO {intermediate_table} ({field1}, {field2}) VALUES (%s, %s);",
                    [collection_id, data_item],
                )
            )

        return insert_intermediate_t_commands

    # END OF FUNCTION

    @staticmethod
    def get_select_collection_command(
        collection: Collection, mapped_fields: list[str]
    ) -> str:
        """
        Purpose:
            Generates SQL to get all of the collections models from the models->>data column.
        Input:
            - collection: collection that will be retrieved.
            - mapped_fields: the fields/columns that are to be retrieved.
        Returns:
            - sql string that can be executed.
        """
        mf_string = ",".join(mapped_fields)
        return f"""
            SELECT {mf_string} FROM models
            WHERE fqid LIKE '{fqid_from_collection_and_id(collection, '%')}';
            """

    # END OF FUNCTION

    @staticmethod
    def get_update_models_command(
        models: list[dict[str, Any]],
    ) -> tuple[str, list[tuple[Jsonb, FullQualifiedId],]]:
        """
        Purpose:
            Generates SQL to be executed with executemany for updating models by overwriting their models->>data column.
        Input:
            - models: list of all elements that need to be updated. Its dicts must contain 'fqid' and 'data'.
        Returns:
            - SQL string that can be executed.
            - Argument list to be directly passed with SQL. Holding a tuple for each model with Jsonb and the fqid.
        """
        return (
            """UPDATE models SET data=%s WHERE fqid=%s""",
            [(Jsonb(elem["data"]), elem["fqid"]) for elem in models],
        )

    # END OF FUNCTION


# END HELPER CLASS


def data_manipulation(curs: Cursor[DictRow]) -> None:
    """
    Purpose:
        Iterates over chunks of the DB table models and writes the data into the respective DB tables
    Input:
        n/a
    Returns:
        n/a
    Commentary:
        TODO: At the moment the iteration for the intermediate table (L.321) is very dirty
        as it iterates over a potentially pretty big list (e.g. some known customers with lots of data).
        Thus it is worth the idea to set the intermediate tables to INITIALLY DEFERRED as well
        so they can be run immediately. This is a measure we already took for default tables.
    """
    Sql_helper.cursor = curs

    data_chunk: list[dict[str, Any]]
    collection: str
    table_name: str
    data: dict[str, Any]
    model: Model
    insert_intermediate_t_commands: list
    sql_fields: str
    sql_values: list

    insert_intermediate_t_commands = []

    result = curs.execute("SELECT COUNT(*) FROM models;").fetchone()
    assert result
    models_count = result["count"]
    # 1) Chunkwise loop trough all data_rows for the models table
    for _ in range(0, ceil(Sql_helper.get_row_count() / Sql_helper.LIMIT)):
        data_chunk = Sql_helper.get_next_data_row_chunk()

        for data_row in data_chunk:
            collection = data_row["fqid"].split("/")[0]
            table_name = HelperGetNames.get_table_name(collection)
            data = data_row["data"]

            if collection == "action_worker":
                # shorten name to fit into 256 bytes.
                action_names = data["name"].split(",")
                if len(action_names) > 1:
                    data["name"] = f"{action_names[0]}_({len(action_names)})"

            model = model_registry[collection]()
            sql_fields = ""
            sql_placeholder = ""
            sql_values = []

            # 2) Iterate over any field found in the data_row
            for field in data.keys():
                # 3) Check wether field exists in models.py too
                if model.has_field(field):

                    # 3.1) If field is RelationListField write the other tables
                    if isinstance(
                        model.get_field(field),
                        tuple(RELATION_LIST_FIELD_CLASSES),
                    ):
                        model_field = model.get_field(field)
                        if (
                            model_field.is_primary
                            and model_field.write_fields is not None
                        ):
                            insert_intermediate_t_commands.extend(
                                Sql_helper.get_insert_intermediate_t_commands(
                                    model.get_field(field), data
                                )
                            )

                    # 3.2) If field is non writable skip
                    if Sql_helper.is_non_writable_sql_field(collection, field):
                        continue

                    # 3.3) If field is non relational simply write
                    value = Sql_helper.transform_data(
                        data[field], model.get_field(field)
                    )
                    if len(sql_fields) == 0:
                        sql_fields = field
                        sql_placeholder = "%s"
                        sql_values = [value]
                    else:
                        sql_fields += f", {field}"
                        sql_placeholder += ", %s"
                        sql_values.append(value)
            # END LOOP data.keys()
            curs.execute(
                f"INSERT INTO {table_name} ({sql_fields}) VALUES ({sql_placeholder})",
                sql_values,
            )
        # END LOOP data_rows
        MigrationHelper.write_line(
            f"{min(Sql_helper.offset, models_count)} of {models_count} models written to tables."
        )
    # END LOOP data chunks

    # 4) INSERT intermediate tables
    for command, values in insert_intermediate_t_commands:
        curs.execute(command, values)

    # clear replace tables as this migration writes the tables directly
    MigrationHelper.set_database_migration_info(
        curs,
        100,
        MigrationState.FINALIZATION_REQUIRED,
        replace_tables={},
    )


def cleanup(curs: Cursor[DictRow]) -> None:
    """
    Purpose:
        Deletes the old tables
    Input:
        cursor
    """
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
    for table_name in OLD_TABLES:
        curs.execute(f"DROP TABLE {table_name} CASCADE;")


# END OF FUNCTION
