from tests.system.action.base import BaseActionTestCase


class MediafileMoveActionTest(BaseActionTestCase):
    def test_move_parent_none(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "mediafile/7",
            {
                "title": "title_7",
                "meeting_id": 222,
                "parent_id": None,
                "child_ids": [8, 9],
            },
        )
        self.create_model(
            "mediafile/8",
            {
                "title": "title_8",
                "meeting_id": 222,
                "parent_id": 7,
                "child_ids": [],
            },
        )
        self.create_model(
            "mediafile/9",
            {
                "title": "title_9",
                "meeting_id": 222,
                "parent_id": 7,
                "child_ids": [10],
            },
        )
        self.create_model(
            "mediafile/10",
            {
                "title": "title_10",
                "meeting_id": 222,
                "parent_id": 9,
                "child_ids": [],
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.move",
                    "data": [{"meeting_id": 222, "ids": [8, 9], "parent_id": None}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        mediafile_7 = self.get_model("mediafile/7")
        assert mediafile_7.get("child_ids") == []
        assert mediafile_7.get("parent_id") is None
        mediafile_8 = self.get_model("mediafile/8")
        assert mediafile_8.get("child_ids") == []
        assert mediafile_8.get("parent_id") is None
        assert mediafile_8.get("is_public")
        mediafile_9 = self.get_model("mediafile/9")
        assert mediafile_9.get("child_ids") == [10]
        assert mediafile_9.get("parent_id") is None
        assert mediafile_9.get("is_public")
        mediafile_10 = self.get_model("mediafile/10")
        assert mediafile_10.get("is_public")
        assert mediafile_10.get("inherited_access_group_ids") == []

    def test_move_parent_set(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "mediafile/7",
            {
                "title": "title_7",
                "meeting_id": 222,
                "parent_id": None,
                "child_ids": [],
                "is_directory": True,
                "is_public": True,
                "inherited_access_group_ids": [],
            },
        )
        self.create_model(
            "mediafile/8",
            {
                "title": "title_8",
                "meeting_id": 222,
                "parent_id": None,
                "child_ids": [],
            },
        )
        self.create_model(
            "mediafile/9",
            {
                "title": "title_9",
                "meeting_id": 222,
                "parent_id": None,
                "child_ids": [],
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.move",
                    "data": [{"meeting_id": 222, "ids": [8, 9], "parent_id": 7}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        mediafile_7 = self.get_model("mediafile/7")
        assert mediafile_7.get("child_ids") == [8, 9]
        assert mediafile_7.get("parent_id") is None
        mediafile_8 = self.get_model("mediafile/8")
        assert mediafile_8.get("child_ids") == []
        assert mediafile_8.get("parent_id") == 7
        assert mediafile_8.get("inherited_access_group_ids") == []
        assert mediafile_8.get("is_public")
        mediafile_9 = self.get_model("mediafile/9")
        assert mediafile_9.get("child_ids") == []
        assert mediafile_9.get("parent_id") == 7
        assert mediafile_9.get("is_public")
        assert mediafile_9.get("inherited_access_group_ids") == []

    def test_move_non_directory_parent_set(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "mediafile/7",
            {
                "title": "title_7",
                "meeting_id": 222,
                "parent_id": None,
                "child_ids": [],
                "is_directory": False,
            },
        )
        self.create_model(
            "mediafile/8",
            {
                "title": "title_8",
                "meeting_id": 222,
                "parent_id": None,
                "child_ids": [],
            },
        )
        self.create_model(
            "mediafile/9",
            {
                "title": "title_9",
                "meeting_id": 222,
                "parent_id": None,
                "child_ids": [],
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.move",
                    "data": [{"meeting_id": 222, "ids": [8, 9], "parent_id": 7}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "New parent is not a directory.", response.json.get("message", "")
        )

    def test_move_multiple_payload_items(self) -> None:
        self.create_model("meeting/222", {})
        self.create_model(
            "mediafile/7",
            {"meeting_id": 222, "is_directory": True},
        )
        self.create_model(
            "mediafile/8",
            {"meeting_id": 222, "is_directory": True},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.move",
                    "data": [
                        {"meeting_id": 222, "ids": [8], "parent_id": 7},
                        {"meeting_id": 222, "ids": [7], "parent_id": 8},
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        mediafile_7 = self.get_model("mediafile/7")
        assert mediafile_7.get("parent_id") is None
        mediafile_8 = self.get_model("mediafile/8")
        assert mediafile_8.get("parent_id") is None

    def test_move_circle(self) -> None:
        self.create_model("meeting/222", {})
        self.create_model(
            "mediafile/7",
            {"meeting_id": 222, "is_directory": True, "child_ids": [8]},
        )
        self.create_model(
            "mediafile/8",
            {"meeting_id": 222, "is_directory": True, "parent_id": 7},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.move",
                    "data": [
                        {"meeting_id": 222, "ids": [7], "parent_id": 8},
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Moving item 7 to one of its children is not possible.",
            response.json.get("message", ""),
        )
