from tests.system.action.base import BaseActionTestCase


class ProjectorDelete(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "projector/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 1,
                    "used_as_default_$motion_in_meeting_id": 1,
                    "used_as_default_$_in_meeting_id": ["motion"],
                },
                "projector/113": {
                    "name": "name_test1",
                    "used_as_reference_projector_meeting_id": 1,
                    "meeting_id": 1,
                },
                "meeting/1": {
                    "reference_projector_id": 113,
                    "default_projector_$_id": ["motion"],
                    "default_projector_$motion_id": 111,
                    "projector_ids": [111, 113],
                },
            }
        )

    def test_delete_correct(self) -> None:
        meeting = self.get_model("meeting/1")
        response = self.request("projector.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("projector/111")
        meeting = self.get_model("meeting/1")
        assert meeting.get("default_projector_$_id") == ["motion"]
        assert meeting.get("default_projector_$motion_id") == 113
        self.assert_model_exists(
            "projector/113",
            {
                "used_as_default_$motion_in_meeting_id": 1,
                "used_as_default_$_in_meeting_id": ["motion"],
                "used_as_reference_projector_meeting_id": 1,
            },
        )

    def test_delete_missing_meeting_id(self) -> None:
        self.set_models(
            {
                "projector/112": {"name": "name_srtgb123"},
            }
        )
        response = self.request("projector.delete", {"id": 112})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Datastore service sends HTTP 400. {'msg': \"The key 'meeting/None' is no fqid, fqfield or collectionkey\", 'type': 1, 'type_verbose': 'INVALID_FORMAT'}",
            response.json["message"],
        )
        model = self.get_model("projector/112")
        assert model.get("name") == "name_srtgb123"

    def test_delete_prevent_if_used_as_reference(self) -> None:
        response = self.request("projector.delete", {"id": 113})
        self.assert_status_code(response, 400)
        assert (
            "A used as reference projector is not allowed to delete."
            in response.data.decode()
        )
        model = self.get_model("projector/113")
        assert model.get("name") == "name_test1"
