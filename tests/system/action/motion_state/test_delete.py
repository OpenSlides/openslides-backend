from tests.system.action.base import BaseActionTestCase


class MotionStateActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("motion_state/111", {"name": "name_srtgb123"})
        response = self.client.post(
            "/",
            json=[{"action": "motion_state.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("motion_state/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion_state/112", {"name": "name_srtgb123"})
        response = self.client.post(
            "/",
            json=[{"action": "motion_state.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_state/112")

    def test_delete_first_state(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_meeting110", "motion_state_ids": [111]}
        )
        self.create_model(
            "motion_workflow/1112",
            {
                "name": "name_XZwyPWxb",
                "first_state_id": 111,
                "meeting_id": 110,
                "state_ids": [111],
            },
        )
        self.create_model(
            "motion_state/111",
            {
                "name": "name_srtgb123",
                "first_state_of_workflow_id": 1112,
                "workflow_id": 1112,
                "meeting_id": 110,
            },
        )
        response = self.client.post(
            "/",
            json=[{"action": "motion_state.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        assert (
            "You can not delete motion_state/111 because you have to delete the following related models first: [FullQualifiedId('motion_workflow/1112')]"
            in response.json["message"]
        )
