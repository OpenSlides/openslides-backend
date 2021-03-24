from tests.system.action.base import BaseActionTestCase


class ListOfSpeakersUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_xQyvfmsS"},
                "list_of_speakers/111": {"closed": False, "meeting_id": 222},
            }
        )
        response = self.request("list_of_speakers.update", {"id": 111, "closed": True})
        self.assert_status_code(response, 200)

        model = self.get_model("list_of_speakers/111")
        assert model.get("closed") is True

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_xQyvfmsS"},
                "list_of_speakers/111": {"closed": False, "meeting_id": 222},
            }
        )

        response = self.request("list_of_speakers.update", {"id": 112, "closed": True})
        self.assert_status_code(response, 400)
        model = self.get_model("list_of_speakers/111")
        assert model.get("closed") is False

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/222": {"name": "name_xQyvfmsS"},
                "list_of_speakers/111": {"closed": False, "meeting_id": 222},
            },
            "list_of_speakers.update",
            {"id": 111, "closed": True},
        )
