from tests.system.action.base import BaseActionTestCase


class ProjectorProject(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {},
                "meeting/2": {},
                "projector/23": {"meeting_id": 1},
                "projector/65": {"meeting_id": 1},
                "projector/75": {"meeting_id": 1, "current_projection_ids": [110, 111]},
                "projection/110": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/453",
                    "current_projector_id": 75,
                    "stable": False
                },
                "projection/111": {
                    "meeting_id": 1,
                    "content_object_id": "assignment/453",
                    "current_projector_id": 75,
                    "stable": True,
                },
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
