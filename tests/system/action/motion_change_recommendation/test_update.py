from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionChangeRecommendationActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/25": {
                "title": "title_pheK0Ja3ai",
                "meeting_id": 1,
            },
            "motion_change_recommendation/111": {
                "line_from": 11,
                "line_to": 23,
                "text": "text_LhmrbbwS",
                "motion_id": 25,
                "meeting_id": 1,
            },
        }

    def test_update_correct(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "motion/25": {
                    "title": "title_pheK0Ja3ai",
                    "meeting_id": 1,
                },
                "motion_change_recommendation/111": {
                    "line_from": 11,
                    "line_to": 23,
                    "text": "text_LhmrbbwS",
                    "motion_id": 25,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_change_recommendation.update",
            {
                "id": 111,
                "text": "text_zzTWoMte",
                "rejected": False,
                "internal": True,
                "type": "insertion",
                "other_description": "other_description_IClpabuM",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_change_recommendation/111")
        assert model.get("text") == "text_zzTWoMte"
        assert model.get("rejected") is False
        assert model.get("internal") is True
        assert model.get("type") == "insertion"
        assert model.get("other_description") == "other_description_IClpabuM"
        self.assert_history_information(
            "motion/25", ["Motion change recommendation updated"]
        )

    def test_update_wrong_id(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "motion/25": {
                    "title": "title_pheK0Ja3ai",
                    "meeting_id": 1,
                },
                "motion_change_recommendation/111": {
                    "line_from": 11,
                    "line_to": 23,
                    "text": "text_LhmrbbwS",
                    "motion_id": 25,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request(
            "motion_change_recommendation.update", {"id": 112, "text": "text_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_change_recommendation/111")
        assert model.get("text") == "text_LhmrbbwS"
        assert model.get("line_from") == 11
        assert model.get("line_to") == 23
        assert model.get("motion_id") == 25

    def test_update_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_change_recommendation.update",
            {
                "id": 111,
                "text": "text_zzTWoMte",
            },
        )

    def test_update_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_change_recommendation.update",
            {
                "id": 111,
                "text": "text_zzTWoMte",
            },
            Permissions.Motion.CAN_MANAGE,
        )

    def test_update_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            self.permission_test_models,
            "motion_change_recommendation.update",
            {
                "id": 111,
                "text": "text_zzTWoMte",
            },
        )

    def create_motions_with_line_changes(self, amount: int = 1) -> None:
        self.create_meeting()
        self.set_models(
            {
                **{
                    f"motion/{id_}": {
                        "title": f"Motion {id_}",
                        "meeting_id": 1,
                        "change_recommendation_ids": list(
                            range((id_ - 1) * 3 + 1, (id_ - 1) * 3 + 4)
                        ),
                    }
                    for id_ in range(1, 1 + amount)
                },
                **{
                    f"motion_change_recommendation/{id_ + (motion_id-1)*3}": {
                        "meeting_id": 1,
                        "motion_id": motion_id,
                        "line_from": linespan[0],
                        "line_to": linespan[1],
                        "text": f"Reco {id_}",
                    }
                    for motion_id in range(1, 1 + amount)
                    for id_, linespan in {1: (1, 2), 2: (4, 6), 3: (8, 10)}.items()
                },
            }
        )

    def test_update_with_line_changes(self) -> None:
        self.create_motions_with_line_changes()

        response = self.request_multi(
            "motion_change_recommendation.update",
            [
                {"id": 1, "line_to": 5},
                {"id": 2, "line_from": 6, "line_to": 7},
                {"id": 3, "line_from": 11, "line_to": 33},
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_change_recommendation/1",
            {
                "line_from": 1,
                "line_to": 5,
            },
        )
        self.assert_model_exists(
            "motion_change_recommendation/2",
            {
                "line_from": 6,
                "line_to": 7,
            },
        )
        self.assert_model_exists(
            "motion_change_recommendation/3",
            {
                "line_from": 11,
                "line_to": 33,
            },
        )

    def test_update_with_line_changes_multi_motion(self) -> None:
        self.create_motions_with_line_changes(amount=2)

        response = self.request_multi(
            "motion_change_recommendation.update",
            [
                {"id": 1, "line_to": 5},
                {"id": 2, "line_from": 6, "line_to": 7},
                {"id": 3, "line_from": 11, "line_to": 33},
                {"id": 6, "line_to": 22},
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion_change_recommendation/1",
            {
                "line_from": 1,
                "line_to": 5,
            },
        )
        self.assert_model_exists(
            "motion_change_recommendation/2",
            {
                "line_from": 6,
                "line_to": 7,
            },
        )
        self.assert_model_exists(
            "motion_change_recommendation/3",
            {
                "line_from": 11,
                "line_to": 33,
            },
        )
        self.assert_model_exists(
            "motion_change_recommendation/6",
            {
                "line_from": 8,
                "line_to": 22,
            },
        )

    def test_update_with_line_changes_stretch_forward_error(self) -> None:
        self.create_motions_with_line_changes()

        response = self.request(
            "motion_change_recommendation.update", {"id": 2, "line_to": 9}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot edit motion_change_recommendation: New line spans cause intersections concerning recommendations {2, 3}.",
            response.json["message"],
        )

    def test_update_with_line_changes_stretch_backward_error(self) -> None:
        self.create_motions_with_line_changes()

        response = self.request(
            "motion_change_recommendation.update", {"id": 2, "line_from": 2}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot edit motion_change_recommendation: New line spans cause intersections concerning recommendations {1, 2}.",
            response.json["message"],
        )

    def test_update_with_line_changes_engulf_error(self) -> None:
        self.create_motions_with_line_changes()

        response = self.request(
            "motion_change_recommendation.update",
            {"id": 2, "line_from": 7, "line_to": 12},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot edit motion_change_recommendation: New line spans cause intersections concerning recommendations {2, 3}.",
            response.json["message"],
        )

    def test_update_with_line_changes_engulfed_error(self) -> None:
        self.create_motions_with_line_changes()

        response = self.request(
            "motion_change_recommendation.update",
            {"id": 2, "line_from": 9, "line_to": 9},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot edit motion_change_recommendation: New line spans cause intersections concerning recommendations {2, 3}.",
            response.json["message"],
        )

    def test_update_with_line_changes_crossover_only_on_edge_error(self) -> None:
        self.create_motions_with_line_changes()

        response = self.request(
            "motion_change_recommendation.update", {"id": 2, "line_to": 8}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot edit motion_change_recommendation: New line spans cause intersections concerning recommendations {2, 3}.",
            response.json["message"],
        )

    def test_update_with_line_changes_inverted_span_error(self) -> None:
        self.create_motions_with_line_changes()

        response = self.request(
            "motion_change_recommendation.update",
            {"id": 2, "line_from": 6, "line_to": 4},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot edit motion_change_recommendation/2: New line span would have its from line after its to line.",
            response.json["message"],
        )

    def test_update_with_line_changes_implied_inverted_span_error(self) -> None:
        self.create_motions_with_line_changes()

        response = self.request(
            "motion_change_recommendation.update", {"id": 2, "line_to": 3}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot edit motion_change_recommendation/2: New line span would have its from line after its to line.",
            response.json["message"],
        )
