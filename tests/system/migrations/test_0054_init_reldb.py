# BUILTIN IMPORTS
import json
from importlib import import_module

# OPENSLIDES IMPORTS
from openslides_backend.database.db_connection_handling import os_conn_pool

# ENV Variables
EXAMPLE_DATA_PATH = "global/data/example-data.json"
TEST_MODULE_PATH = "openslides_backend.migrations.migrations_reldb.0054_init_reldb"

# VARIABLE DECLARATION

test_module = import_module(TEST_MODULE_PATH)
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

    # 5) Call data_manipulation of module
    test_module.data_definition()
    test_module.data_manipulation()

    # 6) TEST CASES
    with os_conn_pool.connection() as conn:
        with conn.cursor() as cur:
            # 6.1) 1:1 relation
            cur.execute("SELECT theme_id FROM organization_t WHERE id=1;")
            assert cur.fetchone() is not None

            # 6.2) generic n:m relation
            cur.execute(
                "SELECT tagged_id FROM gm_organization_tag_tagged_ids_t WHERE organization_tag_id=1 AND tagged_id LIKE 'committee/1';"
            )
            assert cur.fetchone() is not None
            cur.execute(
                "SELECT tagged_id FROM gm_organization_tag_tagged_ids_t WHERE organization_tag_id=1 AND tagged_id LIKE 'meeting/1';"
            )
            assert cur.fetchone() is not None

            # 6.3) n:m relation
            cur.execute(
                "SELECT user_id FROM nm_committee_user_ids_user_t WHERE committee_id=1 ORDER BY user_id;"
            )
            res = cur.fetchall()
            assert (
                res[0]["user_id"] == 1
                and res[1]["user_id"] == 2
                and res[2]["user_id"] == 3
            )
    # END TEST CASES


# END TEST
if __name__ == "__main__":
    test_migration()
