from tests.system.action.base import BaseActionTestCase


class MotionStateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "motion_workflow/42": {
                    "name": "test_name_fjwnq8d8tje8",
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_state.create", {"name": "test_Xcdfgee", "workflow_id": 42}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/1")
        model = self.get_model("motion_state/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("restrictions") == []
        assert model.get("merge_amendment_into_final") == "undefined"
        assert model.get("css_class") == "lightblue"

    def test_create_enum_fields(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "motion_workflow/42": {
                    "name": "test_name_fjwnq8d8tje8",
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_state.create",
            {
                "name": "test_Xcdfgee",
                "workflow_id": 42,
                "css_class": "red",
                "restrictions": ["is_submitter"],
                "merge_amendment_into_final": "do_not_merge",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/1")
        model = self.get_model("motion_state/1")
        assert model.get("name") == "test_Xcdfgee"
        assert model.get("workflow_id") == 42
        assert model.get("css_class") == "red"
        assert model.get("restrictions") == ["is_submitter"]
        assert model.get("merge_amendment_into_final") == "do_not_merge"

    def test_create_empty_data(self) -> None:
        response = self.request("motion_state.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['name', 'workflow_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "motion_state.create", {"wrong_field": "text_AefohteiF8"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['name', 'workflow_id'] properties",
            response.json["message"],
        )

    def test_create_forbidden_value_1(self) -> None:
        response = self.request(
            "motion_state.create",
            {"name": "test_Xcdfgee", "workflow_id": 42, "css_class": "pink"},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.css_class must be one of ['grey', 'red', 'green', 'lightblue', 'yellow']",
            response.json["message"],
        )

    def test_create_forbidden_value_2(self) -> None:
        response = self.request(
            "motion_state.create",
            {
                "name": "test_Xcdfgee",
                "workflow_id": 42,
                "restrictions": ["is__XXXX__submitter"],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.restrictions[0] must be one of ['motion.can_see_internal', 'motion.can_manage_metadata', 'motion.can_manage', 'is_submitter']",
            response.json["message"],
        )
