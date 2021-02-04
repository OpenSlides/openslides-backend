from tests.system.action.base import BaseActionTestCase


class SpeakerSortActionTest(BaseActionTestCase):
    def test_sort_correct_1(self) -> None:
        self.create_model("list_of_speakers/222", {})
        self.create_model("speaker/31", {"list_of_speakers_id": 222})
        self.create_model("speaker/32", {"list_of_speakers_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "speaker.sort",
                    "data": [{"list_of_speakers_id": 222, "speaker_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("speaker/31")
        assert model_31.get("weight") == 2
        model_32 = self.get_model("speaker/32")
        assert model_32.get("weight") == 1

    def test_sort_missing_model(self) -> None:
        self.create_model("list_of_speakers/222", {})
        self.create_model("speaker/31", {"list_of_speakers_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "speaker.sort",
                    "data": [{"list_of_speakers_id": 222, "speaker_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Id 32 not in db_instances." in response.json.get("message", "")

    def test_sort_another_section_db(self) -> None:
        self.create_model("list_of_speakers/222", {})
        self.create_model("speaker/31", {"list_of_speakers_id": 222})
        self.create_model("speaker/32", {"list_of_speakers_id": 222})
        self.create_model("speaker/33", {"list_of_speakers_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "speaker.sort",
                    "data": [{"list_of_speakers_id": 222, "speaker_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Additional db_instances found." in response.json.get("message", "")
