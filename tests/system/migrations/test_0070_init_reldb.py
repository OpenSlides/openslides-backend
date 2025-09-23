# BUILTIN IMPORTS
import json

import pytest
from psycopg.errors import UndefinedTable

# OPENSLIDES IMPORTS
from openslides_backend.migrations.migration_helper import (
    LAST_NON_REL_MIGRATION,
    MigrationHelper,
)
from openslides_backend.services.postgresql.create_schema import create_schema
from openslides_backend.services.postgresql.db_connection_handling import os_conn_pool

# ENV Variables
EXAMPLE_DATA_PATH = "data/example-data.json"

# VARIABLE DECLARATION

# test_module = import_module(TEST_MODULE_PATH)
created_fqids: set()
data: dict[str, any] = {}


# MAIN PROGRAM
def test_migration() -> None:
    """
    Purpose:
        Default method used for the test framework.(?)
    Input:
        n/a
    Returns:
        n/a
    Commentary:
        The test cases initially may seem to be spartanic caused by the lack of testing of integrity
        after transfering the data from the key-value-store into their respective tables.

        What is tested is the correct creation of intermediate tables and simple relations exemplary as we
        can trust that it works for other tables if it worked for one.

        TODO: Implementing further test cases if needed.
    """
    raw_data: dict[str, any]
    json_blob: str
    # 0) Create schema
    create_schema()

    # 1) reading json data from file
    with open(EXAMPLE_DATA_PATH) as file:
        raw_data = json.loads(file.read())

    # 2) fill data dictionary
    for collection, models in raw_data.items():
        # 2.1) skip migration_index
        if collection == "_migration_index":
            continue
        # 2.2) do stuff.
        for model_id, model in models.items():
            data[f"{collection}/{model_id}"] = {
                f: v for f, v in model.items() if not f.startswith("meta_")
            }

    # 3) Open os_connection_pool
    os_conn_pool.open()

    # 4) Write models into db table models
    with os_conn_pool.connection() as conn:
        with conn.cursor() as cur:
            # 4.D1) clears models table
            cur.execute("TRUNCATE TABLE models;")

            # 4.1) Actual writing of models into table
            for fqid, model in data.items():
                json_blob = json.dumps(model)
                cur.execute(
                    "INSERT INTO models VALUES (%s, %s, false, now());",
                    [fqid, json_blob],
                )

            # 4.2) Write Migration Index
            cur.execute(
                f"INSERT INTO positions (timestamp, user_id, migration_index) VALUES ('2020-05-20', 1, {LAST_NON_REL_MIGRATION})"
            )

    # 5) Call data_manipulation of module
    MigrationHelper().run_migrations()

    # 6) TEST CASES
    with os_conn_pool.connection() as conn:
        with conn.cursor() as cur:
            # 6.1) 1:1 relation
            cur.execute("SELECT theme_id FROM organization_t WHERE id=1;")
            assert cur.fetchone() is not None

            # 6.1.1) 1G:1 relation
            cur.execute(
                "SELECT type, content_object_id, content_object_id_motion_id, content_object_id_topic_id FROM agenda_item_t WHERE id=1;"
            )
            assert cur.fetchone() == {
                "type": "common",
                "content_object_id": "motion/1",
                "content_object_id_motion_id": 1,
                "content_object_id_topic_id": None,
            }

            # 6.2) 1:n relation
            cur.execute("SELECT gender_id FROM user_t WHERE id=1;")
            assert cur.fetchone() == {"gender_id": 1}

            # 6.2.1) 1G:n relation
            cur.execute(
                "SELECT title, content_object_id, content_object_id_motion_id, content_object_id_topic_id FROM poll_t WHERE id=1;"
            )
            assert cur.fetchone() == {
                "title": "1",
                "content_object_id": "motion/1",
                "content_object_id_motion_id": 1,
                "content_object_id_topic_id": None,
            }

            # 6.3) n:m relation
            cur.execute(
                "SELECT user_id, committee_id FROM nm_committee_manager_ids_user_t WHERE committee_id=1 ORDER BY user_id;"
            )
            assert cur.fetchall() == [{"user_id": 1, "committee_id": 1}]
            # 6.3.1) nG:m relation
            cur.execute(
                "SELECT tagged_id FROM gm_organization_tag_tagged_ids_t WHERE organization_tag_id=1 AND tagged_id LIKE 'committee/1';"
            )
            assert cur.fetchone() is not None
            cur.execute(
                "SELECT tagged_id FROM gm_organization_tag_tagged_ids_t WHERE organization_tag_id=1 AND tagged_id LIKE 'meeting/1';"
            )
            assert cur.fetchone() is not None

            old_tables = (
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

            # 6.4) Inserted new migration_index
            cur.execute("SELECT migration_index FROM version;")
            assert cur.fetchone() == {"migration_index": LAST_NON_REL_MIGRATION + 1}

    # 6.5) Deleted old table schema
    for table_name in old_tables:
        with os_conn_pool.connection() as conn:
            with conn.cursor() as cur:
                with pytest.raises(UndefinedTable):
                    cur.execute(f"SELECT * FROM {table_name};")
    # END TEST CASES


# END TEST
if __name__ == "__main__":
    test_migration()
