import os
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

from openslides_backend.http.views.action_view import ActionView
from openslides_backend.shared.env import DEV_PASSWORD
from tests.system.util import get_route_path
from tests.util import Response

from .base import BaseActionTestCase
from .util import get_internal_auth_header


class BaseInternalActionsTest(BaseActionTestCase):
    def internal_request(
        self,
        action: str,
        data: Dict[str, Any],
        internal_auth_password: Optional[str] = DEV_PASSWORD,
    ) -> Response:
        if internal_auth_password is None:
            headers = {}
        else:
            headers = get_internal_auth_header(internal_auth_password)
        return self.anon_client.post(
            get_route_path(ActionView.internal_action_route),
            json=[{"action": action, "data": [data]}],
            headers=headers,
        )


class TestInternalActionsDev(BaseInternalActionsTest):
    """
    Uses the anonymous client to call the internal action route. This should skip all permission checks, so the requests
    still succeed.

    Just rudimentary tests that the actions generally succeed since if that's the case, everything should be handled
    analogously to the external case, which is already test sufficiently in the special test cases for the actions.

    Hint: This test assumes that OPENSLIDES_DEVELOPMENT is truthy.
    """

    def test_internal_user_create(self) -> None:
        response = self.internal_request("user.create", {"username": "test"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "test"})

    def test_internal_user_update(self) -> None:
        response = self.internal_request("user.update", {"id": 1, "username": "test"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"username": "test"})

    def test_internal_user_delete(self) -> None:
        response = self.internal_request("user.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("user/1")

    def test_internal_user_set_password(self) -> None:
        response = self.internal_request(
            "user.set_password", {"id": 1, "password": "new_password"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/1")
        assert self.auth.is_equals("new_password", model["password"])

    def test_internal_organization_initial_import(self) -> None:
        self.datastore.truncate_db()
        response = self.internal_request("organization.initial_import", {"data": {}})
        self.assert_status_code(response, 200)
        self.assert_model_exists("organization/1")
        self.assert_model_exists("user/1", {"username": "superadmin"})

    def test_internal_mismatching_passwords(self) -> None:
        response = self.internal_request(
            "user.create", {"username": "test"}, "wrong_pw"
        )
        self.assert_status_code(response, 401)
        self.assert_model_not_exists("user/2")

    def test_internal_no_password_in_request(self) -> None:
        response = self.internal_request("user.create", {"username": "test"}, None)
        self.assert_status_code(response, 401)
        self.assert_model_not_exists("user/2")

    @patch("openslides_backend.shared.env.Environment.is_dev_mode")
    def test_internal_no_password_on_server(self, is_dev_mode: MagicMock) -> None:
        is_dev_mode.return_value = False
        response = self.internal_request(
            "user.create", {"username": "test"}, "some password"
        )
        self.assert_status_code(response, 500)
        self.assert_model_not_exists("user/2")


class TestInternalActionsProd(BaseInternalActionsTest):
    """
    That same as the TestInternalActionsDev class but we patch the is_dev_mode
    in every test.
    """

    def setUp(self) -> None:
        self.internal_auth_password = "my secret password"
        self.secret_file = NamedTemporaryFile()
        self.secret_file.write(self.internal_auth_password.encode("ascii"))
        self.secret_file.seek(0)
        os.environ["INTERNAL_AUTH_PASSWORD_FILE"] = self.secret_file.name
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()
        del os.environ["INTERNAL_AUTH_PASSWORD_FILE"]
        self.secret_file.close()

    @patch("openslides_backend.shared.env.Environment.is_dev_mode")
    def test_internal_try_access_backend_internal_action_wrong_pw(
        self, is_dev_mode: MagicMock
    ) -> None:
        is_dev_mode.return_value = False
        response = self.internal_request(
            "user.create", {"username": "my username"}, "wrong pw"
        )
        self.assert_status_code(response, 401)
        self.assert_model_not_exists("user/2")

    @patch("openslides_backend.shared.env.Environment.is_dev_mode")
    def test_internal_try_access_backend_common_action(
        self, is_dev_mode: MagicMock
    ) -> None:
        is_dev_mode.return_value = False
        response = self.internal_request(
            "user.create", {"username": "my username"}, self.internal_auth_password
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2")

    @patch("openslides_backend.shared.env.Environment.is_dev_mode")
    def test_internal_try_access_backend_internal_action(
        self, is_dev_mode: MagicMock
    ) -> None:
        is_dev_mode.return_value = False
        response = self.internal_request(
            "option.create",
            {"meeting_id": 1, "text": "test"},
            self.internal_auth_password,
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("option/1")
