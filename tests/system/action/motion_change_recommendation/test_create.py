from datetime import datetime
from zoneinfo import ZoneInfo

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase
from tests.util import Response


class MotionChangeRecommendationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "motion/233": {
                    "title": "motion 233",
                    "meeting_id": 1,
                    "state_id": 1,
                    "sequential_number": 233,
                },
            }
        )

    def test_create_good_required_fields(self) -> None:
        now = datetime.now(ZoneInfo("UTC"))
        response = self.request(
            "motion_change_recommendation.create",
            {
                "line_from": 125,
                "line_to": 234,
                "text": "text_DvLXGcdW",
                "motion_id": 233,
            },
        )
        self.assert_status_code(response, 200)
        model = self.assert_model_exists(
            "motion_change_recommendation/1",
            {
                "line_from": 125,
                "line_to": 234,
                "text": "text_DvLXGcdW",
                "motion_id": 233,
                "type": "replacement",
                "meeting_id": 1,
            },
        )
        assert (
            model.get("creation_time", datetime.fromtimestamp(0, ZoneInfo("UTC")))
            >= now
        )
        self.assert_history_information(
            "motion/233", ["Motion change recommendation created"]
        )

    def test_create_good_all_fields(self) -> None:
        now = datetime.now(ZoneInfo("UTC"))
        response = self.request(
            "motion_change_recommendation.create",
            {
                "line_from": 125,
                "line_to": 234,
                "text": "text_DvLXGcdW",
                "motion_id": 233,
                "rejected": False,
                "internal": True,
                "type": "replacement",
                "other_description": "other_description_iuDguxZp",
            },
        )
        self.assert_status_code(response, 200)
        model = self.assert_model_exists(
            "motion_change_recommendation/1",
            {
                "line_from": 125,
                "line_to": 234,
                "text": "text_DvLXGcdW",
                "motion_id": 233,
                "rejected": False,
                "internal": True,
                "type": "replacement",
                "other_description": "other_description_iuDguxZp",
                "meeting_id": 1,
            },
        )
        assert (
            model.get("creation_time", datetime.fromtimestamp(0, ZoneInfo("UTC"))) > now
        )

    def test_create_empty_data(self) -> None:
        response = self.request("motion_change_recommendation.create", {})
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion_change_recommendation.create: data must contain ['line_from', 'line_to', 'motion_id', 'text'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "motion_change_recommendation.create",
            {
                "line_from": 125,
                "line_to": 234,
                "text": "text_DvLXGcdW",
                "motion_id": 233,
                "wrong_field": "text_AefohteiF8",
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Action motion_change_recommendation.create: data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_no_permission(self) -> None:
        self.base_permission_test(
            {},
            "motion_change_recommendation.create",
            {
                "line_from": 125,
                "line_to": 234,
                "text": "text_DvLXGcdW",
                "motion_id": 233,
            },
        )

    def test_create_permission(self) -> None:
        self.base_permission_test(
            {},
            "motion_change_recommendation.create",
            {
                "line_from": 125,
                "line_to": 234,
                "text": "text_DvLXGcdW",
                "motion_id": 233,
            },
            Permissions.Motion.CAN_MANAGE,
        )

    def test_create_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "motion_change_recommendation.create",
            {
                "line_from": 125,
                "line_to": 234,
                "text": "text_DvLXGcdW",
                "motion_id": 233,
            },
        )


class MotionChangeRecommendationLineValidationTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.crid = 0
        self.create_meeting()
        self.set_models(
            {
                "motion/233": {
                    "title": "motion 233",
                    "meeting_id": 1,
                    "state_id": 1,
                    "sequential_number": 233,
                },
            }
        )

    def create_change_recommendation(
        self, line_from: int, line_to: int, motion_id: int = 233
    ) -> None:
        self.crid += 1
        self.create_model(
            f"motion_change_recommendation/{self.crid}",
            {
                "meeting_id": 1,
                "motion_id": motion_id,
                "line_from": line_from,
                "line_to": line_to,
            },
        )

    def cr_request(self, line_from: int, line_to: int) -> Response:
        return self.request(
            "motion_change_recommendation.create",
            {
                "line_from": line_from,
                "line_to": line_to,
                "text": "text",
                "motion_id": 233,
            },
        )

    def test_create_title_change_recommendation(self) -> None:
        response = self.cr_request(0, 0)
        self.assert_status_code(response, 200)

    def test_create_change_recommendation_to_lt_from(self) -> None:
        response = self.cr_request(42, 24)
        self.assert_status_code(response, 400)
        self.assertEqual(
            "Starting line must be smaller than ending line.", response.json["message"]
        )

    def test_create_change_recommendation_other_not_colliding(self) -> None:
        self.create_change_recommendation(1, 5)
        self.create_change_recommendation(10, 15)
        response = self.cr_request(6, 9)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_change_recommendation/3",
            {
                "line_from": 6,
                "line_to": 9,
                "text": "text",
                "motion_id": 233,
            },
        )

    def test_create_change_recommendation_other_colliding(self) -> None:
        self.create_change_recommendation(1, 5)
        response = self.cr_request(1, 5)
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The recommendation collides with an existing one (line 1 - 5).",
            response.json["message"],
        )

    def test_create_change_recommendation_partial_overlap_1(self) -> None:
        self.create_change_recommendation(1, 5)
        response = self.cr_request(4, 10)
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The recommendation collides with an existing one (line 4 - 10).",
            response.json["message"],
        )

    def test_create_change_recommendation_partial_overlap_2(self) -> None:
        self.create_change_recommendation(5, 10)
        response = self.cr_request(1, 6)
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The recommendation collides with an existing one (line 1 - 6).",
            response.json["message"],
        )

    def test_create_change_recommendation_min_overlap_1(self) -> None:
        self.create_change_recommendation(1, 5)
        response = self.cr_request(5, 10)
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The recommendation collides with an existing one (line 5 - 10).",
            response.json["message"],
        )

    def test_create_change_recommendation_min_overlap_2(self) -> None:
        self.create_change_recommendation(5, 10)
        response = self.cr_request(1, 5)
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The recommendation collides with an existing one (line 1 - 5).",
            response.json["message"],
        )

    def test_create_change_recommendation_other_motion_not_colliding(self) -> None:
        self.create_motion(1, 42)
        self.create_change_recommendation(1, 5, motion_id=42)
        response = self.cr_request(1, 5)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_change_recommendation/2",
            {
                "line_from": 1,
                "line_to": 5,
                "text": "text",
                "motion_id": 233,
            },
        )
