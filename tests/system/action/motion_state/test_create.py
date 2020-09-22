from tests.system.action.base import BaseActionTestCase


class MotionStateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("motion_workflow/42", {"name": "test_name_fjwnq8d8tje8"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_state.create",
                    "data": [{"name": "test_Xcdfgee", "workflow_id": 42}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/1")
        model = self.get_model("motion_state/1")
        assert model.get("name") == "test_Xcdfgee"

    def test_create_enum_fields(self) -> None:
        self.create_model("motion_workflow/42", {"name": "test_name_fjwnq8d8tje8"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_state.create",
                    "data": [
                        {
                            "name": "test_Xcdfgee",
                            "workflow_id": 42,
                            "css_class": "red",
                            "restrictions": ["is_submitter"],
                            "merge_amendment_into_final": -1,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/1")
        model = self.get_model("motion_state/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("workflow_id") == 42
        assert model.get("css_class") == "red"
        assert model.get("restrictions") == ["is_submitter"]
        assert model.get("merge_amendment_into_final") == -1

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "motion_state.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'name\\', \\'workflow_id\\'] properties",
            str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_state.create",
                    "data": [{"wrong_field": "text_AefohteiF8"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'name\\', \\'workflow_id\\'] properties",
            str(response.data),
        )

    def test_create_forbidden_value_1(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_state.create",
                    "data": [
                        {"name": "test_Xcdfgee", "workflow_id": 42, "css_class": "pink"}
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0].css_class must be one of [\\'gray\\', \\'red\\', \\'green\\', \\'lightblue\\', \\'yellow\\']",
            str(response.data),
        )

    def test_create_forbidden_value_2(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_state.create",
                    "data": [
                        {
                            "name": "test_Xcdfgee",
                            "workflow_id": 42,
                            "restrictions": ["is__XXXX__submitter"],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0].restrictions[0] must be one of [\\'motions.can_see_internal\\', \\'motions.can_manage_metadata\\', \\'motions.can_manage\\', \\'is_submitter\\']",
            str(response.data),
        )
