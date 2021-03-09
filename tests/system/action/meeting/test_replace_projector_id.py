from tests.system.action.base import BaseActionTestCase


class MeetingReplaceProjectorIdTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "meeting/1": {
                    "default_projector_$_id": ["motion"],
                    "default_projector_$motion_id": 11,
                    "reference_projector_id": 20,
                },
                "projector/11": {
                    "used_as_default_$motion_in_meeting_id": 1,
                    "used_as_default_$_in_meeting_id": ["motion"],
                },
                "projector/20": {
                    "used_as_reference_projector_meeting_id": 1,
                },
            }
        )

    def test_replacing(self) -> None:
        response = self.request(
            "meeting.replace_projector_id", {"id": 1, "projector_id": 11}
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        assert meeting.get("default_projector_$_id") == ["motion"]
        assert meeting.get("default_projector_$motion_id") == 20
        assert meeting.get("reference_projector_id") == 20

        projector_11 = self.get_model("projector/11")
        assert projector_11.get("used_as_default_$motion_in_meeting_id") is None

        projector_20 = self.get_model("projector/20")
        assert projector_20.get("used_as_reference_projector_meeting_id") == 1
        assert projector_20.get("used_as_default_$motion_in_meeting_id") == 1
        assert projector_20.get("used_as_default_$_in_meeting_id") == ["motion"]

    def test_no_replacing(self) -> None:
        response = self.request(
            "meeting.replace_projector_id", {"id": 1, "projector_id": 12}
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        assert meeting.get("default_projector_$_id") == ["motion"]
        assert meeting.get("default_projector_$motion_id") == 11
        assert meeting.get("reference_projector_id") == 20

        projector_11 = self.get_model("projector/11")
        assert projector_11.get("used_as_default_$motion_in_meeting_id") == 1
        assert projector_11.get("used_as_default_$_in_meeting_id") == ["motion"]

        projector_20 = self.get_model("projector/20")
        assert projector_20.get("used_as_reference_projector_meeting_id") == 1
