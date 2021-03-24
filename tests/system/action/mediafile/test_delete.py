from tests.system.action.base import BaseActionTestCase


class MediafileDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/34": {},
                "mediafile/111": {"title": "title_srtgb123", "meeting_id": 34},
            }
        )
        response = self.request("mediafile.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/34": {},
                "mediafile/112": {"title": "title_srtgb123", "meeting_id": 34},
            }
        )
        response = self.request("mediafile.delete", {"id": 111})
        self.assert_status_code(response, 400)
        model = self.get_model("mediafile/112")
        assert model.get("title") == "title_srtgb123"

    def test_delete_directory(self) -> None:
        self.set_models(
            {
                "meeting/34": {},
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "is_directory": True,
                    "child_ids": [110],
                    "meeting_id": 34,
                },
                "mediafile/110": {
                    "title": "title_ghjeu212",
                    "is_directory": False,
                    "parent_id": 112,
                    "meeting_id": 34,
                },
            }
        )
        response = self.request("mediafile.delete", {"id": 112})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/110")
        self.assert_model_deleted("mediafile/112")

    def test_delete_directory_list_of_children(self) -> None:
        self.set_models(
            {
                "meeting/34": {},
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "is_directory": True,
                    "child_ids": [110],
                    "meeting_id": 34,
                },
                "mediafile/110": {
                    "title": "title_ghjeu212",
                    "is_directory": True,
                    "child_ids": [113],
                    "parent_id": 112,
                    "meeting_id": 34,
                },
                "mediafile/113": {
                    "title": "title_del2",
                    "is_directory": False,
                    "child_ids": [],
                    "parent_id": 110,
                    "meeting_id": 34,
                },
            }
        )
        response = self.request("mediafile.delete", {"id": 112})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/110")
        self.assert_model_deleted("mediafile/112")
        self.assert_model_deleted("mediafile/113")

    def test_delete_directory_two_children(self) -> None:
        self.set_models(
            {
                "meeting/34": {},
                "mediafile/112": {
                    "title": "title_srtgb123",
                    "is_directory": True,
                    "child_ids": [110, 113],
                    "meeting_id": 34,
                },
                "mediafile/110": {
                    "title": "title_ghjeu212",
                    "is_directory": False,
                    "child_ids": [],
                    "parent_id": 112,
                    "meeting_id": 34,
                },
                "mediafile/113": {
                    "title": "title_del2",
                    "is_directory": False,
                    "child_ids": [],
                    "parent_id": 112,
                    "meeting_id": 34,
                },
            }
        )
        response = self.request("mediafile.delete", {"id": 112})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/110")
        self.assert_model_deleted("mediafile/112")
        self.assert_model_deleted("mediafile/113")

    def test_delete_check_relations(self) -> None:
        self.set_models(
            {
                "meeting/111": {"logo_$place_id": 222, "logo_$_id": ["place"]},
                "mediafile/222": {
                    "used_as_logo_$place_in_meeting_id": 111,
                    "used_as_logo_$_in_meeting_id": ["place"],
                    "meeting_id": 111,
                },
            }
        )
        response = self.request("mediafile.delete", {"id": 222})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/222")
        meeting = self.get_model("meeting/111")
        assert meeting.get("logo_$place_id") is None
        assert meeting.get("logo_$_id") == []

    def test_delete_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "meeting/111": {"logo_$place_id": 222, "logo_$_id": ["place"]},
                "mediafile/222": {
                    "used_as_logo_$place_in_meeting_id": 111,
                    "used_as_logo_$_in_meeting_id": ["place"],
                    "meeting_id": 111,
                },
            },
            "mediafile.delete",
            {"id": 222},
        )
