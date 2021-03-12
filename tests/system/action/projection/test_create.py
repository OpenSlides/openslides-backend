from tests.system.action.base import BaseActionTestCase


class ProjectionCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models({
            "meeting/1": {},
            "assignment/1": {"meeting_id": 1},
            "projector/2": {"meeting_id": 1},
        })
        response = self.request("projection.create",
            {"content_object_id": "assignment/1", 
             "current_projector_id": 2,
             "options": "",
             "stable": True,
             "type": "test",
             "meeting_id": 1})
        self.assert_status_code(response, 200)
        projection = self.get_model("projection/1")
        assert projection.get("content_object_id") == "assignment/1"
        assert projection.get("meeting_id") == 1
        assert projection.get("options") == ""
        assert projection.get("stable") == True
        assert projection.get("type") == "test"
        projector = self.get_model("projector/2")
        assert projector.get("current_projection_ids") == [1]
        meeting = self.get_model("meeting/1")
        assert meeting.get("all_projection_ids") == [1]
