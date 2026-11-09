from typing import Any

from psycopg import Cursor
from psycopg.rows import DictRow

from openslides_backend.migrations.base import BaseMigration


class Migration(BaseMigration):
    ORIGIN_COLLECTIONS = ["meeting"]

    @staticmethod
    def data_manipulation(curs: Cursor[DictRow], stash: dict[str, Any] | None) -> None:
        curs.execute(
            "UPDATE meeting_t SET motions_enable_consultation_sequence = false;"
        )
