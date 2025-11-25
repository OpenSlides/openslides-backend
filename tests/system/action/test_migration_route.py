from collections.abc import Callable
from threading import Lock
from time import sleep
from typing import Any
from unittest.mock import Mock, patch

from openslides_backend.http.views.action_view import ActionView
from openslides_backend.migrations.core.exceptions import MigrationException
from openslides_backend.migrations.migration_handler import (
    MigrationHandler,
    MigrationState,
)
from openslides_backend.migrations.migration_helper import (
    LAST_NON_REL_MIGRATION,
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
        MigrationHelper.migrate_thread_exception = None
        if MigrationHelper.migrate_thread_stream:
            MigrationHandler.close_migrate_thread_stream()
        super().setUp()

    def wait_for_migration_thread(self, error: bool = False) -> None:
        if error:
            while not MigrationHelper.migrate_thread_exception:
                sleep(0.02)
        else:
            with self.connection.cursor() as curs:
                while (
                    MigrationHelper.get_migration_state(curs)
                    != MigrationState.NO_MIGRATION_REQUIRED
                ):
                    sleep(0.02)
                    self.connection.commit()

    def migration_request(
        self,
        cmd: str,
        internal_auth_password: str | None = DEV_PASSWORD,
    ) -> Response:
        return super().call_internal_route({"cmd": cmd}, internal_auth_password)


class TestMigrationRoute(BaseMigrationRouteTest, BaseInternalPasswordTest):
    def test_stats(self) -> None:
        response = self.migration_request("stats")
        self.assert_status_code(response, 200)
        assert response.json["stats"] == {
            "status": MigrationState.NO_MIGRATION_REQUIRED,
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
        self.wait_for_migration_thread()
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


@patch(
    "openslides_backend.migrations.migration_handler.MigrationHandler.execute_command"
)
class TestMigrationRouteWithLocks(BaseInternalPasswordTest, BaseMigrationRouteTest):
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
            MigrationHelper.write_line("start")
            with self.connection.cursor() as curs:
                MigrationHelper.set_database_migration_info(
                    curs, self.backend_migration_index, MigrationState.MIGRATION_RUNNING
                )
            indicator_lock.release()
            wait_lock.acquire()
            if error:
                raise MigrationException("test")
            with self.connection.cursor() as curs:
                MigrationHelper.set_database_migration_info(
                    curs,
                    self.backend_migration_index,
                    MigrationState.NO_MIGRATION_REQUIRED,
                    writable=True,
                )
            MigrationHelper.write_line("finish")

        return _wait_for_lock

    def test_longer_migration(self, execute_command: Mock) -> None:
        wait_lock = Lock()
        wait_lock.acquire()
        indicator_lock = Lock()
        indicator_lock.acquire()
        execute_command.side_effect = self.wait_for_lock(wait_lock, indicator_lock)
        response = self.migration_request("migrate")
        self.assert_status_code(response, 200)

        indicator_lock.acquire()
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["output"] == "start\n"

        wait_lock.release()
        self.wait_for_migration_thread()
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["output"] == "finish\n"

        # check that the output is preserved for future progress requests
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["output"] == "finish\n"

    def test_stats_during_migration(self, execute_command: Mock) -> None:
        # TODO this test is very hard wired and prone to break with the next migration.
        # needs automatic migration index handling and possibly actual execution of a migration
        with self.connection.cursor() as curs:
            curs.execute("TRUNCATE TABLE version")
            curs.execute("CREATE TABLE models (fqid varchar(256), deleted boolean);")
            curs.execute(
                "INSERT INTO models (fqid, deleted) VALUES (%s, %s);",
                ("organization/1", False),
            )
            MigrationHelper.set_database_migration_info(
                curs,
                LAST_NON_REL_MIGRATION,
                MigrationState.NO_MIGRATION_REQUIRED,
                writable=True,
            )
        wait_lock = Lock()
        wait_lock.acquire()
        indicator_lock = Lock()
        indicator_lock.acquire()

        execute_command.side_effect = self.wait_for_lock(wait_lock, indicator_lock)
        response = self.migration_request("finalize")
        self.assert_status_code(response, 200)

        indicator_lock.acquire()
        response = self.migration_request("stats")
        self.assert_status_code(response, 200)
        assert response.json["stats"] == {
            "status": MigrationState.MIGRATION_RUNNING,
            "output": "start\n",
            "current_migration_index": LAST_NON_REL_MIGRATION,
            "target_migration_index": self.backend_migration_index,
            "migratable_models": {"organization": {"count": 1, "migrated": 1}},
        }

        wait_lock.release()
        self.wait_for_migration_thread()
        response = self.migration_request("stats")
        self.assert_status_code(response, 200)
        assert response.json["stats"] == {
            "status": MigrationState.NO_MIGRATION_REQUIRED,
            "output": "finish\n",
            "current_migration_index": self.backend_migration_index,
            "target_migration_index": self.backend_migration_index,
            "migratable_models": {},
        }

        # check that the output is preserved for future stats requests
        wait_lock.release()
        response = self.migration_request("stats")
        self.assert_status_code(response, 200)
        assert response.json["stats"] == {
            "status": MigrationState.NO_MIGRATION_REQUIRED,
            "output": "finish\n",
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
        self.assert_status_code(response, 400)
        assert response.json["success"] is False
        assert (
            response.json["message"]
            == "Migration is running, only 'stats' command is allowed."
        )
        lock.release()

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
        assert response.json["output"] == "start\n"

        wait_lock.release()
        self.wait_for_migration_thread(True)
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["success"] is True
        assert response.json["output"] == "start\n"
        assert response.json["exception"] == "test"


@disable_dev_mode
class TestMigrationRouteWithoutPassword(BaseMigrationRouteTest):
    def test_migrate_no_password_on_server(self) -> None:
        response = self.migration_request("migrate")
        self.assert_status_code(response, 500)
        self.assertEqual(
            response.json.get("message"), "Missing INTERNAL_AUTH_PASSWORD_FILE."
        )
