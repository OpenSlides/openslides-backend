from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCommentSectionSortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_comment_section/31": {
                "meeting_id": 1,
                "name": "name_loisueb",
            },
            "motion_comment_section/32": {
                "meeting_id": 1,
                "name": "name_blanumop",
            },
        }

    def test_sort_correct_1(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_comment_section/31": {
                    "meeting_id": 222,
                    "name": "name_loisueb",
                },
                "motion_comment_section/32": {
                    "meeting_id": 222,
                    "name": "name_blanumop",
                },
            }
        )
        response = self.request(
            "motion_comment_section.sort",
            {"meeting_id": 222, "motion_comment_section_ids": [32, 31]},
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("motion_comment_section/31")
        assert model_31.get("weight") == 2
        model_32 = self.get_model("motion_comment_section/32")
        assert model_32.get("weight") == 1

    def test_sort_missing_model(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_comment_section/31": {
                    "meeting_id": 222,
                    "name": "name_loisueb",
                },
            }
        )
        response = self.request(
            "motion_comment_section.sort",
            {"meeting_id": 222, "motion_comment_section_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert (
            "motion_comment_section sorting failed, because element motion_comment_section/32 doesn't exist."
            in response.json["message"]
        )

    def test_sort_another_section_db(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_comment_section/31": {
                    "meeting_id": 222,
                    "name": "name_loisueb",
                },
                "motion_comment_section/32": {
                    "meeting_id": 222,
                    "name": "name_blanumop",
                },
                "motion_comment_section/33": {
                    "meeting_id": 222,
                    "name": "name_polusiem",
                },
            }
        )
        response = self.request(
            "motion_comment_section.sort",
            {"meeting_id": 222, "motion_comment_section_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert (
            "motion_comment_section sorting failed, because some elements were not included in the call."
            in response.json["message"]
        )

    def test_sort_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_comment_section.sort",
            {"meeting_id": 1, "motion_comment_section_ids": [32, 31]},
        )

    def test_sort_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_comment_section.sort",
            {"meeting_id": 1, "motion_comment_section_ids": [32, 31]},
            Permissions.Motion.CAN_MANAGE,
        )
