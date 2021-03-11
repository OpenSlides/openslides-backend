from tests.system.action.base import BaseActionTestCase


class SpeakerCreatePointOfOrderActionTest(BaseActionTestCase):
    def test_create_poo_in_only_talker_list(self) -> None:
        self.set_models(
            {
                "meeting/7844": {
                    "name": "name_asdewqasd",
                    "list_of_speakers_enable_point_of_order_speakers": True,
                },
                "user/1": {"meeting_id": 7844},
                "user/7": {"username": "talking", "meeting_id": 7844},
                "speaker/1": {
                    "user_id": 7,
                    "list_of_speakers_id": 23,
                    "begin_time": 100000,
                    "weight": 5,
                },
                "list_of_speakers/23": {"speaker_ids": [1], "meeting_id": 7844},
            }
        )
        response = self.request(
            "speaker.create",
            {
                "user_id": 1,
                "list_of_speakers_id": 23,
                "point_of_order": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/2",
            {"user_id": 1, "point_of_order": True, "weight": 1},
        )
        self.assert_model_exists("list_of_speakers/23", {"speaker_ids": [1, 2]})

    def test_create_poo_after_existing_poo_before_standard(self) -> None:
        self.set_models(
            {
                "meeting/7844": {
                    "name": "name_asdewqasd",
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "list_of_speakers_present_users_only": False,
                },
                "user/7": {"username": "talking with poo", "meeting_id": 7844},
                "user/8": {"username": "waiting with poo", "meeting_id": 7844},
                "user/1": {
                    "speaker_$7844_ids": [3],
                    "speaker_$_ids": ["7844"],
                    "meeting_id": 7844,
                },
                "speaker/1": {
                    "user_id": 7,
                    "list_of_speakers_id": 23,
                    "point_of_order": True,
                    "begin_time": 100000,
                    "weight": 1,
                    "meeting_id": 7844,
                },
                "speaker/2": {
                    "user_id": 8,
                    "list_of_speakers_id": 23,
                    "weight": 2,
                    "point_of_order": True,
                    "meeting_id": 7844,
                },
                "speaker/3": {
                    "user_id": 1,
                    "list_of_speakers_id": 23,
                    "weight": 3,
                    "meeting_id": 7844,
                },
                "list_of_speakers/23": {"speaker_ids": [1, 2, 3], "meeting_id": 7844},
            }
        )
        response = self.request(
            "speaker.create",
            {
                "user_id": 1,
                "list_of_speakers_id": 23,
                "point_of_order": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/2",
            {
                "user_id": 8,
                "weight": 1,
                "point_of_order": True,
            },
        )
        self.assert_model_exists(
            "speaker/4",
            {
                "user_id": 1,
                "weight": 2,
                "point_of_order": True,
            },
        )
        self.assert_model_exists(
            "speaker/3",
            {
                "user_id": 1,
                "weight": 3,
                "point_of_order": None,
            },
        )
        self.assert_model_exists(
            "list_of_speakers/23",
            {"speaker_ids": [1, 2, 3, 4]},
        )

    def test_create_poo_after_existing_poo_before_standard_and_more(self) -> None:
        self.set_models(
            {
                "meeting/7844": {
                    "name": "name_asdewqasd",
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "list_of_speakers_present_users_only": False,
                },
                "user/7": {"username": "waiting with poo1", "meeting_id": 7844},
                "user/8": {"username": "waiting with poo2", "meeting_id": 7844},
                "user/1": {
                    "speaker_$7844_ids": [3],
                    "speaker_$_ids": ["7844"],
                    "meeting_id": 7844,
                },
                "speaker/1": {
                    "user_id": 7,
                    "list_of_speakers_id": 23,
                    "point_of_order": True,
                    "weight": 1,
                    "meeting_id": 7844,
                },
                "speaker/2": {
                    "user_id": 8,
                    "list_of_speakers_id": 23,
                    "weight": 2,
                    "point_of_order": False,
                    "meeting_id": 7844,
                },
                "speaker/3": {
                    "user_id": 1,
                    "list_of_speakers_id": 23,
                    "weight": 3,
                    "meeting_id": 7844,
                },
                "speaker/4": {
                    "user_id": 8,
                    "list_of_speakers_id": 23,
                    "weight": 4,
                    "point_of_order": True,
                    "meeting_id": 7844,
                },
                "list_of_speakers/23": {
                    "speaker_ids": [1, 2, 3, 4],
                    "meeting_id": 7844,
                },
            }
        )
        response = self.request(
            "speaker.create",
            {
                "user_id": 1,
                "list_of_speakers_id": 23,
                "point_of_order": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/1",
            {
                "user_id": 7,
                "weight": 1,
                "point_of_order": True,
            },
        )
        self.assert_model_exists(
            "speaker/5",
            {
                "user_id": 1,
                "weight": 2,
                "point_of_order": True,
            },
        )
        self.assert_model_exists(
            "speaker/2",
            {
                "user_id": 8,
                "weight": 3,
                "point_of_order": False,
            },
        )
        self.assert_model_exists(
            "speaker/3",
            {
                "user_id": 1,
                "weight": 4,
                "point_of_order": None,
            },
        )
        self.assert_model_exists(
            "speaker/4",
            {
                "user_id": 8,
                "weight": 5,
                "point_of_order": True,
            },
        )
        self.assert_model_exists(
            "list_of_speakers/23",
            {"speaker_ids": [1, 2, 3, 4, 5]},
        )

    def test_create_poo_after_existing_poo_at_the_end(self) -> None:
        self.set_models(
            {
                "meeting/7844": {
                    "name": "name_asdewqasd",
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "list_of_speakers_present_users_only": False,
                },
                "user/7": {"username": "waiting with poo", "meeting_id": 7844},
                "user/1": {
                    "speaker_$7844_ids": [3],
                    "speaker_$_ids": ["7844"],
                    "meeting_id": 7844,
                },
                "speaker/1": {
                    "user_id": 7,
                    "list_of_speakers_id": 23,
                    "point_of_order": True,
                    "weight": 1,
                    "meeting_id": 7844,
                },
                "list_of_speakers/23": {"speaker_ids": [1], "meeting_id": 7844},
            }
        )
        response = self.request(
            "speaker.create",
            {
                "user_id": 1,
                "list_of_speakers_id": 23,
                "point_of_order": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "speaker/2",
            {
                "user_id": 1,
                "weight": 2,
                "point_of_order": True,
            },
        )
        self.assert_model_exists("list_of_speakers/23", {"speaker_ids": [1, 2]})

    def test_create_poo_already_exist(self) -> None:
        self.set_models(
            {
                "meeting/7844": {
                    "name": "name_asdewqasd",
                    "list_of_speakers_enable_point_of_order_speakers": True,
                },
                "user/1": {
                    "username": "test_username1",
                    "speaker_$7844_ids": [42],
                    "meeting_id": 7844,
                },
                "list_of_speakers/23": {"speaker_ids": [42], "meeting_id": 7844},
                "speaker/42": {
                    "user_id": 1,
                    "list_of_speakers_id": 23,
                    "point_of_order": True,
                    "meeting_id": 7844,
                },
            }
        )
        response = self.request(
            "speaker.create",
            {
                "user_id": 1,
                "list_of_speakers_id": 23,
                "point_of_order": True,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "User 1 is already on the list of speakers.", response.json["message"]
        )
        list_of_speakers = self.get_model("list_of_speakers/23")
        assert list_of_speakers.get("speaker_ids") == [42]

    def test_create_poo_not_activated_in_meeting(self) -> None:
        self.set_models(
            {
                "meeting/7844": {"name": "name_asdewqasd"},
                "list_of_speakers/23": {"speaker_ids": [], "meeting_id": 7844},
            }
        )
        response = self.request(
            "speaker.create",
            {
                "user_id": 1,
                "list_of_speakers_id": 23,
                "point_of_order": True,
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("speaker/1")
        self.assertIn(
            "Point of order speakers are not enabled for this meeting.",
            response.json["message"],
        )

    def test_create_poo_without_user_id(self) -> None:
        self.set_models(
            {
                "meeting/7844": {
                    "name": "name_asdewqasd",
                    "list_of_speakers_enable_point_of_order_speakers": True,
                    "list_of_speakers_present_users_only": False,
                },
                "user/7": {"username": "talking", "meeting_id": 7844},
                "user/8": {"username": "waiting", "meeting_id": 7844},
                "speaker/1": {
                    "user_id": 7,
                    "list_of_speakers_id": 23,
                    "begin_time": 100000,
                    "meeting_id": 7844,
                },
                "speaker/2": {
                    "user_id": 8,
                    "list_of_speakers_id": 23,
                    "weight": 10000,
                    "meeting_id": 7844,
                },
                "list_of_speakers/23": {"speaker_ids": [1, 2], "meeting_id": 7844},
            }
        )
        response = self.request(
            "speaker.create",
            {
                "list_of_speakers_id": 23,
                "point_of_order": True,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['list_of_speakers_id', 'user_id'] properties",
            response.json["message"],
        )
