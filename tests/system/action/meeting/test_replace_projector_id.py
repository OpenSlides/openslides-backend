from tests.system.action.base import BaseActionTestCase


class MeetingReplaceProjectorIdTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"reference_projector_id": 20},
                "projector/1": {
                    "used_as_default_projector_for_motion_in_meeting_id": 1
                },
                "projector/20": {"meeting_id": 1, "sequential_number": 20},
            }
        )

    def test_replacing(self) -> None:
        response = self.request(
            "meeting.replace_projector_id", {"id": 1, "projector_id": 1}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1",
            {"default_projector_motion_ids": [20], "reference_projector_id": 20},
        )
        self.assert_model_exists(
            "projector/1", {"used_as_default_projector_for_motion_in_meeting_id": None}
        )

        self.assert_model_exists(
            "projector/20",
            {
                "used_as_reference_projector_meeting_id": 1,
                "used_as_default_projector_for_motion_in_meeting_id": 1,
            },
        )

    def test_no_replacing(self) -> None:
        response = self.request(
            "meeting.replace_projector_id", {"id": 1, "projector_id": 12}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1",
            {"default_projector_motion_ids": [1], "reference_projector_id": 20},
        )
        self.assert_model_exists(
            "projector/1", {"used_as_default_projector_for_motion_in_meeting_id": 1}
        )
        self.assert_model_exists(
            "projector/20", {"used_as_reference_projector_meeting_id": 1}
        )
