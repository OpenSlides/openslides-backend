from tests.system.action.base import BaseActionTestCase


class ListOfSpeakersUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model("meeting/222", {"name": "name_xQyvfmsS"})
        self.create_model(
            "list_of_speakers/111",
            {"closed": False, "meeting_id": 222},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "list_of_speakers.update",
                    "data": [{"id": 111, "closed": True}],
                }
            ],
        )
        self.assert_status_code(response, 200)

        model = self.get_model("list_of_speakers/111")
        assert model.get("closed") is True

    def test_update_wrong_id(self) -> None:
        self.create_model("meeting/222", {"name": "name_xQyvfmsS"})
        self.create_model(
            "list_of_speakers/111",
            {"closed": False, "meeting_id": 222},
        )

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "list_of_speakers.update",
                    "data": [{"id": 112, "closed": True}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("list_of_speakers/111")
        assert model.get("closed") is False
