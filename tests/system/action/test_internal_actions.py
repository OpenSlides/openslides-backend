from tempfile import NamedTemporaryFile
from typing import Any

from openslides_backend.http.views.action_view import (
    INTERNAL_AUTHORIZATION_HEADER,
    ActionView,
)
from openslides_backend.http.views.base_view import RouteFunction
from openslides_backend.shared.env import DEV_PASSWORD
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.util import disable_dev_mode, get_route_path
from tests.util import Response

from .base import BaseActionTestCase
from .util import get_internal_auth_header


class BaseInternalRequestTest(BaseActionTestCase):
    """
    Provides the ability to use the anonymous client to call an internal route.
    """

    route: RouteFunction

    def call_internal_route(
        self,
        payload: Any,
        internal_auth_password: str | None = DEV_PASSWORD,
    ) -> Response:
        if internal_auth_password is None:
            headers = {}
        else:
            headers = get_internal_auth_header(internal_auth_password)
        return self.anon_client.post(
            get_route_path(self.route),
            json=payload,
            headers=headers,
        )


class BaseInternalPasswordTest(BaseInternalRequestTest):
    """
    Sets up a server-side password for internal requests.
    """

    internal_auth_password: str = "Q2^$2J9QXimW6lDPoGj4"

    def setUp(self) -> None:
        super().setUp()
        self.secret_file = NamedTemporaryFile()
        self.secret_file.write(self.internal_auth_password.encode("ascii"))
        self.secret_file.seek(0)
        self.env.vars["INTERNAL_AUTH_PASSWORD_FILE"] = self.secret_file.name

    def tearDown(self) -> None:
        super().tearDown()
        self.env.vars["INTERNAL_AUTH_PASSWORD_FILE"] = ""
        self.secret_file.close()


class BaseInternalActionTest(BaseInternalRequestTest):
    """
    Sets up a server-side password for internal requests.
    """

    route: RouteFunction = ActionView.internal_action_route

    def internal_request(
        self,
        action: str,
        data: dict[str, Any],
        internal_auth_password: str | None = DEV_PASSWORD,
    ) -> Response:
        return super().call_internal_route(
            [{"action": action, "data": [data]}], internal_auth_password
        )


class TestInternalActionsDev(BaseInternalActionTest):
    """
    Uses the anonymous client to call the internal action route. This should skip all permission checks, so the requests
    still succeed.

    Just rudimentary tests that the actions generally succeed since if that's the case, everything should be handled
    analogously to the external case, which is already tested sufficiently in the special test cases for the actions.

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
        assert self.auth.is_equal("new_password", model["password"])

    def test_internal_organization_initial_import(self) -> None:
        response = self.internal_request("organization.initial_import", {"data": {}})
        self.assert_status_code(response, 200)
        self.assert_model_exists(ONE_ORGANIZATION_FQID)
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

    def test_internal_wrong_password_in_request(self) -> None:
        response = self.internal_request("user.create", {"username": "test"}, "wrong")
        self.assert_status_code(response, 401)
        self.assert_model_not_exists("user/2")

    def test_internal_execute_stack_internal_via_public_route(self) -> None:
        response = self.request(
            "organization.initial_import", {"data": {}}, internal=False
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            response.json.get("message"),
            "Action organization.initial_import does not exist.",
        )
        self.assert_model_not_exists("organization/1")

    def test_internal_wrongly_encoded_password(self) -> None:
        response = self.anon_client.post(
            get_route_path(self.route),
            json=[{"action": "user.create", "data": [{"username": "test"}]}],
            headers={INTERNAL_AUTHORIZATION_HEADER: "openslides"},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("user/2")


@disable_dev_mode
class TestInternalActionsProd(BaseInternalActionTest):
    """
    The same as the TestInternalActionsDev class but in prod mode.
    """

    def test_internal_no_password_on_server(self) -> None:
        response = self.internal_request(
            "user.create", {"username": "test"}, "some password"
        )
        self.assert_status_code(response, 500)
        self.assert_model_not_exists("user/2")


@disable_dev_mode
class TestInternalActionsProdWithPasswordFile(
    BaseInternalActionTest, BaseInternalPasswordTest
):
    """
    Same as TestInternalActionsProd but with a server-side password set.
    """

    def test_internal_wrong_password(self) -> None:
        response = self.internal_request("user.create", {"username": "test"}, "wrong")
        self.assert_status_code(response, 401)
        self.assert_model_not_exists("user/2")

    def test_internal_execute_public_action(self) -> None:
        response = self.internal_request(
            "user.create", {"username": "test"}, self.internal_auth_password
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2")

    def test_internal_execute_stack_internal_action(self) -> None:
        response = self.internal_request(
            "organization.initial_import", {"data": {}}, self.internal_auth_password
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(ONE_ORGANIZATION_FQID)

    def test_internal_execute_backend_internal_action(self) -> None:
        response = self.internal_request(
            "option.create",
            {"meeting_id": 1, "text": "test"},
            self.internal_auth_password,
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            response.json.get("message"), "Action option.create does not exist."
        )
        self.assert_model_not_exists("option/1")
