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
)

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
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(fqid) FROM models;")
                result = cur.fetchone()
                if result is not None:
                    if len(result) > 0:
                        return int(result[0].get("count", "0"))
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
    def parse_data_to_sql_value(data: Any, quote: str = "'") -> str:
        """
        Purpose:
            Parses the dictionary data into a sql friendly string format.
        Input:
            - data: dictionary containing the python formatted data
            - quote(optional): which quote-type should be used. Necessary for sql formatting arrays
        Returns:
            - data: sql friendly string formatted data
        """
        list_str: str

        # 1.1) format number to string
        if isinstance(data, (int, float)):
            data = str(data)

        # 1.2) format bool to string
        elif isinstance(data, bool):
            if data:
                data = "true"
            else:
                data = "false"

        # 1.3) format dictionary to json string
        elif isinstance(data, dict):
            data = json_dumps(data)
            data = f"'{data}'"

        # 1.4) format list to array string e.g. [1, 'test', 'b'] -> '{1, "test", "b"}'
        # INFO: doesn't cover nested lists yet
        elif isinstance(data, list):
            list_str = ""
            # 1.4.1) format list items
            for n, item in enumerate(data):
                value = Sql_helper.parse_data_to_sql_value(item, quote='"')
                if len(list_str) == 0:
                    list_str = "'{" + f"{value}"
                else:
                    list_str += f", {value}"

                if n + 1 == len(data):
                    list_str += "}'"
            data = list_str

        # 1.5) format string to string
        else:
            data = f"{quote}{str(data)}{quote}"

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
    def insert_intermediate_table(field: Field, data: dict[str, Any]) -> list:
        """
        Purpose:
            Parses the dictionary data into a sql friendly string format.
        Input:
            - field: field that will be checked for relational dependencies
            - data: dictionary containing the data of the collection
        Returns:
            - sql_command: string containing one or several sql_commands built during the method
        """
        sql_commands: list = []
        values: Any
        collection_id: str
        intermediate_table: str
        field1: str
        field2: str
        sql_value: str

        values = data.get(field.own_field_name)
        collection_id = data.get("id", "")

        assert field.write_fields is not None  # error code here

        intermediate_table = field.write_fields[0]
        field1 = field.write_fields[1]
        field2 = field.write_fields[2]

        # 1.3) Add sql command
        for data_item in values:
            sql_value = Sql_helper.parse_data_to_sql_value(data_item)
            sql_commands.append(
                f"INSERT INTO {intermediate_table}_t ({field1}, {field2}) VALUES ({collection_id}, {sql_value});"
            )

        return sql_commands

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


# END OF FUNCTION


def data_manipulation() -> None:
    """
    Purpose:
        Iterates over chunks of the DB table models and writes the data into the respective DB tables
    Input:
        n/a
    Returns:
        n/a
    """
    data_chunk: list[dict[str, Any]]
    collection: str
    data: dict[str, Any]
    model: Model
    sql_commands: list
    sql_fields: str
    sql_values: str

    # 1) Prepare connection & cursor
    with os_conn_pool.connection() as conn:
        with conn.cursor() as cur:

            # 2) BEGIN TRANSACTION
            with conn.transaction():

                # 3) Chunkwise loop trough all data_rows for the models table
                for i in range(0, ceil(Sql_helper.get_row_count() / Sql_helper.limit)):
                    data_chunk = Sql_helper.get_next_data_row_chunk()

                    for data_row in data_chunk:
                        collection = data_row["fqid"].split("/")[0]
                        data = data_row["data"]
                        model = model_registry[collection]()
                        sql_fields, sql_values = "", ""
                        sql_commands = []

                        # 4) Iterate over any field found in the data_row
                        for field in data.keys():
                            # 5) Check wether field exists in models.py too
                            if model.has_field(field):

                                # 5.1) If field is non writable skip
                                if Sql_helper.is_non_writable_sql_field(
                                    collection, field
                                ):
                                    continue

                                # 5.3) If field is non relational simply write
                                sql_value = Sql_helper.parse_data_to_sql_value(
                                    data[field]
                                )
                                if len(sql_fields) == 0:
                                    sql_fields = field
                                    sql_values = sql_value
                                else:
                                    sql_fields += f", {field}"
                                    sql_values += f", {sql_value}"

                                # 5.2) If field is RelationListField write the other tables
                                if isinstance(
                                    model.get_field(field),
                                    tuple(RELATION_LIST_FIELD_CLASSES),
                                ):
                                    model_field = model.get_field(field)
                                    if (
                                        model_field.is_primary
                                        and model_field.write_fields is not None
                                    ):
                                        sql_commands.extend(
                                            Sql_helper.insert_intermediate_table(
                                                model.get_field(field), data
                                            )
                                        )

                        sql_commands.append(
                            f"INSERT INTO {collection}_t ({sql_fields}) VALUES({sql_values});"
                        )
                        for command in sql_commands:
                            cur.execute(command)
                            # BESPRECHEN: Funktioniert gut, bis etwas nicht deferred ist bspw. agenda_item_t_content_object_id_motion_id
                        # 6) Extend TRANSACTION by INSERT
                    # END LOOP data_rows
                # END LOOP data chunks
            # 7) END TRANSACTION
        # 8) Exit cursor
    # 9) Exit connection


# END OF FUNCTION
