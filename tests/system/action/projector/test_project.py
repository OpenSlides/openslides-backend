from tests.system.action.base import BaseActionTestCase


class ProjectorProject(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {},
                "meeting/2": {},
                "projector/23": {
                    "meeting_id": 1,
                    "current_projection_ids": [105, 106],
                    "scroll": 80,
                },
                "projector/65": {"meeting_id": 1},
                "projector/75": {"meeting_id": 1, "current_projection_ids": [110, 111]},
                "projection/105": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/452",
                    "current_projector_id": 23,
                    "stable": False,
                },
                "projection/106": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/452",
                    "current_projector_id": 23,
                    "stable": True,
                },
                "projection/110": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/453",
                    "current_projector_id": 75,
                    "stable": False,
                },
                "projection/111": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/453",
                    "current_projector_id": 75,
                    "stable": True,
                },
                "assignment/452": {"meeting_id": 1},
                "assignment/453": {"meeting_id": 1},
                "assignment/567": {"meeting_id": 2},
            }
        )

    def test_project(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [23],
                "content_object_id": "assignment/453",
                "options": "",
                "stable": False,
                "type": "test",
            },
        )
        self.assert_status_code(response, 200)
        projection = self.get_model("projection/112")
        assert projection.get("current_projector_id") == 23
        assert projection.get("content_object_id") == "assignment/453"
        assert projection.get("options") == ""
        assert projection.get("stable") is False
        assert projection.get("type") == "test"
        projection = self.get_model("projection/105")
        assert projection.get("current_projector_id") is None
        assert projection.get("history_projector_id") == 23
        assert projection.get("weight") == 2
        projection = self.get_model("projection/106")
        assert projection.get("current_projector_id") == 23
        assert projection.get("history_projector_id") is None
        projection = self.get_model("projection/110")
        assert projection.get("current_projector_id") is None
        assert projection.get("history_projector_id") == 75
        projector_23 = self.get_model("projector/23")
        assert projector_23.get("current_projection_ids") == [106, 112]
        assert projector_23.get("history_projection_ids") == [105]
        assert projector_23.get("scroll") == 0
        projector_75 = self.get_model("projector/75")
        assert projector_75.get("current_projection_ids") == [111]
        assert projector_75.get("history_projection_ids") == [110]

    def test_project_2(self) -> None:
        response = self.request(
            "projector.project",
            {"ids": [23, 65], "content_object_id": "assignment/453", "stable": True},
        )
        self.assert_status_code(response, 200)
        projection_1 = self.get_model("projection/112")
        assert projection_1.get("current_projector_id") == 23
        assert projection_1.get("content_object_id") == "assignment/453"
        projection_2 = self.get_model("projection/113")
        assert projection_2.get("current_projector_id") == 65
        assert projection_2.get("content_object_id") == "assignment/453"
        projector_23 = self.get_model("projector/23")
        assert projector_23.get("current_projection_ids") == [105, 106, 112]
        projector_65 = self.get_model("projector/65")
        assert projector_65.get("current_projection_ids") == [113]

    def test_project_3(self) -> None:
        response = self.request(
            "projector.project",
            {"ids": [], "content_object_id": "assignment/453", "stable": False},
        )
        self.assert_status_code(response, 200)
        projector_23 = self.get_model("projector/75")
        assert projector_23.get("current_projection_ids") == [111]
        assert projector_23.get("history_projection_ids") == [110]
        projection_110 = self.get_model("projection/110")
        assert projection_110.get("current_projector_id") is None
        assert projection_110.get("history_projector_id") == 75
        assert projection_110.get("weight") == 2

    def test_project_wrong_meeting(self) -> None:
        response = self.request(
            "projector.project",
            {"ids": [23], "content_object_id": "assignment/567", "stable": True},
        )
        self.assert_status_code(response, 400)
        assert (
            "The relation current_projector_id requires the following fields to be equal:\\nprojection/112/meeting_id: 2\\nprojector/23/meeting_id: 1"
            in response.data.decode()
        )

    def test_project_not_unique_ids(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [23, 23],
                "content_object_id": "assignment/453",
                "options": "",
                "stable": False,
                "type": "test",
            },
        )
        self.assert_status_code(response, 400)
        assert "data.ids must contain unique items" in response.data.decode()
