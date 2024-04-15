import os
from typing import TypedDict
from unittest import TestCase

from psycopg2 import connect


class WritePayload(TypedDict):
    table: str
    fields: list[str]
    rows: list[tuple]


class BaseRelationalDBTestCase(TestCase):
    def setUp(self) -> None:
        self._filled_tables_cache: list[str] = []

    def tearDown(self) -> None:
        self._clearDB()
        return super().tearDown()

    def write_data(self, payloads: list[WritePayload]) -> None:
        env = os.environ
        connect_data = f"dbname='{env['DATABASE_NAME']}' user='{env['DATABASE_USER']}' host='{env['DATABASE_HOST']}' password='{env['PGPASSWORD']}'"
        conn = connect(connect_data)

        with conn:
            with conn.cursor() as cursor:
                for payload in payloads:
                    query = f"INSERT INTO {payload['table']} ({', '.join(payload['fields'])}) VALUES {', '.join(['%s' for i in range(len(payload['rows']))])}"
                    cursor.execute(query, payload["rows"])
            conn.commit()
        conn.close()
        self._filled_tables_cache = list({payload["table"] for payload in payloads})

    def _clearDB(self) -> None:
        if self._filled_tables_cache:
            env = os.environ
            connect_data = f"dbname='{env['DATABASE_NAME']}' user='{env['DATABASE_USER']}' host='{env['DATABASE_HOST']}' password='{env['PGPASSWORD']}'"
            conn = connect(connect_data)

            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"TRUNCATE {', '.join(self._filled_tables_cache)} CASCADE"
                    )
                conn.commit()
            conn.close()
            self._filled_tables_cache = []
