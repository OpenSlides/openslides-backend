from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class ProjectorToggle(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_motion(1)
        self.create_poll(788)

    def create_poll(self, base: int) -> None:
        self.set_models(
            {
                f"poll/{base}": {
                    "meeting_id": 1,
                    "title": "A very important change",
                    "type": Poll.TYPE_PSEUDOANONYMOUS,
                    "backend": "fast",
                    "pollmethod": "YN",
                    "onehundred_percent_base": Poll.ONEHUNDRED_PERCENT_BASE_YN,
                    "content_object_id": "motion/1",
                }
            }
        )

    def setup_projection_33(self, stable: bool) -> None:
        self.set_models(
            {
                "projection/33": {
                    "meeting_id": 1,
                    "content_object_id": "poll/788",
                    "current_projector_id": 1,
                    "stable": stable,
                },
            }
        )

    def test_correct_remove_stable_projection(self) -> None:
        self.setup_projection_33(True)
        response = self.request(
            "projector.toggle",
            {
                "ids": [1],
                "content_object_id": "poll/788",
                "meeting_id": 1,
                "stable": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("projection/33")
        self.assert_model_exists("projector/1", {"current_projection_ids": None})

    def test_correct_remove_unstable_projection(self) -> None:
        self.setup_projection_33(False)
        response = self.request(
            "projector.toggle",
            {
                "ids": [1],
                "content_object_id": "poll/788",
                "meeting_id": 1,
                "stable": False,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("projector/1", {"history_projection_ids": [33]})

    def test_correct_add_projection(self) -> None:
        response = self.request(
            "projector.toggle",
            {
                "ids": [1],
                "content_object_id": "poll/788",
                "meeting_id": 1,
                "stable": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projection/1",
            {
                "meeting_id": 1,
                "stable": True,
                "current_projector_id": 1,
                "content_object_id": "poll/788",
            },
        )
        self.assert_model_exists("projector/1", {"current_projection_ids": [1]})

    def test_toggle_unstable_move_into_history(self) -> None:
        self.setup_projection_33(False)
        self.create_poll(888)
        response = self.request(
            "projector.toggle",
            {
                "ids": [1],
                "content_object_id": "poll/888",
                "meeting_id": 1,
                "stable": False,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "projector/1",
            {
                "current_projection_ids": [34],
                "history_projection_ids": [33],
                "scroll": 0,
            },
        )
        self.assert_model_exists(
            "projection/34",
            {
                "meeting_id": 1,
                "current_projector_id": 1,
                "content_object_id": "poll/888",
            },
        )

    def test_content_object_id_not_in_meeting_1(self) -> None:
        self.create_meeting(4)
        self.create_motion(4, 30)
        response = self.request(
            "projector.toggle",
            {
                "ids": [1],
                "content_object_id": "motion/30",
                "meeting_id": 1,
                "stable": True,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The following models do not belong to meeting 1: ['motion/30']",
            response.json["message"],
        )
        self.assert_model_exists("projector/1", {"current_projection_ids": None})
        self.assert_model_exists("motion/30", {"projection_ids": None})
        self.assert_model_not_exists("projection/1")

    def test_content_object_id_not_in_meeting_2(self) -> None:
        self.create_meeting(4)
        response = self.request(
            "projector.toggle",
            {
                "ids": [1],
                "content_object_id": "meeting/4",
                "meeting_id": 1,
                "stable": True,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The following models do not belong to meeting 1: ['meeting/4']",
            response.json["message"],
        )
        self.assert_model_exists("projector/1", {"current_projection_ids": None})
        self.assert_model_exists("meeting/4", {"projection_ids": None})
        self.assert_model_not_exists("projection/1")

    def test_toggle_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "projector.toggle",
            {"ids": [1], "content_object_id": "poll/788", "meeting_id": 1},
        )

    def test_toggle_permission(self) -> None:
        self.base_permission_test(
            {},
            "projector.toggle",
            {"ids": [1], "content_object_id": "poll/788", "meeting_id": 1},
            Permissions.Projector.CAN_MANAGE,
        )

    def test_toggle_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "projector.toggle",
            {"ids": [1], "content_object_id": "poll/788", "meeting_id": 1},
        )
