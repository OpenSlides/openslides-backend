# BUILTIN IMPORTS
import json
import os
from copy import deepcopy
from datetime import datetime, timedelta
from importlib import import_module
from time import sleep
from typing import cast
from unittest import TestCase
from unittest.mock import _patch

import pytest
from psycopg.errors import UndefinedTable

from openslides_backend.http.application import OpenSlidesBackendWSGIApplication
from openslides_backend.http.views import ActionView
from openslides_backend.migrations.migration_handler import MigrationHandler
# OPENSLIDES IMPORTS
from openslides_backend.migrations.migration_helper import (
    LAST_NON_REL_MIGRATION,
    MigrationHelper,
    MigrationState,
)
from openslides_backend.migrations.migration_manager import MigrationManager
from openslides_backend.services.auth.interface import AuthenticationService
from openslides_backend.services.postgresql.create_schema import (
    create_db,
    create_schema,
    drop_db,
)
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
    get_unpooled_db_connection,
    os_conn_pool,
)
from openslides_backend.shared.env import DEV_PASSWORD, Environment
from tests.conftest import OLD_TABLES, get_rel_db_table_names
from tests.conftest_helper import generate_sql_for_test_initiation
from tests.system.action.util import get_internal_auth_header
from tests.system.util import create_action_test_application, get_route_path
from tests.util import AuthData, Client, Response

migration_module = import_module(
    "openslides_backend.migrations.migrations_reldb.0071_init_reldb"
)
# ENV Variables
EXAMPLE_DATA_PATH = "data/example-data.json"

# VARIABLE DECLARATION
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
MIGRATIONS_URL = get_route_path(ActionView.migrations_route)
created_fqids: set()
data: dict[str, any] = {}


