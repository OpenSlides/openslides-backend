from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ListOfSpeakersReAddLastActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {
                    "is_active_in_organization_id": 1,
                },
                "user/42": {"meeting_user_ids": [42]},
                "user/43": {"meeting_user_ids": [43]},
                "user/44": {"meeting_user_ids": [44]},
                "list_of_speakers/111": {
                    "meeting_id": 1,
                    "speaker_ids": [222, 223, 224],
                },
                "speaker/222": {
                    "list_of_speakers_id": 111,
                    "meeting_user_id": 42,
                    "begin_time": 1000,
                    "end_time": 2000,
                    "meeting_id": 1,
                },
                "speaker/223": {
                    "list_of_speakers_id": 111,
                    "meeting_user_id": 43,
                    "begin_time": 3000,
                    "end_time": 4000,
                    "meeting_id": 1,
                },
                "speaker/224": {
                    "list_of_speakers_id": 111,
                    "meeting_user_id": 44,
                    "begin_time": 5000,
                    "meeting_id": 1,
                },
                "meeting_user/42": {
                    "meeting_id": 1,
                    "user_id": 42,
                    "speaker_ids": [222],
                },
                "meeting_user/43": {
                    "meeting_id": 1,
                    "user_id": 43,
                    "speaker_ids": [223],
                },
                "meeting_user/44": {
                    "meeting_id": 1,
                    "user_id": 44,
                    "speaker_ids": [224],
                },
            }
        )

    def test_correct(self) -> None:
        response = self.request("list_of_speakers.re_add_last", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("list_of_speakers/111")
        self.assertEqual(model.get("speaker_ids"), [222, 223, 224])
        model = self.get_model("speaker/223")
        self.assertTrue(model.get("begin_time") is None)
        self.assertTrue(model.get("end_time") is None)
        self.assertEqual(model.get("meeting_user_id"), 43)
        self.assertEqual(model.get("weight"), -1)
        model = self.get_model("meeting_user/43")
        self.assertEqual(model.get("speaker_ids"), [223])

    def test_correct_in_closed_list(self) -> None:
        self.set_models(
            {
                "list_of_speakers/111": {
                    "closed": True,
                },
            }
        )
        response = self.request("list_of_speakers.re_add_last", {"id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("list_of_speakers/111")
        self.assertCountEqual(model.get("speaker_ids", []), [222, 223, 224])
        self.assert_model_exists(
            "speaker/223",
            {"begin_time": None, "end_time": None, "meeting_user_id": 43, "weight": -1},
        )
        self.assert_model_exists(
            "speaker/222", {"begin_time": 1000, "end_time": 2000, "meeting_user_id": 42}
        )

    def test_no_speakers(self) -> None:
        self.set_models(
            {
                "list_of_speakers/112": {
                    "meeting_id": 1,
                    "speaker_ids": [],
                },
            }
        )
        response = self.request("list_of_speakers.re_add_last", {"id": 112})
        self.assert_status_code(response, 400)
        self.assertTrue(
            "List of speakers 112 has no speakers." in response.json["message"]
        )

    def test_no_last_speaker(self) -> None:
        self.set_models(
            {
                "speaker/222": {
                    "begin_time": None,
                    "end_time": None,
                },
                "speaker/223": {
                    "begin_time": None,
                    "end_time": None,
                },
            }
        )
        response = self.request("list_of_speakers.re_add_last", {"id": 111})
        self.assert_status_code(response, 400)
        self.assertTrue(
            "There is no last speaker that can be re-added." in response.json["message"]
        )

    def test_last_speaker_poos(self) -> None:
        self.set_models(
            {
                "speaker/223": {
                    "point_of_order": True,
                },
            }
        )
        response = self.request("list_of_speakers.re_add_last", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/223",
            {
                "list_of_speakers_id": 111,
                "meeting_user_id": 43,
                "begin_time": None,
                "end_time": None,
                "meeting_id": 1,
            },
        )

    def test_last_speaker_also_in_waiting_list(self) -> None:
        self.set_models(
            {
                "speaker/225": {
                    "list_of_speakers_id": 111,
                    "meeting_id": 1,
                    "meeting_user_id": 43,
                },
            }
        )
        response = self.request("list_of_speakers.re_add_last", {"id": 111})
        self.assert_status_code(response, 400)
        self.assertTrue(
            "User 43 is already on the list of speakers." in response.json["message"]
        )

    def test_last_speaker_also_in_waiting_list_but_poos(self) -> None:
        self.set_models(
            {
                "speaker/224": {
                    "meeting_user_id": 43,
                    "point_of_order": True,
                },
            }
        )
        response = self.request("list_of_speakers.re_add_last", {"id": 111})
        self.assert_status_code(response, 200)

    def test_last_speaker_poos_also_in_waiting_list(self) -> None:
        self.set_models(
            {
                "speaker/223": {
                    "point_of_order": True,
                },
                "speaker/224": {
                    "meeting_user_id": 43,
                    "point_of_order": True,
                },
            }
        )
        response = self.request("list_of_speakers.re_add_last", {"id": 111})
        self.assert_status_code(response, 400)

    def test_last_speaker_poos_also_in_waiting_list_but_normal(self) -> None:
        self.set_models(
            {
                "speaker/223": {
                    "point_of_order": True,
                },
                "speaker/224": {
                    "meeting_user_id": 43,
                },
            }
        )
        response = self.request("list_of_speakers.re_add_last", {"id": 111})
        self.assert_status_code(response, 200)

    def test_re_add_last_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "list_of_speakers.re_add_last",
            {"id": 111},
        )

    def test_re_add_last_permissions(self) -> None:
        self.base_permission_test(
            {},
            "list_of_speakers.re_add_last",
            {"id": 111},
            Permissions.ListOfSpeakers.CAN_MANAGE,
        )
