import time as _time
from datetime import tzinfo,datetime,timedelta
from decimal import Decimal
from json import dumps as json_dumps
from math import ceil
from typing import Any
import os
import re


from psycopg import Cursor
from psycopg.rows import DictRow
from psycopg.types.json import Jsonb

from meta.dev.src.helper_get_names import HelperGetNames  # type: ignore # noqa
from openslides_backend.migrations.migration_helper import (
    OLD_TABLES,
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

PAT_TRUTHY = r'^(1|YES|ON|TRUE)$'  # matched with IGNORECASE flag
PAT_OFFSET = r'^[\+-]?\d\d:\d\d$'
RELATION_LIST_FIELD_CLASSES = [RelationListField, GenericRelationListField]
# TODO update before merging into main.
ORIGIN_COLLECTIONS = [
    "organization",
    "user",
    "meeting_user",
    "gender",
    "organization_tag",
    "theme",
    "committee",
    "meeting",
    "structure_level",
    "group",
    "personal_note",
    "tag",
    "agenda_item",
    "list_of_speakers",
    "structure_level_list_of_speakers",
    "point_of_order_category",
    "speaker",
    "topic",
    "motion",
    "motion_submitter",
    "motion_supporter",
    "motion_editor",
    "motion_working_group_speaker",
    "motion_comment",
    "motion_comment_section",
    "motion_category",
    "motion_block",
    "motion_change_recommendation",
    "motion_state",
    "motion_workflow",
    "poll",
    "option",
    "vote",
    "assignment",
    "assignment_candidate",
    "poll_candidate_list",
    "poll_candidate",
    "mediafile",
    "meeting_mediafile",
    "projector",
    "projection",
    "projector_message",
    "projector_countdown",
    "chat_group",
    "chat_message",
    "action_worker",
    "import_preview",
    "history_position",
    "history_entry",
]


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
        Returns:
        - integer : number of fqid in sql models table
        """
        Sql_helper.cursor.execute("SELECT COUNT(fqid) FROM models;")
        result = Sql_helper.cursor.fetchone()
        return (result.get("count", 0)) if result else 0

    # END OF FUNCTION

    @staticmethod
    def raise_offset() -> None:
        """
        Purpose:
            Raises Sql_helper.offset by LIMIT
        """
        Sql_helper.offset += Sql_helper.LIMIT

    # END OF FUNCTION

    @staticmethod
    def get_next_data_row_chunk() -> list[dict[str, Any]]:
        """
        Purpose:
            Fetches the next data chunk from sql models table depending on Sql_helper.limit and Sql_helper.offset.
            Also raises the offset after getting the chunk.
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
            data = datetime.fromtimestamp(data,tz=OSTime())
        elif isinstance(field, JSONField):
            data = json_dumps(data)

        return data

    # END OF FUNCTION

    @staticmethod
    def is_non_writable_sql_field(field: Field) -> bool:
        """
        Purpose:
            Checks wether the field needs to be skipped or not.
        Input:
            - field: field type that will be checked
        Returns:
            - True / False: Boolean value dictating if field will be skipped.
        """
        # 1) OrganizationFields are always generated on DB side
        # ViewFields are solely for the DB table view
        return isinstance(field, OrganizationField) or field.is_view_field

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

        intermediate_table = HelperGetNames.get_table_name(intermediate_table, True)

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


class OSTime(tzinfo):

    def utcoffset(self, dt):
        return get_utc_offset() + self.dst(dt)

    def dst(self, dt):
        dst_hours = 0
        if get_use_dst() and is_dst(dt):
            dst_hours = 1

        return timedelta(hours=dst_hours)

    def tzname(self, dt):
        return None


def get_utc_offset():
    hours, minutes = os.environ['MIG0100_UTC_OFFSET'].split(':')
    return timedelta(hours=int(hours), minutes=int(minutes))


def get_use_dst():
    return bool(re.match(PAT_TRUTHY, os.environ['MIG0100_USE_DST'], flags=re.IGNORECASE))


def is_dst(dt):
    tt = (dt.year, dt.month, dt.day,
          dt.hour, dt.minute, dt.second,
          dt.weekday(), 0, 0)
    stamp = _time.mktime(tt)
    tt = _time.localtime(stamp)
    return tt.tm_isdst > 0


def check_prerequisites() -> bool:
    try:
        i_read_docs = os.environ['MIG0100_I_READ_DOCS']
        utc_offset = os.environ['MIG0100_UTC_OFFSET']
        _ = os.environ['MIG0100_USE_DST']
    except KeyError as e:
        print("This is migration 100, part of the OpenSlides 4.3.0 release.")
        print("This migration will fundamentally restructure all data.")
        print("See LINK for more information.")
        print()
        print("env var not set " + str(e))
        return False

    if not re.match(PAT_TRUTHY, i_read_docs, flags=re.IGNORECASE):
        print(f"'{i_read_docs}' is no acceptable value for MIG0100_I_READ_DOCS")
        return False
    if not re.match(PAT_OFFSET, utc_offset):
        print(f"'{utc_offset}' is no acceptable value for MIG0100_UTC_OFFSET")
        return False

    print( "For timestamp conversion ...")
    print(f"- using UTC offset: {utc_offset}")
    print(f"- using platform provided DST: {get_use_dst()}")

    return True


def data_manipulation(curs: Cursor[DictRow]) -> None:
    """
    Purpose:
        Iterates over chunks of the DB table models and writes the data into the respective DB tables
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
    found_collections = set()
    # 1) Chunkwise loop trough all data_rows for the models table
    for _ in range(0, ceil(Sql_helper.get_row_count() / Sql_helper.LIMIT)):
        data_chunk = Sql_helper.get_next_data_row_chunk()

        for data_row in data_chunk:
            collection = data_row["fqid"].split("/")[0]
            found_collections.add(collection)
            table_name = HelperGetNames.get_table_name(collection, True)
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
            for field_name in data.keys():
                # 3) Check wether field exists in models.py too
                if field := model.try_get_field(field_name):

                    # 3.1) If field is RelationListField write the other tables
                    if (
                        isinstance(field, tuple(RELATION_LIST_FIELD_CLASSES))
                        and field.is_primary
                        and field.write_fields is not None
                    ):
                        insert_intermediate_t_commands.extend(
                            Sql_helper.get_insert_intermediate_t_commands(field, data)
                        )

                    # 3.2) If field is non writable skip
                    if Sql_helper.is_non_writable_sql_field(field):
                        continue

                    # 3.3) If field is non relational simply write
                    value = Sql_helper.transform_data(data[field_name], field)
                    if len(sql_fields) == 0:
                        sql_fields = field_name
                        sql_placeholder = "%s"
                        sql_values = [value]
                    else:
                        sql_fields += f", {field_name}"
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
    )


def cleanup(curs: Cursor[DictRow]) -> None:
    """
    Purpose:
        Deletes the old tables
    Input:
        cursor
    """

    try:
        i_read_code = os.environ['MIG0100_I_READ_CODE']
    except KeyError:
        i_read_code = None
    if i_read_code is not None:
        if re.match(PAT_TRUTHY, i_read_code, flags=re.IGNORECASE):
            print('(┛◉Д◉)┛彡┻━┻')
            MigrationHelper.write_line('(┛◉Д◉)┛彡┻━┻')

    for table_name in OLD_TABLES:
        curs.execute(f"DROP TABLE {table_name} CASCADE;")


# END OF FUNCTION
