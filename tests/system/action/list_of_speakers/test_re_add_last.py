from tests.system.action.base import BaseActionTestCase


class ListOfSpeakersReAddLastActionTest(BaseActionTestCase):
    def test_correct(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_xQyvfmsS"},
                "user/42": {"username": "test_username42", "speaker_$222_ids": [222]},
                "user/43": {"username": "test_username43", "speaker_$222_ids": [223]},
                "user/44": {"username": "test_username43", "speaker_$222_ids": [224]},
                "list_of_speakers/111": {
                    "closed": False,
                    "meeting_id": 222,
                    "speaker_ids": [222, 223, 224],
                },
                "speaker/222": {
                    "list_of_speakers_id": 111,
                    "user_id": 42,
                    "begin_time": 1000,
                    "end_time": 2000,
                },
                "speaker/223": {
                    "list_of_speakers_id": 111,
                    "user_id": 43,
                    "begin_time": 3000,
                    "end_time": 4000,
                },
                "speaker/224": {
                    "list_of_speakers_id": 111,
                    "user_id": 44,
                    "begin_time": 5000,
                },
            }
        )
        response = self.request("list_of_speakers.re_add_last", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("list_of_speakers/111")
        self.assertEqual(model.get("speaker_ids"), [222, 223, 224])
        model = self.get_model("speaker/223")
        self.assertTrue(model.get("begin_time") is None)
        self.assertTrue(model.get("end_time") is None)
        self.assertEqual(model.get("user_id"), 43)
        self.assertEqual(model.get("weight"), -1)
        model = self.get_model("user/43")
        self.assertEqual(model.get("speaker_$222_ids"), [223])

    def test_no_speakers(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_xQyvfmsS"},
                "list_of_speakers/111": {
                    "closed": False,
                    "meeting_id": 222,
                    "speaker_ids": [],
                },
            }
        )
        response = self.request("list_of_speakers.re_add_last", {"id": 111})
        self.assert_status_code(response, 400)
        self.assertTrue(
            "List of speakers 111 has no speakers." in response.json["message"]
        )

    def test_no_last_speaker(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_xQyvfmsS"},
                "user/42": {"username": "test_username42", "speaker_$222_ids": [223]},
                "list_of_speakers/111": {
                    "closed": False,
                    "meeting_id": 222,
                    "speaker_ids": [223],
                },
                "speaker/223": {
                    "list_of_speakers_id": 111,
                    "user_id": 42,
                    "begin_time": 3000,
                },
            }
        )
        response = self.request("list_of_speakers.re_add_last", {"id": 111})
        self.assert_status_code(response, 400)
        self.assertTrue(
            "There is no last speaker that can be re-added." in response.json["message"]
        )

    def test_last_speaker_also_in_waiting_list(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_xQyvfmsS"},
                "user/42": {
                    "username": "test_username42",
                    "speaker_$222_ids": [223, 224],
                },
                "list_of_speakers/111": {
                    "closed": False,
                    "meeting_id": 222,
                    "speaker_ids": [223, 224],
                },
                "speaker/223": {
                    "list_of_speakers_id": 111,
                    "user_id": 42,
                    "begin_time": 3000,
                    "end_time": 4000,
                },
                "speaker/224": {"list_of_speakers_id": 111, "user_id": 42},
            }
        )
        response = self.request("list_of_speakers.re_add_last", {"id": 111})
        self.assert_status_code(response, 400)
        self.assertTrue(
            "User 42 is already on the list of speakers." in response.json["message"]
        )

    def test_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/222": {"name": "name_xQyvfmsS"},
                "user/42": {"username": "test_username42", "speaker_$222_ids": [222]},
                "user/43": {"username": "test_username43", "speaker_$222_ids": [223]},
                "user/44": {"username": "test_username43", "speaker_$222_ids": [224]},
                "list_of_speakers/111": {
                    "closed": False,
                    "meeting_id": 222,
                    "speaker_ids": [222, 223, 224],
                },
                "speaker/222": {
                    "list_of_speakers_id": 111,
                    "user_id": 42,
                    "begin_time": 1000,
                    "end_time": 2000,
                },
                "speaker/223": {
                    "list_of_speakers_id": 111,
                    "user_id": 43,
                    "begin_time": 3000,
                    "end_time": 4000,
                },
                "speaker/224": {
                    "list_of_speakers_id": 111,
                    "user_id": 44,
                    "begin_time": 5000,
                },
            },
            "list_of_speakers.re_add_last",
            {"id": 111},
        )
