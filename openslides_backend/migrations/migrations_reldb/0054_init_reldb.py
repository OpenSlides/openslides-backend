import os
import sys
from datetime import datetime
from json import dumps as json_dumps
from math import ceil
from typing import Any

from psycopg.rows import dict_row

from openslides_backend.database.db_connection_handling import os_conn_pool
from openslides_backend.models.base import Model, model_registry
from openslides_backend.models.fields import (
    Field,
    GenericRelationListField,
    OrganizationField,
    RelationListField,
    TimestampField,
)
from openslides_backend.models.models import *  # type: ignore # noqa # necessary to fill model_registry

sys.path.append("global")

from meta.dev.src.helper_get_names import HelperGetNames  # type: ignore # noqa

RELATION_LIST_FIELD_CLASSES = [RelationListField, GenericRelationListField]


class Sql_helper:
    """
    Purpose:
        Helper class containing multiple functions to make sql handling easier.
    """

    offset: int = 0
    limit: int = 100

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
        with os_conn_pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT COUNT(fqid) FROM models;")
                result = cur.fetchone()
                if result is not None:
                    if len(result) > 0:
                        return int(result.get("count", "0"))
                return 0

    # END OF FUNCTION

    @staticmethod
    def raise_offset() -> None:
        """
        Purpose:
            Raises Sql_helper.offset by 100
        Input:
            n/a
        Returns:
            n/a
        """
        Sql_helper.offset += 100

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

        with os_conn_pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"SELECT fqid, data FROM models ORDER BY fqid LIMIT {str(Sql_helper.limit)} OFFSET {str(Sql_helper.offset)};"
                )
                data_rows = cur.fetchall()
        assert data_rows is not None, "No data was found in sql table models"
        Sql_helper.raise_offset()
        return data_rows

    # END OF FUNCTION

    @staticmethod
    def cast_data(data: Any, field: Field | None = None) -> Any:
        """
        Purpose:
            Casts data so it is psycopg friendly in case it is not parsable by psycopg.
            Known and implemented cases:
                - Dictionaries
                - Timestamps
        Input:
            - data: python formatted data
        Returns:
            - data: psycopg friendly data
        """

        if field is None:
            return data

        elif isinstance(field, TimestampField):
            data = datetime.fromtimestamp(data)

        elif isinstance(data, dict):
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

        # 1.3) Ids are generated as well
        elif field == "id":
            return True

        return False

    # END OF FUNCTION

    @staticmethod
    def get_insert_intermediate_t_commands(field: Field, data: dict[str, Any]) -> list:
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


# END HELPER CLASS


def data_definition() -> None:
    """
    Purpose:
        Applies the relational schema to the database
    Input:
        n/a
    Returns:
        n/a
    """
    with os_conn_pool.connection() as conn:
        with conn.cursor() as cur:
            path = os.path.realpath(
                os.path.join("global", "meta", "dev", "sql", "schema_relational.sql")
            )
            try:
                cur.execute(open(path).read())
            except Exception as e:
                print(f"On applying relational schema there was an error: {str(e)}\n")
                return


# END OF FUNCTION


def data_manipulation() -> None:
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
    data_chunk: list[dict[str, Any]]
    collection: str
    table_name: str
    data: dict[str, Any]
    model: Model
    insert_intermediate_t_commands: list
    sql_fields: str
    sql_values: list

    # 1) Prepare connection & cursor
    with os_conn_pool.connection() as conn:
        with conn.cursor() as cur:

            # 2) BEGIN TRANSACTION
            with conn.transaction():
                insert_intermediate_t_commands = []

                # 3) Chunkwise loop trough all data_rows for the models table
                for i in range(0, ceil(Sql_helper.get_row_count() / Sql_helper.limit)):
                    data_chunk = Sql_helper.get_next_data_row_chunk()

                    for data_row in data_chunk:
                        collection = data_row["fqid"].split("/")[0]
                        table_name = HelperGetNames.get_table_name(collection)
                        data = data_row["data"]
                        model = model_registry[collection]()
                        sql_fields = ""
                        sql_placeholder = ""
                        sql_values = []

                        # 4) Iterate over any field found in the data_row
                        for field in data.keys():
                            # 5) Check wether field exists in models.py too
                            if model.has_field(field):

                                # 5.1) If field is RelationListField write the other tables
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

                                # 5.2) If field is non writable skip
                                if Sql_helper.is_non_writable_sql_field(
                                    collection, field
                                ):
                                    continue

                                # 5.3) If field is non relational simply write
                                value = Sql_helper.cast_data(
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
                        cur.execute(
                            f"INSERT INTO {table_name} ({sql_fields}) VALUES ({sql_placeholder})",
                            sql_values,
                        )
                    # END LOOP data_rows
                # END LOOP data chunks

                # 6) INSERT intermediate tables
                for command, values in insert_intermediate_t_commands:
                    cur.execute(command, values)
            # 7) END TRANSACTION
        # 8) Exit cursor
    # 9) Exit connection


# END OF FUNCTION
