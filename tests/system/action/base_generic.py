import re

import yaml

from meta.dev.src.generate_sql_schema import GenerateCodeBlocks, InternalHelper
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)

from .base import BaseActionTestCase


class BaseGenericTestCase(BaseActionTestCase):
    """
    Base class for systematic testing of generic action classes
    with new abstract collections.

    If `yml` is provided, the class creates all the described tables along with
    the related views and triggers. After all tests in the class finish, all
    generated database objects are removed again.

    After each individual test, generated tables are truncated to ensure clean state.
    """

    tables_to_reset: list[str]
    trigger_table_map: dict[str, str]
    yml: str

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if cls.yml:
            cls.create_table_view(cls.yml)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        if not cls.yml:
            return

        with get_new_os_conn() as conn, conn.cursor() as curs:
            curs.execute(
                "".join(
                    f"DROP TRIGGER IF EXISTS {trigger} ON {table};"
                    for trigger, table in getattr(cls, "trigger_table_map", {}).items()
                )
            )
            curs.execute(
                "".join(
                    f"""DROP TABLE IF EXISTS {table} CASCADE;"""
                    for table in getattr(cls, "tables_to_reset", [])
                )
            )

    def tearDown(self) -> None:
        super().tearDown()
        if self.tables_to_reset:
            with self.connection.cursor() as curs:
                curs.execute(
                    "".join(
                        f"""TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"""
                        for table in self.tables_to_reset
                    )
                )

    @classmethod
    def create_table_view(cls, yml: str) -> None:
        GenerateCodeBlocks.models = InternalHelper.MODELS = yaml.safe_load(yml)

        (
            pre_code,
            table_name_code,
            view_name_code,
            alter_table_code,
            final_info_code,
            missing_handled_attributes,
            im_table_code,
            create_trigger_partitioned_sequences_code,
            create_trigger_1_1_relation_not_null_code,
            create_trigger_relationlistnotnull_code,
            create_trigger_unique_ids_pair_code,
            create_trigger_notify_code,
            errors,
        ) = GenerateCodeBlocks.generate_the_code()

        sql = (
            table_name_code
            + im_table_code
            + view_name_code
            + alter_table_code
            + create_trigger_1_1_relation_not_null_code
            + create_trigger_relationlistnotnull_code
            + create_trigger_unique_ids_pair_code
        )
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                curs.execute(sql)
        cls.extract_sql_objects(sql)

    @classmethod
    def extract_sql_objects(cls, sql: str) -> None:
        """
        Populate:
            - cls.trigger_table_map = {trigger_name: table_name}
            - cls.tables_to_reset = [table_name, ...]
        """
        trigger_map_pattern = re.compile(
            r"CREATE\s+(?:CONSTRAINT\s+)?TRIGGER\s+"
            r"(tr_[a-zA-Z0-9_]+)"
            r".+?ON\s+([a-zA-Z0-9_.]+)",
            re.IGNORECASE | re.DOTALL,
        )

        table_pattern = re.compile(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
            r"([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)",
            re.IGNORECASE,
        )

        cls.trigger_table_map = {
            trigger: table for trigger, table in trigger_map_pattern.findall(sql)
        }
        cls.tables_to_reset = table_pattern.findall(sql)
