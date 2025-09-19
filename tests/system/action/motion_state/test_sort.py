from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionStateSort(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "motion_state/2": {
                    "name": "state 2",
                    "workflow_id": 1,
                    "meeting_id": 1,
                    "weight": 2,
                },
                "motion_state/3": {
                    "name": "state 3",
                    "workflow_id": 1,
                    "meeting_id": 1,
                    "weight": 3,
                },
            }
        )

    def test_sort_good(self) -> None:
        response = self.request(
            "motion_state.sort",
            {"workflow_id": 1, "motion_state_ids": [3, 2, 1]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_state/1", {"weight": 3})
        self.assert_model_exists("motion_state/2", {"weight": 2})
        self.assert_model_exists("motion_state/3", {"weight": 1})

    def test_sort_extra_id_in_payload(self) -> None:
        response = self.request(
            "motion_state.sort",
            {"workflow_id": 1, "motion_state_ids": [3, 2, 4, 1]},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "motion_state sorting failed, because element motion_state/4 doesn't exist.",
            response.json["message"],
        )

    def test_sort_missing_id_in_payload(self) -> None:
        response = self.request(
            "motion_state.sort",
            {"workflow_id": 1, "motion_state_ids": [3, 1]},
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "motion_state sorting failed, because some elements were not included in the call.",
            response.json["message"],
        )

    def test_sort_no_permissions(self) -> None:
        self.base_permission_test(
            {}, "motion_state.sort", {"workflow_id": 1, "motion_state_ids": [3, 2, 1]}
        )

    def test_sort_permissions(self) -> None:
        self.base_permission_test(
            {},
            "motion_state.sort",
            {"workflow_id": 1, "motion_state_ids": [3, 2, 1]},
            Permissions.Motion.CAN_MANAGE,
        )

    def test_sort_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {}, "motion_state.sort", {"workflow_id": 1, "motion_state_ids": [3, 2, 1]}
        )
