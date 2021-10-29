from tests.system.action.base import BaseActionTestCase


class ListOfSpeakersDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/78": {
                    "name": "name_RWtyEUGy",
                    "list_of_speakers_ids": [111],
                    "is_active_in_organization_id": 1,
                },
                "list_of_speakers/111": {"closed": True, "meeting_id": 78},
            }
        )
        response = self.request("list_of_speakers.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("list_of_speakers/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/78": {
                    "name": "name_RWtyEUGy",
                    "list_of_speakers_ids": [112],
                    "is_active_in_organization_id": 1,
                },
                "list_of_speakers/112": {"closed": True, "meeting_id": 78},
            }
        )
        response = self.request("list_of_speakers.delete", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("list_of_speakers/112")
        assert model.get("closed") is True
        assert model.get("meeting_id") == 78
