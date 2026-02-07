# BUILTIN IMPORTS
import json
import os
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime, timedelta
from importlib import import_module
from io import StringIO
from threading import Lock
from time import sleep
from typing import Any, cast
from unittest import TestCase
from unittest.mock import DEFAULT as mockdefault
from unittest.mock import Mock, _patch, patch

from meta.dev.src.generate_sql_schema import GenerateCodeBlocks
from openslides_backend.http.application import OpenSlidesBackendWSGIApplication
from openslides_backend.http.views import ActionView
from openslides_backend.migrations.migration_handler import MigrationHandler
from openslides_backend.migrations.migration_helper import (
    MIN_NON_REL_MIGRATION,
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
    "openslides_backend.migrations.migrations.0100_init_reldb"
)

# VARIABLE DECLARATION
EXAMPLE_DATA_PATH = os.path.realpath(
    os.path.join(
        os.getcwd(), "tests", "system", "migrations", "legacy-example-data.json"
    )
)
DEPR_SQL_PATH = os.path.realpath(
    os.path.join(os.getcwd(), "tests", "system", "migrations", "deprecated_schema.sql")
)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
MIGRATIONS_URL = get_route_path(ActionView.migrations_route)
created_fqids: set()
data: dict[str, any] = {}


class BaseMigrationTestCase(TestCase):
    """
    Commentary:
        The test cases initially may seem to be spartanic caused by the lack of testing of integrity
        after transfering the data from the key-value-store into their respective tables.

        What is tested is the correct creation of intermediate tables and simple relations exemplary as we
        can trust that it works for other tables if it worked for one.
        Also it is tested that the new tables are created on top of an old basis and the old tables are deleted.
        It should be only used like this in this migration test since it leads to a performance problem
        once the actual connection context is entered the first time after the database was dropped and recreated.
    """

    app: OpenSlidesBackendWSGIApplication
    auth: AuthenticationService
    # Save auth data as class variable
    auth_data: AuthData | None = None
    auth_mockers: dict[str, _patch]

    def wait_for_lock(self, wait_lock: Lock, indicator_lock: Lock) -> Callable:
        """
        wait_lock is intended to be waited upon and should be unlocked in the test when needed.
        indicator_lock is used as an indicator that the thread is waiting for the wait_lock and must
        be in locked state.
        Intended for use of a function being wrapped instead of replaced by a mock.
        """

        def _wait_for_lock(*args: Any, **kwargs: Any) -> mockdefault:
            indicator_lock.release()
            wait_lock.acquire()
            return mockdefault

        return _wait_for_lock

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
        MigrationHelper.migrate_thread_stream = None

    def setUp(self):
        # 1) Create old idempotent key-value-store schema and relational schema on top
        # self.drop_tables()
        drop_db()
        create_db()
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                curs.execute(open(DEPR_SQL_PATH).read())

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
            # Login and save copy of auth data for all following tests
            self.client.login(ADMIN_USERNAME, ADMIN_PASSWORD)
            BaseMigrationTestCase.auth_data = deepcopy(self.client.auth_data)

        self.setup_data()
        self.apply_test_relational_schema()

    def request(
        self,
        command: str,
        lang: str | None = None,
    ) -> Response:
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
                    f"INSERT INTO positions (timestamp, user_id, migration_index) VALUES ('2020-05-20', 1, {MIN_NON_REL_MIGRATION + 1})"
                )

    def check_data(self) -> None:
        def assert_content_not_none(
            query: str, value: dict[str:Any] | None = None, error_message: str = ""
        ) -> None:
            """
            Checks whether the first element of the result for `query` matches `value`.
            `value` should be None if the expected result is just not None.
            Because of this behavior, it can't be compared to an expected result of None.
            """
            result = cur.execute(query).fetchone()
            if error_message:
                assert result, error_message
            else:
                assert result
            if value is not None:
                assert result == value

        # 6) TEST CASES
        with os_conn_pool.connection() as conn:
            with conn.cursor() as cur:
                # 6.1) 1:1 relation
                assert_content_not_none(
                    "SELECT theme_id FROM organization_t WHERE id=1;",
                    None,
                    "1:1 relation in organization not filled.",
                )

                # 6.1.1) 1G:1 relation
                assert_content_not_none(
                    "SELECT type, content_object_id, content_object_id_motion_id, content_object_id_topic_id FROM agenda_item_t WHERE id=1;",
                    {
                        "type": "common",
                        "content_object_id": "motion/1",
                        "content_object_id_motion_id": 1,
                        "content_object_id_topic_id": None,
                    },
                )

                # 6.2) 1:n relation
                assert_content_not_none(
                    "SELECT gender_id FROM user_t WHERE id=1;", {"gender_id": 1}
                )

                # 6.2.1) 1G:n relation
                assert_content_not_none(
                    "SELECT title, content_object_id, content_object_id_motion_id, content_object_id_topic_id FROM poll_t WHERE id=1;",
                    {
                        "title": "1",
                        "content_object_id": "motion/1",
                        "content_object_id_motion_id": 1,
                        "content_object_id_topic_id": None,
                    },
                )

                # 6.3) n:m relation
                assert_content_not_none(
                    "SELECT user_id, committee_id FROM nm_committee_manager_ids_user_t WHERE committee_id=1 ORDER BY user_id;",
                    {"user_id": 1, "committee_id": 1},
                )
                # 6.3.1) nG:m relation
                assert_content_not_none(
                    "SELECT tagged_id FROM gm_organization_tag_tagged_ids_t WHERE organization_tag_id=1 AND tagged_id LIKE 'committee/1';",
                )
                assert_content_not_none(
                    "SELECT tagged_id FROM gm_organization_tag_tagged_ids_t WHERE organization_tag_id=1 AND tagged_id LIKE 'meeting/1';",
                )

                # 6.4) Set id sequences correctly
                assert_content_not_none(
                    "SELECT last_value FROM gender_t_id_seq;",
                    {"last_value": 4},
                )

                # 6.4.1) Set sequential_number sequences correctly
                assert_content_not_none(
                    "SELECT last_value FROM projector_t_meeting_id1_sequential_number_seq;",
                    {"last_value": 2},
                )

                # 6.5) Deleted old table schema
                for table_name in OLD_TABLES:
                    cur.execute(
                        f"SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{table_name}';"
                    )
                    assert cur.fetchone() is None

                # 6.6) Recreated constraints
                assert_content_not_none(
                    "SELECT 1 FROM information_schema.constraint_column_usage WHERE constraint_name = 'personal_note_t_meeting_user_id_fkey';"
                )

                # 6.7) Recreated triggers
                for trigger_name in [
                    "tr_i_topic_agenda_item_id",  # check_not_null_for_1_1
                    "tr_i_meeting_default_projector_agenda_item_list_ids",  # check_not_null_for_relation_lists
                    "restrict_motion_identical_motion_ids",  # check_unique_ids_pair
                    "tr_generate_sequence_motion_block_sequential_number",
                    "tr_log_tagged_id_meeting_id_gm_organization_tag_tagged_ids_t",
                ]:
                    assert_content_not_none(
                        f"SELECT 1 FROM pg_trigger WHERE tgname = '{trigger_name}';"
                    )

                # 6.8 Recreated foreign key constraints
                assert_content_not_none(
                    """SELECT 1
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = 'organization_t'
                        AND ccu.table_name = 'theme_t'
                        AND kcu.column_name = 'theme_id'
                        AND ccu.column_name = 'id'
                        AND tc.constraint_name = 'organization_t_theme_id_fkey';"""
                )

                # 6.9) Recreated views
                assert_content_not_none("SELECT 1 from organization;")
        # END TEST CASES

    def assert_indices_state(self, state: MigrationState) -> None:
        """Asserts that all migration indices after the MIN_NON_REL_MIGRATION are set to given state."""
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                curs.execute("SELECT migration_index, migration_state FROM version;")
                result = curs.fetchall()
                del result[0]
                for idx, row in enumerate(result, 100):
                    assert {
                        "migration_index": idx,
                        "migration_state": state,
                    } == row

    def test_migration_handler(self) -> None:
        # Prepare what manager would.
        MigrationHelper.load_migrations()
        MigrationHelper.add_new_migrations_to_version()
        MigrationHelper.migrate_thread_stream = StringIO()
        # 5) Call data_manipulation of module
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                handler = MigrationHandler(
                    curs, self.env, self.services, self.app.logging
                )
                handler.execute_command("migrate")
                self.assert_indices_state(MigrationState.FINALIZATION_REQUIRED)
                handler.execute_command("finalize")

        self.assert_indices_state(MigrationState.FINALIZED)
        self.check_data()

    def test_migration_manager(self) -> None:
        # 5) Call data_manipulation of module
        manager = MigrationManager(self.env, self.services, self.app.logging)
        manager.handle_request({"cmd": "migrate", "verbose": True})

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                while (
                    MigrationHelper.get_migration_state(curs)
                    != MigrationState.FINALIZATION_REQUIRED
                ):
                    sleep(0.1)
                    curs.connection.commit()
        self.assert_indices_state(MigrationState.FINALIZATION_REQUIRED)

        manager.handle_request({"cmd": "finalize", "verbose": True})

        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                while (
                    MigrationHelper.get_migration_state(curs)
                    != MigrationState.FINALIZED
                ):
                    sleep(0.1)
                    curs.connection.commit()

        self.assert_indices_state(MigrationState.FINALIZED)
        self.check_data()

    @patch(
        "meta.dev.src.generate_sql_schema.GenerateCodeBlocks.generate_the_code",
        wraps=GenerateCodeBlocks.generate_the_code,
    )
    def test_migration_route_0(self, method_mock: Mock) -> None:
        """Uses migrate command first and then finalize."""
        # TODO store a recent copy of example_json before this gets merged into main.

        wait_lock = Lock()
        wait_lock.acquire()
        indicator_lock = Lock()
        indicator_lock.acquire()
        method_mock.side_effect = self.wait_for_lock(wait_lock, indicator_lock)
        # 5) Call data_manipulation of module
        # Future migrations do not need to test all commands. Finalize should be sufficient. Or call MigrationHelper().run_migrations() directly.

        # TODO do response checks in test_migration_route.py if possible
        response = self.request("stats")
        assert response.json == {
            "success": True,
            "stats": {
                # TODO only migrate one index? Would require altering the test-visible migration files.
                "status": MigrationState.MIGRATION_REQUIRED,
                "current_migration_index": MIN_NON_REL_MIGRATION,
                "target_migration_index": 100,
                "migratable_models": {
                    "agenda_item": {"count": 15, "migrated": 0},
                    "assignment": {"count": 2, "migrated": 0},
                    "assignment_candidate": {"count": 5, "migrated": 0},
                    "chat_group": {"count": 2, "migrated": 0},
                    "committee": {"count": 1, "migrated": 0},
                    "gender": {"count": 4, "migrated": 0},
                    "group": {"count": 5, "migrated": 0},
                    "list_of_speakers": {"count": 16, "migrated": 0},
                    "mediafile": {"count": 1, "migrated": 0},
                    "meeting": {"count": 1, "migrated": 0},
                    "meeting_mediafile": {"count": 1, "migrated": 0},
                    "meeting_user": {"count": 3, "migrated": 0},
                    "motion": {"count": 4, "migrated": 0},
                    "motion_block": {"count": 1, "migrated": 0},
                    "motion_category": {"count": 2, "migrated": 0},
                    "motion_change_recommendation": {"count": 2, "migrated": 0},
                    "motion_comment": {"count": 1, "migrated": 0},
                    "motion_comment_section": {"count": 1, "migrated": 0},
                    "motion_state": {"count": 15, "migrated": 0},
                    "motion_submitter": {"count": 4, "migrated": 0},
                    "motion_supporter": {"count": 1, "migrated": 0},
                    "motion_workflow": {"count": 2, "migrated": 0},
                    "option": {"count": 13, "migrated": 0},
                    "organization": {"count": 1, "migrated": 0},
                    "organization_tag": {"count": 1, "migrated": 0},
                    "personal_note": {"count": 1, "migrated": 0},
                    "poll": {"count": 5, "migrated": 0},
                    "projection": {"count": 4, "migrated": 0},
                    "projector": {"count": 2, "migrated": 0},
                    "projector_countdown": {"count": 2, "migrated": 0},
                    "projector_message": {"count": 1, "migrated": 0},
                    "speaker": {"count": 13, "migrated": 0},
                    "structure_level": {"count": 3, "migrated": 0},
                    "tag": {"count": 3, "migrated": 0},
                    "theme": {"count": 3, "migrated": 0},
                    "topic": {"count": 8, "migrated": 0},
                    "user": {"count": 3, "migrated": 0},
                    "vote": {"count": 9, "migrated": 0},
                },
            },
        }
        response = self.request("migrate")
        assert response.json == {
            "success": True,
            "status": MigrationState.MIGRATION_RUNNING,
            "output": "started\n",
        }

        # Test before and after setting migration states. (Committing points of transaction)
        indicator_lock.acquire()
        response = self.request("stats")
        assert response.json == {
            "success": True,
            "stats": {
                "status": MigrationState.MIGRATION_RUNNING,
                "output": "started\n",
                "current_migration_index": MIN_NON_REL_MIGRATION,
                "target_migration_index": 100,
                "migratable_models": response.json["stats"]["migratable_models"],
            },
        }
        wait_lock.release()

        # Wait for migrate with a sec delay per iteration.
        max_time = timedelta(seconds=15)
        start = datetime.now()
        while (response := self.request("progress").json) != {
            "success": True,
            "status": MigrationState.FINALIZATION_REQUIRED,
            "output": "finished\n",
        }:
            sleep(0.1)
            if datetime.now() - start > max_time:
                raise Exception(
                    f"The migration doesn't finish in {max_time}. {response}"
                )
        self.assert_indices_state(MigrationState.FINALIZATION_REQUIRED)

        response = self.request("finalize")
        assert response.json == {
            "success": True,
            "status": MigrationState.FINALIZATION_RUNNING,
            "output": "finalization started\n",
        }

        indicator_lock.acquire()
        wait_lock.release()
        start = datetime.now()
        # Continue after setting finalized migration state.
        while (response := self.request("migrate").json) == {
            "success": False,
            "message": "Finalization is running, only 'stats' command is allowed.",
        }:
            sleep(0.1)
            if datetime.now() - start > max_time:
                raise Exception(
                    f"The finalization doesn't finish in {max_time}. {response}"
                )
        assert response == {
            "success": True,
            "status": MigrationState.FINALIZED,
        }

        self.assert_indices_state(MigrationState.FINALIZED)
        self.check_data()

    def test_migration_route_1(self) -> None:
        """Uses finalize command directly and tries to migrate in fast succession."""
        # 5) Call data_manipulation of module
        # Future migrations do not need to test all commands. Finalize should be sufficient. Or call MigrationHelper().run_migrations() directly.

        response = self.request("finalize")
        assert response.json == {
            "success": True,
            "status": MigrationState.MIGRATION_RUNNING,
            "output": "started\n",
        }

        # Wait for migrate with a sec delay per iteration. TODO centralize this
        max_time = timedelta(seconds=15)
        start = datetime.now()
        while (response := self.request("migrate").json) != {
            "success": True,
            "status": MigrationState.FINALIZED,
        }:
            sleep(0.1)
            if datetime.now() - start > max_time:
                raise Exception(
                    f"The migration doesn't finish in {max_time}. {response}"
                )
        assert response == {
            "success": True,
            "status": MigrationState.FINALIZED,
        }

        self.assert_indices_state(MigrationState.FINALIZED)
        self.check_data()
