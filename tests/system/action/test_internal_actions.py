from typing import Any, Dict

from openslides_backend.http.views.action_view import ActionView
from tests.system.util import get_route_path
from tests.util import Response

from .base import BaseActionTestCase


class TestInternalActions(BaseActionTestCase):
    """
    Uses the anonymous client to call the internal action route. This should skip all permission checks, so the requests
    still succeed.
    Just rudimentary tests that the actions generally succeed since if that's the case, everything should be handled
    analogously to the external case, which is already test sufficiently in the special test cases for the actions.
    """

    def internal_request(self, action: str, data: Dict[str, Any]) -> Response:
        return self.anon_client.post(
            get_route_path(ActionView.internal_action_route),
            json=[{"action": action, "data": [data]}],
        )

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
