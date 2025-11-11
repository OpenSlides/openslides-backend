from collections.abc import Callable
from threading import Lock
from time import sleep
from typing import Any
from unittest.mock import MagicMock, Mock, patch

from openslides_backend.http.views.action_view import ActionView
from openslides_backend.migrations import (
    get_backend_migration_index,
    get_datastore_migration_index,
)
from openslides_backend.migrations.core.exceptions import MigrationException
from openslides_backend.migrations.migration_handler import (
    MigrationHandler,
    MigrationState,
)
from openslides_backend.migrations.migration_helper import MigrationHelper
from openslides_backend.shared.env import DEV_PASSWORD
from tests.system.util import RouteFunction, disable_dev_mode
from tests.util import Response

from .test_internal_actions import BaseInternalPasswordTest, BaseInternalRequestTest


class BaseMigrationRouteTest(BaseInternalRequestTest):
    """
    Uses the anonymous client to call the migration route.
    """

    route: RouteFunction = ActionView.migrations_route

    def setUp(self) -> None:
        # TODO probably needs delitions
        MigrationHelper.migrate_thread_exception = None
        if MigrationHelper.migrate_thread_stream:
            MigrationHandler.close_migrate_thread_stream()
        super().setUp()

    def wait_for_migration_thread(self) -> None:
        with self.connection.cursor() as curs:
            while (
                MigrationHelper.get_migration_state(curs)
                != MigrationState.NO_MIGRATION_REQUIRED
            ):
                sleep(0.02)

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
            "current_migration_index": 70,
            "target_migration_index": 70,
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
        assert get_datastore_migration_index() == get_backend_migration_index()

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
            MigrationHandler.write_line(MagicMock(), "start")
            indicator_lock.release()
            wait_lock.acquire()
            if error:
                raise MigrationException("test")
            MigrationHandler.write_line(MagicMock(), "finish")

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
        assert response.json["output"] == "start\nfinish\n"

        # check that the output is preserved for future progress requests
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["output"] == "start\nfinish\n"

    def test_stats_during_migration(self, execute_command: Mock) -> None:
        # TODO this test is very hard wired and prone to break with the next migration.
        # needs automatic migration index handling and possibly actual execution of a migration
        wait_lock = Lock()
        wait_lock.acquire()
        indicator_lock = Lock()
        indicator_lock.acquire()
        with self.connection.cursor() as curs:
            MigrationHelper.set_database_migration_info(
                curs, 69, MigrationState.NO_MIGRATION_REQUIRED, writable=True
            )
        execute_command.side_effect = self.wait_for_lock(wait_lock, indicator_lock)
        response = self.migration_request("finalize")
        self.assert_status_code(response, 200)

        indicator_lock.acquire()
        response = self.migration_request("stats")
        self.assert_status_code(response, 200)
        assert response.json["stats"] == {
            "status": MigrationState.MIGRATION_RUNNING,
            "current_migration_index": 69,
            "target_migration_index": 70,
            "migratable_models": {"poll": {"count": 0}, "user": {"count": 1}},
        }

        wait_lock.release()
        self.wait_for_migration_thread()
        with self.connection.cursor() as curs:
            MigrationHelper.set_database_migration_info(
                curs, 70, MigrationState.NO_MIGRATION_REQUIRED, writable=True
            )
        # MigrationHelper.execute_migrations()
        # self.wait_for_migration_thread()
        response = self.migration_request("stats")
        self.assert_status_code(response, 200)
        assert response.json["stats"] == {
            "status": MigrationState.NO_MIGRATION_REQUIRED,
            "current_migration_index": 70,
            "target_migration_index": 70,
            "migratable_models": {"poll": {"count": 0}, "user": {"count": 1}},
        }

        # check that the output is preserved for future stats requests
        wait_lock.release()
        response = self.migration_request("stats")
        self.assert_status_code(response, 200)
        assert response.json["stats"] == {
            "status": MigrationState.NO_MIGRATION_REQUIRED,
            "current_migration_index": 70,
            "target_migration_index": 70,
            "migratable_models": {"poll": {"count": 0}, "user": {"count": 1}},
        }

    # def test_double_migration(self, execute_command: Mock) -> None:
    #     lock = Lock()
    #     lock.acquire()
    #     indicator_lock = Lock()
    #     indicator_lock.acquire()
    #     execute_command.side_effect = self.wait_for_lock(lock, indicator_lock)
    #     response = self.migration_request("migrate")
    #     self.assert_status_code(response, 200)

    #     response = self.migration_request("migrate")
    #     self.assert_status_code(response, 400)
    #     assert response.json["success"] is False
    #     assert (
    #         response.json["message"]
    #         == "Migration is running, only 'stats' command is allowed."
    #     )
    #     lock.release()

    def test_migration_with_error(self, execute_command: Mock) -> None:
        lock = Lock()
        lock.acquire()
        indicator_lock = Lock()
        indicator_lock.acquire()
        execute_command.side_effect = self.wait_for_lock(
            lock, indicator_lock, error=True
        )
        response = self.migration_request("migrate")
        self.assert_status_code(response, 200)
        assert response.json["success"] is True
        assert response.json["output"] == "start\n"

        lock.release()
        self.wait_for_migration_thread()
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
