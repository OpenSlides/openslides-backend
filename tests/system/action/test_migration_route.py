import os
from tempfile import NamedTemporaryFile
from threading import Lock
from time import sleep
from typing import Any, Callable, Optional
from unittest.mock import MagicMock, Mock, patch

from migrations import get_backend_migration_index, get_datastore_migration_index
from openslides_backend.http.views.action_view import ActionView
from openslides_backend.migration_handler.migration_handler import (
    MigrationHandler,
    MigrationProgressState,
)
from openslides_backend.shared.env import DEV_PASSWORD, INTERNAL_AUTH_PASSWORD_FILE
from tests.system.util import get_route_path
from tests.util import Response

from .base import BaseActionTestCase
from .util import get_internal_auth_header


class TestMigrationRoute(BaseActionTestCase):
    """
    Uses the anonymous client to call the migration route.
    """

    def setUp(self) -> None:
        super().setUp()
        if MigrationHandler.migrate_thread_stream:
            MigrationHandler.close_migrate_thread_stream()
        self.secret_file = NamedTemporaryFile()
        self.secret_file.write(DEV_PASSWORD.encode("ascii"))
        self.secret_file.seek(0)
        os.environ[INTERNAL_AUTH_PASSWORD_FILE] = self.secret_file.name

    def tearDown(self) -> None:
        super().tearDown()
        self.secret_file.close()

    def migration_request(
        self,
        cmd: str,
        internal_auth_password: Optional[str] = DEV_PASSWORD,
    ) -> Response:
        if internal_auth_password is None:
            headers = {}
        else:
            headers = get_internal_auth_header(internal_auth_password)
        return self.anon_client.post(
            get_route_path(ActionView.migrations_route),
            json={"cmd": cmd},
            headers=headers,
        )

    def test_migrate_mismatching_passwords(self) -> None:
        response = self.migration_request("migrate", "wrong_pw")
        self.assert_status_code(response, 401)

    def test_migrate_no_password_in_request(self) -> None:
        response = self.migration_request("migrate", None)
        self.assert_status_code(response, 401)

    @patch("openslides_backend.shared.env.is_dev_mode")
    def test_migrate_no_password_on_server(self, is_dev_mode: Mock) -> None:
        is_dev_mode.return_value = False
        del os.environ[INTERNAL_AUTH_PASSWORD_FILE]
        response = self.migration_request("migrate")
        self.assert_status_code(response, 500)

    def test_migrate_success(self) -> None:
        response = self.migration_request("migrate")
        self.assert_status_code(response, 200)
        assert get_datastore_migration_index() == get_backend_migration_index()

    def test_progress_no_migration(self) -> None:
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["status"] == MigrationProgressState.NO_MIGRATION_RUNNING
        assert "output" not in response.json

    def wait_for_lock(self, lock: Lock) -> Callable[[], None]:
        def _wait_for_lock(*args: Any, **kwargs: Any) -> None:
            MigrationHandler.write_line(MagicMock(), "start")
            lock.acquire()
            MigrationHandler.write_line(MagicMock(), "finish")

        return _wait_for_lock

    @patch(
        "openslides_backend.migration_handler.migration_handler.MigrationWrapper.execute_command"
    )
    def test_longer_migration(self, execute_command: Mock) -> None:
        lock = Lock()
        lock.acquire()
        execute_command.side_effect = self.wait_for_lock(lock)
        response = self.migration_request("migrate")
        self.assert_status_code(response, 200)
        assert response.json["status"] == MigrationProgressState.MIGRATION_RUNNING
        assert response.json["output"] == "start\n"

        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["status"] == MigrationProgressState.MIGRATION_RUNNING
        assert response.json["output"] == "start\n"

        lock.release()
        while MigrationHandler.migration_running:
            sleep(0.01)
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["status"] == MigrationProgressState.MIGRATION_FINISHED
        assert response.json["output"] == "start\nfinish\n"

        # check that the output is preserved for future progress requests
        response = self.migration_request("progress")
        self.assert_status_code(response, 200)
        assert response.json["status"] == MigrationProgressState.MIGRATION_FINISHED
        assert response.json["output"] == "start\nfinish\n"

    @patch(
        "openslides_backend.migration_handler.migration_handler.MigrationWrapper.execute_command"
    )
    def test_double_migration(self, execute_command: Mock) -> None:
        lock = Lock()
        lock.acquire()
        execute_command.side_effect = self.wait_for_lock(lock)
        response = self.migration_request("migrate")
        self.assert_status_code(response, 200)
        assert response.json["status"] == MigrationProgressState.MIGRATION_RUNNING

        response = self.migration_request("migrate")
        self.assert_status_code(response, 400)
        assert response.json["success"] is False
        assert (
            response.json["message"]
            == "Migration is running, only 'progress' command is allowed"
        )
        lock.release()
