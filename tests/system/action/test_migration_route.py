from collections.abc import Callable
from threading import Lock
from typing import Any
from unittest.mock import Mock, patch

from openslides_backend.http.views.action_view import ActionView
from openslides_backend.migrations.exceptions import MigrationException
from openslides_backend.migrations.migration_handler import (
    MigrationHandler,
    MigrationState,
)
from openslides_backend.migrations.migration_helper import (
    MIN_NON_REL_MIGRATION,
    MigrationHelper,
)
from openslides_backend.shared.env import DEV_PASSWORD
from tests.system.util import RouteFunction, disable_dev_mode
from tests.util import Response

from .test_internal_actions import BaseInternalPasswordTest, BaseInternalRequestTest


class BaseMigrationRouteTest(BaseInternalRequestTest):
    """
    Uses the anonymous client to call the migration route.
    """

    backend_migration_index = MigrationHelper.get_backend_migration_index()
    route: RouteFunction = ActionView.migrations_route

    def setUp(self) -> None:
        MigrationHelper.migrate_thread = None
        MigrationHelper.migrate_thread_exception = None
        MigrationHelper.migrate_thread_stream_read_pos = 0
        MigrationHelper.migrate_thread_stream_just_read = False
        if MigrationHelper.migrate_thread_stream:
            MigrationHandler.close_migrate_thread_stream()
        super().setUp()

    def wait_for_migration_thread(self, state: MigrationState) -> None:
        """
        Waits for the thread to terminate for two seconds and asserts the state.
        If state is MIGRATION_FAILED: asserts a migrate_thread_exception.
        """
        assert MigrationHelper.migrate_thread
        MigrationHelper.migrate_thread.join(2)
        assert not MigrationHelper.migrate_thread.is_alive()
        if state == MigrationState.MIGRATION_FAILED:
            assert MigrationHelper.migrate_thread_exception
        with self.connection.cursor() as curs:
            assert MigrationHelper.get_migration_state(curs) == state

    def migration_request(
        self,
        cmd: str,
        internal_auth_password: str | None = DEV_PASSWORD,
    ) -> Response:
        return super().call_internal_route({"cmd": cmd}, internal_auth_password)


class TestMigrationRoute(BaseMigrationRouteTest, BaseInternalPasswordTest):
    # TODO test all migration states
    def test_stats(self) -> None:
        response = self.migration_request("stats")
        self.assert_status_code(response, 200)
        assert response.json["stats"] == {
            "status": MigrationState.FINALIZED,
            "current_migration_index": self.backend_migration_index,
            "target_migration_index": self.backend_migration_index,
            "migratable_models": {},
        }

    def test_migrate_mismatching_passwords(self) -> None:
        response = self.migration_request("migrate", "wrong_pw")
        self.assert_status_code(response, 401)

    def test_migrate_no_password_in_request(self) -> None:
        response = self.migration_request("migrate", None)
        self.assert_status_code(response, 401)

    def test_migrate_success(self) -> None:
        response = self.migration_request("migrate")
        self.assert_status_code(response, 200)
        self.wait_for_migration_thread(MigrationState.FINALIZED)
        with self.connection.cursor() as curs:
            assert (
                MigrationHelper.get_database_migration_index(curs)
                == self.backend_migration_index
            )

    def test_progress_no_migration(self) -> None:
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert "output" not in response.json

    def test_unknown_command(self) -> None:
        response = self.migration_request("unknown")
        self.assert_status_code(response, 400)
        assert response.json == {
            "success": False,
            "message": "Unknown command: unknown",
        }


