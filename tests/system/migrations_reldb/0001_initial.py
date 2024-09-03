# BUILTIN IMPORTS
import json
from importlib import import_module

# OPENSLIDES IMPORTS
from openslides_backend.database.db_connection_handling import os_conn_pool
from openslides_backend.models.base import Model

# ENV Variables
EXAMPLE_DATA_PATH = "global/data/example-data.json"
TEST_MODULE_PATH = "openslides_backend.migrations.migrations_reldb.0001_test"

# VARIABLE DECLARATION

test_module = import_module(TEST_MODULE_PATH)
created_fqids: set()
data: dict[str, any] = {}


# FUNCTION DEFINITION
def insert_model_into_models(fqid: str, model: type["Model"]) -> None:
    sql_command: str

    sql_command = f"INSERT INTO models VALUES ('{fqid}','{model}',false,now());"

    with os_conn_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_command)


def clear_models() -> None:
    with os_conn_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE models;")


# MAIN PROGRAM
if __name__ == "__main__":
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
    clear_models()

    # 4) Write models into db table models
    for fqid, model in data.items():
        json_blob = json.dumps(model)

        insert_model_into_models(fqid, json_blob)

    # 5) Call data_manipulation of module
    test_module.data_manipulation()


# END MAIN PROGRAM
