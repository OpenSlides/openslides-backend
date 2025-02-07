import json
from typing import Any

from psycopg import Connection, Cursor

from openslides_backend.shared.patterns import strip_reserved_fields


# TODO use cursor from connection directly?
def setup_data(
    connection: Connection, cursor: Cursor, data: dict[str, dict[str, Any]]
) -> None:
    for collection, models in data.items():
        for model in models.values():
            model_data = json.loads(json.dumps(model))
            strip_reserved_fields(model_data)
            cursor.execute(
                f"INSERT INTO {collection}_t ({', '.join(key for key in model_data.keys())}) VALUES ({', '.join('%s' for i in range(len(model_data)))})",
                [val for val in model_data.values()],
            )
    connection.commit()
