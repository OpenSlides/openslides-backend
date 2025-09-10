import yaml

from meta.dev.src.generate_sql_schema import GenerateCodeBlocks, InternalHelper
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
)

from .base import BaseActionTestCase


class BaseGenericTestCase(BaseActionTestCase):
    """Base test class meant for systematic testing of generic action classes with new abstract collections."""

    tables_to_reset: list[str]
    yml: str

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if cls.yml:
            cls.create_table_view(cls.yml)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    "".join(
                        f"""DROP TABLE {table} CASCADE;"""
                        for table in cls.tables_to_reset
                    )
                )

    def tearDown(self) -> None:
        super().tearDown()
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
            create_trigger_1_1_relation_not_null_code,
            create_trigger_relationlistnotnull_code,
            create_trigger_unique_ids_pair_code,
            create_trigger_notify_code,
            errors,
        ) = GenerateCodeBlocks.generate_the_code()
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                curs.execute(
                    table_name_code
                    + im_table_code
                    + view_name_code
                    + alter_table_code
                    #  + create_trigger_1_1_relation_not_null_code
                    + create_trigger_relationlistnotnull_code
                    + create_trigger_unique_ids_pair_code
                )
        return
