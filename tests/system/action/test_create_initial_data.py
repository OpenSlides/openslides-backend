import tempfile
from copy import deepcopy
from unittest.mock import MagicMock, patch

from openslides_backend.shared.exceptions import ActionException
from tests.system.action.base import BaseActionTestCase


class TestInitialDataCreation(BaseActionTestCase):
    def setUp(self) -> None:
        self.init_with_login = False
        super().setUp()
        self.vars = deepcopy(self.env.vars)
        self.env.vars["OPENSLIDES_BACKEND_CREATE_INITIAL_DATA"] = "1"

    def tearDown(self) -> None:
        super().tearDown()
        self.env.vars.update(self.vars)

    def test_initial_data_dev_mode(self) -> None:
        self.app.create_initial_data()
        self.logger.info.assert_any_call("Creating initial data...")
        self.logger.error.assert_not_called()
        self.assert_model_exists("organization/1", {"name": "Test Organization"})
        user = self.assert_model_exists("user/1", {"username": "admin"})
        assert self.auth.is_equal("admin", user["password"])

    @patch(
        "openslides_backend.action.action_handler.ActionHandler.execute_internal_action"
    )
    def test_initial_data_error(self, mock: MagicMock) -> None:
        mock.side_effect = ActionException("test")
        self.app.create_initial_data()
        self.logger.info.assert_any_call("Creating initial data...")
        self.logger.error.assert_called_with("Initial data creation failed: test")

    def test_initial_data_prod_mode_changed_superadmin_password(self) -> None:
        old_changed_password = "password123"
        new_changed_password = "password456"
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            fp.write(old_changed_password.encode())
        self.env.vars["OPENSLIDES_DEVELOPMENT"] = "false"
        self.env.vars["SUPERADMIN_PASSWORD_FILE"] = fp.name
        self.app.create_initial_data()
        self.logger.info.assert_any_call("Creating initial data...")
        self.logger.error.assert_not_called()
        self.assert_model_exists("organization/1", {"name": "[Your organization]"})
        user = self.assert_model_exists("user/1", {"username": "superadmin"})
        assert self.auth.is_equal(old_changed_password, user["password"])
        self.client.login(user["username"], old_changed_password)
        response = self.request(
            "user.set_password",
            {
                "id": 1,
                "password": new_changed_password,
            },
        )
        self.assert_status_code(response, 200)
        self.app.create_initial_data()  # throws an db-not-empty exception, may not change users passwort
        user = self.assert_model_exists("user/1", {"username": "superadmin"})
        assert self.auth.is_equal(new_changed_password, user["password"])
        self.assert_logged_out()

    def test_initial_data_prod_mode(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            fp.write(b"password123")
        self.env.vars["OPENSLIDES_DEVELOPMENT"] = "false"
        self.env.vars["SUPERADMIN_PASSWORD_FILE"] = fp.name
        self.app.create_initial_data()
        self.logger.info.assert_any_call("Creating initial data...")
        self.logger.error.assert_not_called()
        self.assert_model_exists("organization/1", {"name": "[Your organization]"})
        user = self.assert_model_exists("user/1", {"username": "superadmin"})
        assert self.auth.is_equal("password123", user["password"])
