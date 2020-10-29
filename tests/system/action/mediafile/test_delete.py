from tests.system.action.base import BaseActionTestCase


class MediafileDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("mediafile/111", {"title": "title_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "mediafile.delete", "data": [{"id": 111}]}],
        )

        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("mediafile/112", {"title": "title_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "mediafile.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("mediafile/112")
        assert model.get("title") == "title_srtgb123"

    def test_delete_directory(self) -> None:
        self.create_model(
            "mediafile/112",
            {"title": "title_srtgb123", "is_directory": True, "child_ids": [110]},
        )
        self.create_model(
            "mediafile/110", {"title": "title_ghjeu212", "is_directory": False}
        )
        response = self.client.post(
            "/", json=[{"action": "mediafile.delete", "data": [{"id": 112}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/110")
        self.assert_model_deleted("mediafile/112")

    def test_delete_directory_list_of_children(self) -> None:
        self.create_model(
            "mediafile/112",
            {"title": "title_srtgb123", "is_directory": True, "child_ids": [110]},
        )
        self.create_model(
            "mediafile/110",
            {"title": "title_ghjeu212", "is_directory": True, "child_ids": [113]},
        )
        self.create_model(
            "mediafile/113",
            {"title": "title_del2", "is_directory": False, "child_ids": []},
        )
        response = self.client.post(
            "/", json=[{"action": "mediafile.delete", "data": [{"id": 112}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/110")
        self.assert_model_deleted("mediafile/112")
        self.assert_model_deleted("mediafile/113")

    def test_delete_directory_two_children(self) -> None:
        self.create_model(
            "mediafile/112",
            {"title": "title_srtgb123", "is_directory": True, "child_ids": [110, 113]},
        )
        self.create_model(
            "mediafile/110",
            {"title": "title_ghjeu212", "is_directory": False, "child_ids": []},
        )
        self.create_model(
            "mediafile/113",
            {"title": "title_del2", "is_directory": False, "child_ids": []},
        )
        response = self.client.post(
            "/", json=[{"action": "mediafile.delete", "data": [{"id": 112}]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("mediafile/110")
        self.assert_model_deleted("mediafile/112")
        self.assert_model_deleted("mediafile/113")
