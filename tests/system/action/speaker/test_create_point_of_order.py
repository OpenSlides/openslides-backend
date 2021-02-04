from tests.system.action.base import BaseActionTestCase


class SpeakerCreatePointOfOrderActionTest(BaseActionTestCase):
    def test_create_poo(self) -> None:
        self.create_model(
            "meeting/7844",
            {
                "name": "name_asdewqasd",
                "list_of_speakers_enable_point_of_order_speakers": True,
                "list_of_speakers_present_users_only": False,
            },
        )
        self.create_model("user/7", {"username": "talking"})
        self.create_model("user/8", {"username": "waiting"})
        self.create_model(
            "user/9",
            {
                "username": "waiting and poo",
                "speaker_$7844_ids": [3],
                "speaker_$_ids": ["7844"],
            },
        )
        self.create_model(
            "speaker/1", {"user_id": 7, "list_of_speakers_id": 23, "begin_time": 100000}
        )
        self.create_model(
            "speaker/2", {"user_id": 8, "list_of_speakers_id": 23, "weight": 10000}
        )
        self.create_model(
            "speaker/3", {"user_id": 9, "list_of_speakers_id": 23, "weight": 10000}
        )
        self.create_model(
            "list_of_speakers/23", {"speaker_ids": [1, 2, 3], "meeting_id": 7844}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "speaker.create",
                    "data": [
                        {
                            "user_id": 9,
                            "list_of_speakers_id": 23,
                            "point_of_order": True,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/3",
            {
                "user_id": 9,
                "list_of_speakers_id": 23,
                "weight": 10000,
                "point_of_order": None,
            },
        )
        self.assert_model_exists(
            "speaker/4",
            {
                "user_id": 9,
                "list_of_speakers_id": 23,
                "weight": 9999,
                "point_of_order": True,
            },
        )
        list_of_speakers = self.get_model("list_of_speakers/23")
        self.assertListEqual(list_of_speakers["speaker_ids"], [1, 2, 3, 4])
        user = self.get_model("user/9")
        self.assertListEqual(user["speaker_$7844_ids"], [3, 4])
        self.assertListEqual(user["speaker_$_ids"], ["7844"])

    def test_create_regular_besides_poo(self) -> None:
        self.create_model("meeting/7844", {"name": "name_asdewqasd"})
        self.create_model("user/7", {"username": "talking"})
        self.create_model("user/8", {"username": "waiting"})
        self.create_model(
            "user/9",
            {
                "username": "waiting and poo",
                "speaker_$7844_ids": [3],
                "speaker_$_ids": ["7844"],
            },
        )
        self.create_model(
            "speaker/1", {"user_id": 7, "list_of_speakers_id": 23, "begin_time": 100000}
        )
        self.create_model(
            "speaker/2", {"user_id": 8, "list_of_speakers_id": 23, "weight": 10000}
        )
        self.create_model(
            "speaker/3",
            {"user_id": 9, "list_of_speakers_id": 23, "point_of_order": True},
        )
        self.create_model(
            "list_of_speakers/23", {"speaker_ids": [1, 2, 3], "meeting_id": 7844}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "speaker.create",
                    "data": [{"user_id": 9, "list_of_speakers_id": 23}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/3",
            {"user_id": 9, "list_of_speakers_id": 23, "point_of_order": True},
        )
        speaker4 = self.get_model("speaker/4")
        self.assertEqual(speaker4["user_id"], 9)
        self.assertEqual(speaker4["list_of_speakers_id"], 23)
        self.assertIn(speaker4.get("point_of_order"), (False, None))
        list_of_speakers = self.get_model("list_of_speakers/23")
        self.assertListEqual(list_of_speakers["speaker_ids"], [1, 2, 3, 4])
        user = self.get_model("user/9")
        self.assertListEqual(user["speaker_$7844_ids"], [3, 4])
        self.assertListEqual(user["speaker_$_ids"], ["7844"])

    def test_create_poo_already_exist(self) -> None:
        self.create_model(
            "meeting/7844",
            {
                "name": "name_asdewqasd",
                "list_of_speakers_enable_point_of_order_speakers": True,
            },
        )
        self.create_model(
            "user/7", {"username": "test_username1", "speaker_$7844_ids": [42]}
        )
        self.create_model(
            "list_of_speakers/23", {"speaker_ids": [42], "meeting_id": 7844}
        )
        self.create_model(
            "speaker/42",
            {"user_id": 7, "list_of_speakers_id": 23, "point_of_order": True},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "speaker.create",
                    "data": [
                        {
                            "user_id": 7,
                            "list_of_speakers_id": 23,
                            "point_of_order": True,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn("User 7 is already on the list of speakers.", str(response.data))
        list_of_speakers = self.get_model("list_of_speakers/23")
        assert list_of_speakers.get("speaker_ids") == [42]

    def test_create_poo_not_activated_in_meeting(self) -> None:
        self.create_model("meeting/7844", {"name": "name_asdewqasd"})
        self.create_model(
            "user/9",
            {
                "username": "waiting and poo",
                "speaker_$7844_ids": [3],
                "speaker_$_ids": ["7844"],
            },
        )
        self.create_model(
            "list_of_speakers/23", {"speaker_ids": [], "meeting_id": 7844}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "speaker.create",
                    "data": [
                        {
                            "user_id": 9,
                            "list_of_speakers_id": 23,
                            "point_of_order": True,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("speaker/1")
        self.assertIn(
            "Point of order speakers are not enabled for this meeting.",
            str(response.data),
        )
