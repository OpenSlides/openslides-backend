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
                "stable": True,
                "type": "test",
            },
        )
        self.assert_status_code(response, 200)
        projection = self.get_model("projection/1")
        assert projection.get("current_projector_id") == 23
        assert projection.get("content_object_id") == "assignment/453"
        assert projection.get("options") == ""
        assert projection.get("stable") is True
        assert projection.get("type") == "test"

    def test_project_2(self) -> None:
        response = self.request(
            "projector.project",
            {"ids": [23, 65], "content_object_id": "assignment/453"},
        )
        self.assert_status_code(response, 200)
        projection_1 = self.get_model("projection/1")
        assert projection_1.get("current_projector_id") == 23
        assert projection_1.get("content_object_id") == "assignment/453"
        projection_2 = self.get_model("projection/2")
        assert projection_2.get("current_projector_id") == 65
        assert projection_2.get("content_object_id") == "assignment/453"

    def test_project_wrong_meeting(self) -> None:
        response = self.request(
            "projector.project", {"ids": [23], "content_object_id": "assignment/567"}
        )
        self.assert_status_code(response, 400)
        assert (
            "The relation current_projector_id requires the following fields to be equal:\\nprojection/1/meeting_id: 2\\nprojector/23/meeting_id: 1"
            in response.data.decode()
        )
