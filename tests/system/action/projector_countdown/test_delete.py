from tests.system.action.base import BaseActionTestCase


class ProjectorCountdownDelete(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {"projector_countdown_ids": [1, 2, 3]},
                "projector_countdown/1": {"meeting_id": 1, "title": "test1"},
                "projector_countdown/2": {
                    "meeting_id": 1,
                    "title": "test2",
                    "used_as_list_of_speaker_countdown_meeting_id": 1,
                },
                "projector_countdown/3": {
                    "meeting_id": 1,
                    "title": "test3",
                    "used_as_poll_countdown_meeting_id": 1,
                },
            }
        )

    def test_delete(self) -> None:
        response = self.request("projector_countdown.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("projector_countdown/1")
        meeting = self.get_model("meeting/1")
        assert meeting.get("projector_countdown_ids") == [2, 3]

    def test_delete_not_allowed_1(self) -> None:
        response = self.request("projector_countdown.delete", {"id": 2})
        self.assert_status_code(response, 400)
        assert (
            "List of speakers or poll countdown is not allowed to delete."
            in response.data.decode()
        )

    def test_delete_not_allowed_2(self) -> None:
        response = self.request("projector_countdown.delete", {"id": 3})
        self.assert_status_code(response, 400)
        assert (
            "List of speakers or poll countdown is not allowed to delete."
            in response.data.decode()
        )
