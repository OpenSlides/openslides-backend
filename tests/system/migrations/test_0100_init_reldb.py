# BUILTIN IMPORTS
import json
import os
from datetime import datetime
from io import StringIO
from threading import Lock
from typing import Any
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

from openslides_backend.http.application import OpenSlidesBackendWSGIApplication
from openslides_backend.http.views import ActionView
from openslides_backend.migrations.mig_0100_init_reldb.migration import Sql_helper
from openslides_backend.migrations.migration_handler import MigrationHandler
from openslides_backend.migrations.migration_helper import (
    MIN_NON_REL_MIGRATION,
    MigrationHelper,
    MigrationState,
)
from openslides_backend.migrations.migration_manager import MigrationManager
from openslides_backend.services.auth.interface import AuthenticationService
from openslides_backend.services.postgresql.db_connection_handling import (
    get_new_os_conn,
    os_conn_pool,
)
from openslides_backend.shared.env import DEV_PASSWORD
from tests.system.action.util import get_internal_auth_header
from tests.system.migrations.base_migration_test import BaseMigrationTestCase
from tests.system.util import create_action_test_application, get_route_path
from tests.util import AuthData, Client, Response

from .conftest import OLD_TABLES

# VARIABLE DECLARATION
EXAMPLE_DATA_PATH = os.path.realpath(
    os.path.join(
        os.getcwd(), "tests", "system", "migrations", "legacy-example-data.json"
    )
)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
MIGRATIONS_URL = get_route_path(ActionView.migrations_route)
data: dict[str, Any] = {}


