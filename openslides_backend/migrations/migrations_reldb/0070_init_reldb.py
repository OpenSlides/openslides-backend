import os
from datetime import datetime
from decimal import Decimal
from json import dumps as json_dumps
from math import ceil
from typing import Any

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from meta.dev.src.helper_get_names import HelperGetNames  # type: ignore # noqa
from openslides_backend.models.base import Model, model_registry
from openslides_backend.models.fields import (
    DecimalField,
    Field,
    GenericRelationListField,
    OrganizationField,
    RelationListField,
    TimestampField,
)
from openslides_backend.models.models import *  # type: ignore # noqa # necessary to fill model_registry
from openslides_backend.services.postgresql.db_connection_handling import os_conn_pool
from openslides_backend.shared.patterns import (
    FullQualifiedId,
    Id,
    collection_and_id_from_fqid,
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from openslides_backend.shared.typing import Collection, PartialModel

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
                    f"SELECT fqid, data FROM models WHERE deleted='f' ORDER BY fqid LIMIT {str(Sql_helper.limit)} OFFSET {str(Sql_helper.offset)};"
                )
                data_rows = cur.fetchall()
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
                - Dictionaries
                - Timestamps
        Input:
            - data: python formatted data
        Returns:
            - data: psycopg friendly data
        """

        if field is None:
            return data
        elif isinstance(field, DecimalField):
            data = Decimal(data)
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
                os.path.join("meta", "dev", "sql", "schema_relational.sql")
            )
            try:
                cur.execute(open(path).read())
            except Exception as e:
                print(f"On applying relational schema there was an error: {str(e)}\n")
                return


# END OF FUNCTION


def poll_routine(polls: list[dict[str, Any]], options: dict[Id, PartialModel]) -> None:
    """
    Purpose:
        Alters all poll models specified by the new vote service.
    Input:
        - polls: list of polls that shall be modified. Needs 'fqid' and 'data'.
        - options: options containing all necessary information.
    Returns:
        n/a
    Commentary:
        changes to poll
        type'analog', 'named', 'pseudoanonymous', 'cryptographic' -> visibility'manually', 'named', 'secret'
        pollmethod -> method 'approval', 'selection', 'rating-score', 'rating-approval'
        state `published` -> `finished` + published boolean
        x -> config?
            min_votes_amount
            max_votes_amount
            max_votes_per_option
            global_yes
            global_no
            global_abstain
            onehundred_percent_base TODO after the client is done
            entitled_users_at_stop TODO after the client is done
        x -> result?
            option_ids
            global_option_id
            votesvalid
            votesinvalid
            votescast
    """
    for poll in polls:
        collection, id_ = collection_and_id_from_fqid(poll["fqid"])
        data = poll["data"]
        result = dict()
        config = dict()

        # for config
        global_no = data.pop("global_no", None)
        global_yes = data.pop("global_yes", None)
        global_abstain = data.pop("global_abstain", None)
        min_votes_amount = data.pop("min_votes_amount", None)
        max_votes_amount = data.pop("max_votes_amount", None)
        max_votes_per_option = data.pop("max_votes_per_option", None)
        onehundred_percent_base = data.pop("onehundred_percent_base", None)
        entitled_users_at_stop = data.pop("entitled_users_at_stop", None)
        config["global_no"] = global_no
        config["global_yes"] = global_yes
        config["global_abstain"] = global_abstain
        config["min_votes_amount"] = min_votes_amount
        config["max_votes_amount"] = max_votes_amount
        config["max_votes_per_option"] = max_votes_per_option
        config["onehundred_percent_base"] = onehundred_percent_base
        config["entitled_users_at_stop"] = entitled_users_at_stop

        # for result
        option_ids = data.pop("option_ids", None)
        global_option_id = data.pop("global_option_id", None)
        votesvalid = data.pop("votesvalid", None)
        votesinvalid = data.pop("votesinvalid", None)
        votescast = data.pop("votescast", None)
        result["option_ids"] = option_ids
        result["global_option_id"] = global_option_id
        result["votesvalid"] = votesvalid
        result["votesinvalid"] = votesinvalid
        result["votescast"] = votescast

        content_object_type = collection_from_fqid(data["content_object_id"])

        pollmethod = data.pop("pollmethod")

        type_ = data.pop("type")
        match type_:
            case "analog":
                data["visibility"] = "manually"
            case "pseudoanonymous", "cryptographic":
                data["visibility"] = "secret"
            case _:
                data["visibility"] = type_

        if (state := data.get("state", "")) and state == "published":
            data["state"] = "finished"
            data["published"] = True

        match content_object_type:
            case "motion":
                data["method"] = "approval"
                result = dict() if pollmethod == "YNA" else {"allow_abstain": False}
            case "assignment" | "topic":
                data["method"] = "rating-approval"
                result = dict() if pollmethod == "YNA" else {"allow_abstain": False}
            case _:
                raise Exception(
                    f"Polls with this content object type ({content_object_type}) do not exist."
                )

        if option_id := data.pop("option_id", 0):
            option = options[option_id]
            result["option_ids?"] = option["content_object_id?"]

        data["result"] = json_dumps(result)
        data["config"] = json_dumps(config)


def vote_routine(votes: list[dict[str, Any]], options: dict[Id, PartialModel]) -> None:
    """
    Purpose:
        Alters all vote models specified by the new vote service.
    Input:
        - votes: list of votes that shall be modified. Needs 'fqid' and 'data'.
        - options: options containing all necessary information.
    Returns:
        n/a
    Commentary:
        changes to vote
        pop option_id
        poll_id = option/poll_id
    """
    for vote in votes:
        collection, id_ = collection_and_id_from_fqid(vote["fqid"])
        data = vote["data"]
        if option_id := data.pop("option_id", 0):
            option = options[option_id]
            data["poll_id"] = option["poll_id"]


def pre_migration() -> None:
    """
    Purpose:
        Migrates all vote_service related models so that the data will fit the table scheme.
    Input:
        n/a
    Returns:
        n/a
    """
    definitions: dict = {
        "poll": {
            "del": [
                "description",
                "backend",
                "is_pseudoanonymized",
                "live_voting_enabled",
                "live_votes",
                "crypt_key",
                "crypt_signature",
                "votes_raw",
                "votes_signature",
            ],
            "routine": poll_routine,
        },
        "user": {
            "del": ["option_ids"],
            "renames": {
                "vote_ids": "acting_vote_ids",
                "delegated_vote_ids": "represented_vote_ids",
            },
        },
        "motion": {"del": ["option_ids"]},
        "meeting": {
            "del": ["option_ids", "vote_ids", "poll_default_backend"],
            "set": {
                "poll_default_allow_invalid": False,
                "poll_default_allow_vote_split": False,
            },
        },
        "vote": {
            "del": ["meeting_id", "option_id"],
            "renames": {
                "user_id": "acting_user_id",
                "delegated_user_id": "represented_user_id",
            },
            "routine": vote_routine,
        },
        "assignment": {"del": ["option_id"]},
        "organization": {"del": ["vote_decrypt_public_main_key"]},
    }

    # 1) Prepare connection & cursor
    with os_conn_pool.connection() as conn:
        with conn.cursor() as cur:

            # 2) BEGIN TRANSACTION
            with conn.transaction():
                # 2.1) Get options out of the way
                # needed to generate poll/result and vote
                cur.execute(Sql_helper.get_select_collection_command("option", ["*"]))
                options = {
                    id_from_fqid(elem["fqid"]): elem["data"] for elem in cur.fetchall()
                }
                cur.execute("DELETE FROM models WHERE fqid LIKE 'option/%';")

                for collection, definition in definitions.items():
                    cur.execute(
                        Sql_helper.get_select_collection_command(collection, ["*"])
                    )
                    result = cur.fetchall()
                    # 2.2) Do generic changes: Delete, rename, set
                    for elem in result:
                        collection, id_ = collection_and_id_from_fqid(elem["fqid"])
                        data = elem["data"]
                        for field_name in definition.get("del", []):
                            data.pop(field_name, None)
                        for old_field, new_field in definition.get(
                            "renames", {}
                        ).items():
                            data[new_field] = data.pop(old_field, None)
                        if "set" in definition:
                            data.update(definition["set"])
                    # 2.3) Run routine
                    if "routine" in definition:
                        definition["routine"](result, options)
                    # 3) Apply changes for collection
                    cur.executemany(*Sql_helper.get_update_models_command(result))


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
    pre_migration()

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
            # Delete old tables
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
                cur.execute(f"DROP TABLE {table_name} CASCADE;")
        # 8) Exit cursor
    # 9) Exit connection


# END OF FUNCTION
