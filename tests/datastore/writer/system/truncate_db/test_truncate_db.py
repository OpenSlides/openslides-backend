import pytest

from openslides_backend.datastore.shared.di import injector
from openslides_backend.datastore.shared.postgresql_backend import ALL_TABLES
from openslides_backend.datastore.shared.services import EnvironmentService
from openslides_backend.datastore.shared.services.environment_service import (
    DATASTORE_DEV_MODE_ENVIRONMENT_VAR,
)
from openslides_backend.datastore.writer.flask_frontend.routes import TRUNCATE_DB_URL
from tests.datastore.util import assert_response_code


def test_truncate_db(db_connection, db_cur, json_client):
    db_cur.execute("insert into positions (user_id, migration_index) values (1, 1)")
    db_cur.execute(
        "insert into events (position, fqid, type, weight) values (1, 'a/1', 'create', 1)"
    )
    db_cur.execute("insert into id_sequences values ('c', 1)")
    db_cur.execute(
        "insert into collectionfields (collectionfield, position) values ('c/f', 1)"
    )
    db_cur.execute("insert into events_to_collectionfields values (1, 1)")
    db_cur.execute("insert into models values ('c/1', '{}', TRUE)")
    db_connection.commit()

    response = json_client.post(TRUNCATE_DB_URL, {})
    assert_response_code(response, 204)

    with db_connection.cursor() as cursor:
        for table in ALL_TABLES:
            cursor.execute(f"select * from {table}")
            assert cursor.fetchone() is None


GLOB = {}


@pytest.mark.skip(reason="Only for performance testing")
def test_truncate_db_perf(db_connection, db_cur, json_client):
    from time import time
    from unittest.mock import patch

    GLOB["orig_post"] = json_client.post
    GLOB["tot"] = 0
    count = 100

    def post(*args, **kwargs):
        start = time()
        result = GLOB["orig_post"](*args, **kwargs)
        GLOB["tot"] += time() - start
        return result

    with patch.object(json_client, "post", post):
        for i in range(count):
            test_truncate_db(db_connection, db_cur, json_client)
    tot = GLOB["tot"]
    print(f"Total: {tot}")
    print(f"per call: {tot / count}")


def test_not_found_in_non_dev(json_client):
    injector.get(EnvironmentService).set(DATASTORE_DEV_MODE_ENVIRONMENT_VAR, "0")
    response = json_client.post(TRUNCATE_DB_URL, {})
    assert_response_code(response, 404)