@patch(
    "openslides_backend.migrations.migration_handler.MigrationHandler.execute_command"
)
class TestMigrationRouteWithLocks(BaseInternalPasswordTest, BaseMigrationRouteTest):
    def setUp(self) -> None:
        super().setUp()
        with self.connection.cursor() as curs:
            curs.execute("TRUNCATE TABLE version")
            MigrationHelper.set_database_migration_info(
                curs, MIN_NON_REL_MIGRATION, MigrationState.FINALIZED
            )

    def wait_for_lock(
        self,
        wait_lock: Lock,
        indicator_lock: Lock,
        error: bool = False,
    ) -> Callable[[], None]:
        """
        wait_lock is intended to be waited upon and should be unlocked in the test when needed.
        indicator_lock is used as an indicator that the thread is waiting for the wait_lock and must
        be in locked state.
        """

        def _wait_for_lock(*args: Any, **kwargs: Any) -> None:
            match args[0]:
                case "migrate":
                    state = MigrationState.MIGRATION_RUNNING
                    MigrationHelper.write_line("migration started")
                case "finalize":
                    state = MigrationState.FINALIZATION_RUNNING
                    MigrationHelper.write_line("finalization started")
            with self.connection.cursor() as curs:
                MigrationHelper.set_database_migration_info(
                    curs, self.backend_migration_index, state
                )
            match args[0]:
                case "migrate":
                    state = MigrationState.FINALIZATION_REQUIRED
                    finished_message = "migration finished"
                case "finalize":
                    state = MigrationState.FINALIZED
                    finished_message = "finalization finished"
            # This is wonky in some tests as the thread may stop later than the test itself.
            indicator_lock.release()
            wait_lock.acquire()
            if error:
                raise MigrationException("test")
            with self.connection.cursor() as curs:
                MigrationHelper.set_database_migration_info(
                    curs, self.backend_migration_index, state
                )
            MigrationHelper.write_line(finished_message)

        return _wait_for_lock

    def test_longer_migration(self, execute_command: Mock) -> None:
        wait_lock = Lock()
        wait_lock.acquire()
        indicator_lock = Lock()
        indicator_lock.acquire()
        execute_command.side_effect = self.wait_for_lock(wait_lock, indicator_lock)
        response = self.migration_request("migrate")
        self.assert_status_code(response, 200)
        assert response.json == {
            "status": MigrationState.MIGRATION_RUNNING,
            "success": True,
            "output": "migration started\n",
        }

        indicator_lock.acquire()
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["output"] == "migration started\n"

        wait_lock.release()
        self.wait_for_migration_thread(MigrationState.FINALIZATION_REQUIRED)
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["output"] == "migration finished\n"

        # check that the output is preserved for future progress requests
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["output"] == "migration finished\n"

    def test_stats_during_migration(self, execute_command: Mock) -> None:
        # TODO this test is very hard wired and prone to break with the next migration.
        # needs automatic migration index handling and possibly actual execution of a migration
        with self.connection.cursor() as curs:
            curs.execute("CREATE TABLE models (fqid varchar(256), deleted boolean);")
            curs.execute(
                "INSERT INTO models (fqid, deleted) VALUES (%s, %s);",
                ("organization/1", False),
            )
            MigrationHelper.set_database_migration_info(
                curs,
                MIN_NON_REL_MIGRATION,
                MigrationState.FINALIZED,
            )
        wait_lock = Lock()
        wait_lock.acquire()
        indicator_lock = Lock()
        indicator_lock.acquire()

        execute_command.side_effect = self.wait_for_lock(wait_lock, indicator_lock)
        response = self.migration_request("finalize")
        self.assert_status_code(response, 200)
        assert response.json == {
            "status": MigrationState.FINALIZATION_RUNNING,
            "success": True,
            "output": "finalization started\n",
        }

        indicator_lock.acquire()
        response = self.migration_request("stats")
        self.assert_status_code(response, 200)
        assert response.json["stats"] == {
            "status": MigrationState.FINALIZATION_RUNNING,
            "output": "finalization started\n",
            "current_migration_index": MIN_NON_REL_MIGRATION,
            "target_migration_index": self.backend_migration_index,
            "migratable_models": {},
            # "migratable_models": {"organization": {"count": 1, "migrated": 1}},
        }

        wait_lock.release()
        self.wait_for_migration_thread(MigrationState.FINALIZED)
        response = self.migration_request("stats")
        self.assert_status_code(response, 200)
        assert response.json["stats"] == {
            "status": MigrationState.FINALIZED,
            "output": "finalization finished\n",
            "current_migration_index": self.backend_migration_index,
            "target_migration_index": self.backend_migration_index,
            "migratable_models": {},
        }

        # check that the output is preserved for future stats requests
        wait_lock.release()
        response = self.migration_request("stats")
        self.assert_status_code(response, 200)
        assert response.json["stats"] == {
            "status": MigrationState.FINALIZED,
            "output": "finalization finished\n",
            "current_migration_index": self.backend_migration_index,
            "target_migration_index": self.backend_migration_index,
            "migratable_models": {},
        }
        with self.connection.cursor() as curs:
            curs.execute("DROP TABLE models;")
        self.connection.commit()

    def test_double_migration(self, execute_command: Mock) -> None:
        lock = Lock()
        lock.acquire()
        indicator_lock = Lock()
        indicator_lock.acquire()
        execute_command.side_effect = self.wait_for_lock(lock, indicator_lock)
        response = self.migration_request("migrate")
        self.assert_status_code(response, 200)

        response = self.migration_request("migrate")
        lock.release()
        self.assert_status_code(response, 400)
        assert response.json["success"] is False
        assert (
            response.json["message"]
            == "Migration is running, only 'stats' command is allowed."
        )

    def test_migration_with_error(self, execute_command: Mock) -> None:
        wait_lock = Lock()
        wait_lock.acquire()
        indicator_lock = Lock()
        indicator_lock.acquire()
        execute_command.side_effect = self.wait_for_lock(
            wait_lock, indicator_lock, error=True
        )
        response = self.migration_request("migrate")
        self.assert_status_code(response, 200)
        assert response.json["success"] is True
        assert response.json["output"] == "migration started\n"

        wait_lock.release()
        self.wait_for_migration_thread(MigrationState.MIGRATION_FAILED)
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["success"] is True
        assert response.json["output"] == "migration started\n"
        assert response.json["exception"] == "test"


@disable_dev_mode
class TestMigrationRouteWithoutPassword(BaseMigrationRouteTest):
    def test_migrate_no_password_on_server(self) -> None:
        response = self.migration_request("migrate")
        self.assert_status_code(response, 500)
        self.assertEqual(
            response.json.get("message"), "Missing INTERNAL_AUTH_PASSWORD_FILE."
        )