class TestMigration100(BaseMigrationTestCase):
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

    migration_number = 100
    app: OpenSlidesBackendWSGIApplication
    auth: AuthenticationService
    # Save auth data as class variable
    auth_data: AuthData | None = None
    MAX_WAIT = 15
    EXPECTED_INTRODUCTION = """This is migration 100, part of the OpenSlides 4.3.0 release.
This migration will fundamentally restructure all data.
For more information, see
  https://github.com/OpenSlides/OpenSlides/blob/main/UPDATE_TO_4.3.md
\n"""

    @classmethod
    def tearDownClass(cls) -> None:
        # 8) Final Cleanup
        for key in ["MIG0100_I_READ_DOCS", "MIG0100_TIMEZONE"]:
            if os.getenv(key):
                del os.environ[key]
        super().tearDownClass()

    def tearDown(self) -> None:
        Sql_helper.offset = 0
        super().tearDown()

    def setUp(self) -> None:
        # 1.1) Create services and login.
        self.app = create_action_test_application()
        self.client = Client(self.app)

        # 1.2) Setup data and other class variables
        super().setUp()
        self.setup_data()

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
            self.used_collections.add(collection)
            for model_id, model in models.items():
                data[f"{collection}/{model_id}"] = {
                    f: v for f, v in model.items() if not f.startswith("meta_")
                }

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

    def check_data(self) -> None:
        # 6) TEST CASES
        with os_conn_pool.connection() as conn:
            with conn.cursor() as cur:
                # 6.1) 1:1 relation
                self.assert_content_not_none(
                    cur,
                    "SELECT theme_id FROM organization_t WHERE id=1;",
                    None,
                    "1:1 relation in organization not filled.",
                )

                # 6.1.1) 1G:1 relation
                self.assert_content_not_none(
                    cur,
                    "SELECT type, content_object_id, content_object_id_motion_id, content_object_id_topic_id FROM agenda_item_t WHERE id=1;",
                    {
                        "type": "common",
                        "content_object_id": "motion/1",
                        "content_object_id_motion_id": 1,
                        "content_object_id_topic_id": None,
                    },
                )

                # 6.2) 1:n relation
                self.assert_content_not_none(
                    cur, "SELECT gender_id FROM user_t WHERE id=1;", {"gender_id": 1}
                )

                # 6.2.1) 1G:n relation
                self.assert_content_not_none(
                    cur,
                    "SELECT title, content_object_id, content_object_id_motion_id, content_object_id_topic_id FROM poll_t WHERE id=1;",
                    {
                        "title": "1",
                        "content_object_id": "motion/1",
                        "content_object_id_motion_id": 1,
                        "content_object_id_topic_id": None,
                    },
                )

                # 6.3) n:m relation
                self.assert_content_not_none(
                    cur,
                    "SELECT user_id, committee_id FROM nm_committee_manager_ids_user_t WHERE committee_id=1 ORDER BY user_id;",
                    {"user_id": 1, "committee_id": 1},
                )
                # 6.3.1) nG:m relation
                self.assert_content_not_none(
                    cur,
                    "SELECT tagged_id FROM gm_organization_tag_tagged_ids_t WHERE organization_tag_id=1 AND tagged_id LIKE 'committee/1';",
                )
                self.assert_content_not_none(
                    cur,
                    "SELECT tagged_id FROM gm_organization_tag_tagged_ids_t WHERE organization_tag_id=1 AND tagged_id LIKE 'meeting/1';",
                )

                # 6.4) Set id sequences correctly
                self.assert_content_not_none(
                    cur,
                    "SELECT last_value FROM gender_t_id_seq;",
                    {"last_value": 4},
                )

                # 6.4.1) Set sequential_number sequences correctly
                self.assert_content_not_none(
                    cur,
                    "SELECT last_value FROM projector_t_meeting_id1_sequential_number_seq;",
                    {"last_value": 2},
                )

                # 6.5) Deleted old table schema
                table_name_array = "'{" + ", ".join(t for t in OLD_TABLES) + "}'"
                assert (
                    cur.execute(
                        f"SELECT 1 AS still_exists FROM information_schema.tables WHERE table_schema = 'public' AND table_name = ANY({table_name_array});"
                    ).fetchone()
                    is None
                )

                # 6.6) Created constraints
                self.assert_content_not_none(
                    cur,
                    "SELECT 1 FROM information_schema.constraint_column_usage WHERE constraint_name = 'fk_option_t_content_object_id_poll_candidate_list_id_pold428251';",
                )

                # 6.7) Created triggers
                for trigger_name in [
                    "tr_i_not_null_topic_agenda_item_id",  # check_not_null_for_1_1
                    "tr_i_not_null_meeting_default_projector_agenda_item_list_ids",  # check_not_null_for_relation_lists
                    "tr_restrict_unique_ids_pair_motion_identical_motion_ids",  # check_unique_ids_pair
                    "tr_generate_sequence_motion_block_sequential_number",
                    "tr_log_tagged_id_meeting_id_gm_organization_tag_tagged_ids_t",
                ]:
                    self.assert_content_not_none(
                        cur,
                        f"SELECT 1 FROM pg_trigger WHERE tgname = '{trigger_name}';",
                    )

                # 6.8 Created foreign key constraints
                self.assert_content_not_none(
                    cur,
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
                        AND tc.constraint_name = 'fk_organization_t_theme_id_theme_t_id';""",
                )

                # 6.9) Created views
                self.assert_content_not_none(cur, "SELECT 1 from organization;")

                # 6.10) Created correct timestamp
                assert cur.execute(
                    "SELECT start_time, end_time, time_zone FROM meeting_t;"
                ).fetchone() == {
                    # Meeting begins and ends at midnight Europe/Berlin.
                    # UTC value is epxected to be shifted by the Europe/Berlin offset one hour or two hours considering dst.
                    # Client will calculate the display time from UTC considering the meetings `time_zone`.
                    "start_time": datetime(2020, 1, 17, 23, tzinfo=ZoneInfo("UTC")),
                    "end_time": datetime(2020, 6, 17, 22, tzinfo=ZoneInfo("UTC")),
                    "time_zone": "Europe/Berlin",
                }
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

    def test_migration_fail_prerequisites(self) -> None:
        del os.environ["MIG0100_TIMEZONE"]
        del os.environ["MIG0100_I_READ_DOCS"]
        response = self.request("migrate")
        self.wait_for_migration_thread(self.MAX_WAIT)
        expected_error_message = "Required env vars not set - aborting.\nMissing: MIG0100_I_READ_DOCS, MIG0100_TIMEZONE"
        response = self.request("stats")
        assert response.json["stats"] == {
            "status": MigrationState.MIGRATION_REQUIRED,
            "exception": f"openslides_backend.migrations.exceptions.MigrationSetupException: Pre check for migration 0100_init_reldb failed.\n{expected_error_message}",
            "output": f"{self.EXPECTED_INTRODUCTION}{expected_error_message}\n",
            "current_migration_index": 73,
            "target_migration_index": 100,
        }
        self.assert_indices_state(MigrationState.MIGRATION_REQUIRED)

    def test_migration_fail_time_zone(self) -> None:
        os.environ["MIG0100_TIMEZONE"] = "JST/Kame Hausu"
        response = self.request("migrate")
        self.wait_for_migration_thread(self.MAX_WAIT)
        expected_error_message = "JST/Kame Hausu is no accepted value for MIG0100_TIMEZONE. Please refer to the documentation on how to obtain a full list of all options available."
        response = self.request("stats")
        assert response.json["stats"] == {
            "status": MigrationState.MIGRATION_REQUIRED,
            "exception": f"openslides_backend.migrations.exceptions.MigrationSetupException: Pre check for migration 0100_init_reldb failed.\n{expected_error_message}",
            "output": f"{self.EXPECTED_INTRODUCTION}{expected_error_message}\n",
            "current_migration_index": 73,
            "target_migration_index": 100,
        }
        self.assert_indices_state(MigrationState.MIGRATION_REQUIRED)

    def test_migration_handler(self) -> None:
        # Prepare what manager would.
        MigrationHelper.load_migrations()
        MigrationHelper.add_new_migrations_to_version()
        MigrationHelper.migrate_thread_stream = StringIO()
        # 5) Call data_manipulation of module
        with get_new_os_conn() as conn:
            with conn.cursor() as curs:
                handler = MigrationHandler(curs, Mock(), Mock(), self.app.logging)
                handler.execute_command("migrate")

        self.assert_indices_state(MigrationState.FINALIZED)
        self.check_data()

    def test_migration_manager(self) -> None:
        # 5) Call data_manipulation of module
        manager = MigrationManager(Mock(), Mock(), self.app.logging)
        result = manager.handle_request({"cmd": "migrate", "verbose": True})
        assert result == {
            "status": MigrationState.MIGRATION_RUNNING,
            "output": self.EXPECTED_INTRODUCTION
            + "For setting organization and meeting time zones using 'Europe/Berlin'.\nmigration started\n100 of 161 models written to tables.\n",
        }

        self.wait_for_migration_thread(self.MAX_WAIT)
        self.assert_indices_state(MigrationState.FINALIZED)
        self.check_data()

    @patch("openslides_backend.migrations.migration_helper.MigrationHelper.write_line")
    def test_migration_route(self, method_mock: Mock) -> None:
        """Uses migrate http route."""
        wait_lock = Lock()
        wait_lock.acquire()
        indicator_lock = Lock()
        indicator_lock.acquire()
        method_mock.side_effect = self.wait_for_lock(wait_lock, indicator_lock)
        # 5) Call data_manipulation of module
        # Future migrations do not need to test all commands. Calling MigrationManager or MigrationHandler directly should be sufficient.
        # TODO do response checks in test_migration_route.py if possible

        response = self.request("stats")
        assert response.json == {
            "success": True,
            "stats": {
                "status": MigrationState.MIGRATION_REQUIRED,
                "output": "",
                "current_migration_index": MIN_NON_REL_MIGRATION,
                "target_migration_index": 100,
                "migratable_models": {
                    "agenda_item": 15,
                    "assignment": 2,
                    "assignment_candidate": 5,
                    "chat_group": 2,
                    "committee": 1,
                    "gender": 4,
                    "group": 5,
                    "list_of_speakers": 16,
                    "mediafile": 1,
                    "meeting": 1,
                    "meeting_mediafile": 1,
                    "meeting_user": 3,
                    "motion": 4,
                    "motion_block": 1,
                    "motion_category": 2,
                    "motion_change_recommendation": 2,
                    "motion_comment": 1,
                    "motion_comment_section": 1,
                    "motion_state": 15,
                    "motion_submitter": 4,
                    "motion_supporter": 1,
                    "motion_workflow": 2,
                    "option": 13,
                    "organization": 1,
                    "organization_tag": 1,
                    "personal_note": 1,
                    "poll": 5,
                    "projection": 4,
                    "projector": 2,
                    "projector_countdown": 2,
                    "projector_message": 1,
                    "speaker": 13,
                    "structure_level": 3,
                    "tag": 3,
                    "theme": 3,
                    "topic": 8,
                    "user": 3,
                    "vote": 9,
                },
            },
        }

        response = self.request("migrate")
        assert response.json == {
            "success": True,
            "status": MigrationState.MIGRATION_RUNNING,
            "output": self.EXPECTED_INTRODUCTION
            + "For setting organization and meeting time zones using 'Europe/Berlin'.\nmigration started\n",
        }

        indicator_lock.acquire()
        response = self.request("stats")
        assert response.json == {
            "success": True,
            "stats": {
                "status": MigrationState.MIGRATION_RUNNING,
                "output": self.EXPECTED_INTRODUCTION
                + "For setting organization and meeting time zones using 'Europe/Berlin'.\nmigration started\n",
                "current_migration_index": MIN_NON_REL_MIGRATION,
                "target_migration_index": 100,
                "migratable_models": response.json["stats"]["migratable_models"],
            },
        }
        assert self.request("migrate").json == {
            "success": False,
            "message": "Migration is running, only 'stats' or 'progress' commands are allowed.",
        }
        wait_lock.release()
        self.wait_for_migration_thread(self.MAX_WAIT)

        assert self.request("progress").json == {
            "success": True,
            "status": MigrationState.FINALIZED,
            "output": "100 of 161 models written to tables.\n161 of 161 models written to tables.\nmigration finished\n",
        }

        self.assert_indices_state(MigrationState.FINALIZED)
        self.check_data()