class BaseMigrationTestCase(TestCase):
    app: OpenSlidesBackendWSGIApplication
    auth: AuthenticationService
    # Save auth data as class variable
    auth_data: AuthData | None = None
    auth_mockers: dict[str, _patch]

    @classmethod
    def tearDownClass(cls) -> None:
        # 8) Final Cleanup
        drop_db()
        cls.apply_test_relational_schema()
        super().tearDownClass()

    @staticmethod
    def apply_test_relational_schema() -> None:
        create_schema()
        with get_unpooled_db_connection("openslides") as conn:
            with conn.cursor() as curs:
                table_names = get_rel_db_table_names(curs)
                curs.execute(generate_sql_for_test_initiation(tuple(table_names)))

    def tearDown(self) -> None:
        migration_module.Sql_helper.offset = 0
        MigrationHelper.table_translations = dict()

    def setUp(self):
        # 1) Create old idempotent key-value-store schema and relational schema on top
        # self.drop_tables()
        drop_db()
        create_db()
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                path = os.path.realpath(
                    os.path.join(
                        os.getcwd(),
                        "openslides_backend",
                        "services",
                        "postgresql",
                        "schema.sql",
                    )
                )
                curs.execute(open(path).read())

        # 1.1) Create services and login.
        self.app = create_action_test_application()
        # self.logger = cast(MagicMock, self.app.logger)
        self.services = self.app.services
        self.env = cast(Environment, self.app.env)
        self.auth = self.services.authentication()
        self.client = Client(self.app)
        self.client.auth = self.auth  # type: ignore
        if self.auth_data:
            # Reuse old login data to avoid a new login request
            self.client.update_auth_data(self.auth_data)
        else:
            self.auth.create_update_user_session(
                {
                    "type": "create",
                    "fqid": "user/1",
                    "fields": {
                        "username": ADMIN_USERNAME,
                        "password": self.auth.hash(ADMIN_PASSWORD),
                    },
                }
            )
            # Login and save copy of auth data for all following tests
            self.client.login(ADMIN_USERNAME, ADMIN_PASSWORD, 1)
            BaseMigrationTestCase.auth_data = deepcopy(self.client.auth_data)

        self.setup_data()
        self.apply_test_relational_schema()

    # def check_auth_mockers_started(self) -> bool:
    #     if (
    #         hasattr(self, "auth_mockers")
    #         and not self.auth_mockers["auth_http_adapter_patch"]._active_patches  # type: ignore
    #     ):
    #         return False
    #     return True

    def request(
        self,
        command: str,
        lang: str | None = None,
    ) -> Response:
        # if not self.check_auth_mockers_started():
        #     raise Exception("Argh")
        headers = get_internal_auth_header(DEV_PASSWORD)
        if lang:
            headers["Accept-Language"] = lang
        response = self.client.post(
            MIGRATIONS_URL, json={"cmd": command, "verbose": True}, headers=headers
        )
        if response.status_code == 200:
            results = response.json.get("results", {})
            assert results == {}
        return response

    def setup_data(self) -> None:
        raw_data: dict[str, any]
        json_blob: str

        # 2) reading json data from file
        with open(EXAMPLE_DATA_PATH) as file:
            raw_data = json.loads(file.read())

        # 2.1) fill data dictionary without meta_ fields and _migration_index
        for collection, models in raw_data.items():
            if collection == "_migration_index":
                continue
            for model_id, model in models.items():
                data[f"{collection}/{model_id}"] = {
                    f: v for f, v in model.items() if not f.startswith("meta_")
                }

        # 3) Open os_connection_pool
        os_conn_pool.open()

        # 4) Write models into db table models
        with os_conn_pool.connection() as conn:
            with conn.cursor() as curs:
                # 4.D1) clears models table
                curs.execute("TRUNCATE TABLE models;")

                # 4.1) Actual writing of models into table
                for fqid, model in data.items():
                    json_blob = json.dumps(model)
                    curs.execute(
                        "INSERT INTO models VALUES (%s, %s, false, now());",
                        [fqid, json_blob],
                    )

                # 4.2) Write Migration Index like Docker setup would expect
                curs.execute(
                    f"INSERT INTO positions (timestamp, user_id, migration_index) VALUES ('2020-05-20', 1, {LAST_NON_REL_MIGRATION})"
                )

    def check_data(self) -> None:
        # 6) TEST CASES
        with os_conn_pool.connection() as conn:
            with conn.cursor() as cur:
                # 6.1) 1:1 relation
                result = cur.execute(
                    "SELECT theme_id FROM organization_t WHERE id=1;"
                ).fetchone()
                assert result is not None, "1:1 relation in organization not filled."

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

        # 6.5) Deleted old table schema
        for table_name in OLD_TABLES:
            with os_conn_pool.connection() as conn:
                with conn.cursor() as cur:
                    with pytest.raises(UndefinedTable):
                        cur.execute(f"SELECT * FROM {table_name};")
        # END TEST CASES

    def test_migration_handler(self) -> None:
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
            Also it is tested that the new tables are created on top of an old basis and the old tables are deleted.
            It should be only used like this in this migration test since it leads to a performance problem
            once the actual connection context is entered the first time after the database was dropped and recreated.
        """
        # 5) Call data_manipulation of module
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                # Prepare what manager does.
                MigrationHelper.load_migrations()
                MigrationHelper.add_new_migrations_to_version()
                handler = MigrationHandler(
                    curs, self.env, self.services, self.app.logging
                )
                handler.execute_command("migrate")

                # 6.4) Inserted new migration_index and state
                curs.execute("SELECT migration_index, migration_state FROM version;")
                assert curs.fetchall() == [
                    {
                        "migration_index": LAST_NON_REL_MIGRATION,
                        "migration_state": MigrationState.NO_MIGRATION_REQUIRED,
                    },
                    {
                        "migration_index": LAST_NON_REL_MIGRATION + 1,
                        "migration_state": MigrationState.FINALIZATION_REQUIRED,
                    },
                ]
        self.check_data()

    def test_migration_manager(self) -> None:
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
            Also it is tested that the new tables are created on top of an old basis and the old tables are deleted.
            It should be only used like this in this migration test since it leads to a performance problem
            once the actual connection context is entered the first time after the database was dropped and recreated.
        """

        # 5) Call data_manipulation of module
        manager = MigrationManager(self.env, self.services, self.app.logging)
        print(manager.handle_request({"cmd": "migrate", "verbose": True}))

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                while (
                    MigrationHelper.get_migration_state(curs)
                    != MigrationState.FINALIZATION_REQUIRED
                ):
                    curs.connection.commit()
                    sleep(1)

                # 6.4) Inserted new migration_index and state
                curs.execute("SELECT migration_index, migration_state FROM version;")
                assert curs.fetchall() == [
                    {
                        "migration_index": LAST_NON_REL_MIGRATION,
                        "migration_state": MigrationState.NO_MIGRATION_REQUIRED,
                    },
                    {
                        "migration_index": LAST_NON_REL_MIGRATION + 1,
                        "migration_state": MigrationState.FINALIZATION_REQUIRED,
                    },
                ]
        self.check_data()

    def test_migration_route_0(self) -> None:
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
            Also it is tested that the new tables are created on top of an old basis and the old tables are deleted.
            It should be only used like this in this migration test since it leads to a performance problem
            once the actual connection context is entered the first time after the database was dropped and recreated.
            # TODO store a copy of example_json before this gets merged.
        """

        # 5) Call data_manipulation of module
        # Future migrations do not need to test all commands. Finalize should be sufficient. Or call MigrationHelper().run_migrations() directly.

        # TODO do response checks in test_migration_route.py if possible
        response = self.request("stats")
        assert response.json == {
            "success": True,
            "stats": {
                # TODO only migrate one index? Would require altering the test-visible migration files.
                "status": MigrationState.MIGRATION_REQUIRED,
                "current_migration_index": LAST_NON_REL_MIGRATION,
                "target_migration_index": LAST_NON_REL_MIGRATION + 1,
                "migratable_models": {
                    "agenda_item": {"count": 15},
                    "assignment": {"count": 2},
                    "assignment_candidate": {"count": 5},
                    "chat_group": {"count": 2},
                    "committee": {"count": 1},
                    "gender": {"count": 4},
                    "group": {"count": 5},
                    "list_of_speakers": {"count": 16},
                    "mediafile": {"count": 1},
                    "meeting": {"count": 1},
                    "meeting_mediafile": {"count": 1},
                    "meeting_user": {"count": 3},
                    "motion": {"count": 4},
                    "motion_block": {"count": 1},
                    "motion_category": {"count": 2},
                    "motion_change_recommendation": {"count": 2},
                    "motion_comment": {"count": 1},
                    "motion_comment_section": {"count": 1},
                    "motion_state": {"count": 15},
                    "motion_submitter": {"count": 4},
                    "motion_workflow": {"count": 2},
                    "organization": {"count": 1},
                    "organization_tag": {"count": 1},
                    "personal_note": {"count": 1},
                    "poll": {"count": 5},
                    "projection": {"count": 4},
                    "projector": {"count": 2},
                    "projector_countdown": {"count": 2},
                    "projector_message": {"count": 1},
                    "speaker": {"count": 13},
                    "structure_level": {"count": 3},
                    "tag": {"count": 3},
                    "theme": {"count": 3},
                    "topic": {"count": 8},
                    "user": {"count": 3},
                    "vote": {"count": 9},
                },
            },
        }
        response = self.request("migrate")
        assert response.json == {
            "success": True,
            "status": MigrationState.MIGRATION_RUNNING,
            "output": "",
        }

        response = self.request("stats")
        assert response.json == {
            "success": True,
            "stats": {
                "status": MigrationState.MIGRATION_RUNNING,
                "current_migration_index": LAST_NON_REL_MIGRATION,
                "target_migration_index": LAST_NON_REL_MIGRATION + 1,
                "migratable_models": {},
            },
        }

        # Wait for migrate with a sec delay per iteration.
        max_time = timedelta(seconds=15)
        start = datetime.now()
        while (response := self.request("progress").json) != {
            "success": True,
            "status": MigrationState.FINALIZATION_REQUIRED,
            "output": "",
        }:
            sleep(1)
            print(response)
            if datetime.now() - start > max_time:
                raise Exception(
                    f"The migration doesn't finish in {max_time}. {response}"
                )
        print(response)

        response = self.request("finalize")
        assert response.json == {
            "success": True,
            "status": MigrationState.FINALIZATION_REQUIRED,
            "output": "",
        }

        start = datetime.now()
        while (response := self.request("migrate").json) == {
            "success": False,
            "message": "Migration is running, only 'stats' command is allowed",
        }:
            sleep(1)
            print(response)
            if datetime.now() - start > max_time:
                raise Exception(
                    f"The migration doesn't finish in {max_time}. {response}"
                )
        sleep(1)
        assert response == {
            "success": True,
            "status": MigrationState.NO_MIGRATION_REQUIRED,
            "output": "",
        }

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                # 6.4) Inserted new migration_index and state
                curs.execute("SELECT migration_index, migration_state FROM version;")
                for idx, row in enumerate(curs.fetchall(), LAST_NON_REL_MIGRATION):
                    assert {
                        "migration_index": idx,
                        "migration_state": MigrationState.NO_MIGRATION_REQUIRED,
                    } == row
        self.check_data()

    def test_migration_route_1(self) -> None:
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
            Also it is tested that the new tables are created on top of an old basis and the old tables are deleted.
            It should be only used like this in this migration test since it leads to a performance problem
            once the actual connection context is entered the first time after the database was dropped and recreated.
            # TODO store a copy of example_json before this gets merged.
        """

        # 5) Call data_manipulation of module
        # Future migrations do not need to test all commands. Finalize should be sufficient. Or call MigrationHelper().run_migrations() directly.

        response = self.request("finalize")
        assert response.json == {
            "success": True,
            "status": MigrationState.MIGRATION_RUNNING,
            "output": "",
        }

        # Wait for migrate with a sec delay per iteration.
        max_time = timedelta(seconds=15)
        start = datetime.now()
        while (response := self.request("migrate").json) != {
            "success": True,
            "status": MigrationState.NO_MIGRATION_REQUIRED,
            "output": "",
        }:
            # while (response := self.request("migrate").json) == {'success': False, 'message': "Migration is running, only 'stats' command is allowed"}:
            sleep(1)
            print(response)
            if datetime.now() - start > max_time:
                raise Exception(
                    f"The migration doesn't finish in {max_time}. {response}"
                )
        sleep(1)
        assert response == {
            "success": True,
            "status": MigrationState.NO_MIGRATION_REQUIRED,
            "output": "",
        }

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                # 6.4) Inserted new migration_index and state
                curs.execute("SELECT migration_index, migration_state FROM version;")
                for idx, row in enumerate(curs.fetchall(), LAST_NON_REL_MIGRATION):
                    assert {
                        "migration_index": idx,
                        "migration_state": MigrationState.NO_MIGRATION_REQUIRED,
                    } == row

        self.check_data()
