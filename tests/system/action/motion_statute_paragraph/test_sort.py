from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionStatuteParagraphSortActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion_statute_paragraph/31": {
                "meeting_id": 1,
                "title": "title_loisueb",
            },
            "motion_statute_paragraph/32": {
                "meeting_id": 1,
                "title": "title_blanumop",
            },
        }

    def test_sort_correct_1(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_statute_paragraph/31": {
                    "meeting_id": 222,
                    "title": "title_loisueb",
                },
                "motion_statute_paragraph/32": {
                    "meeting_id": 222,
                    "title": "title_blanumop",
                },
            }
        )
        response = self.request(
            "motion_statute_paragraph.sort",
            {"meeting_id": 222, "statute_paragraph_ids": [32, 31]},
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("motion_statute_paragraph/31")
        assert model_31.get("weight") == 2
        model_32 = self.get_model("motion_statute_paragraph/32")
        assert model_32.get("weight") == 1

    def test_sort_missing_model(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_statute_paragraph/31": {
                    "meeting_id": 222,
                    "title": "title_loisueb",
                },
            }
        )
        response = self.request(
            "motion_statute_paragraph.sort",
            {"meeting_id": 222, "statute_paragraph_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert (
            "motion_statute_paragraph sorting failed, because element motion_statute_paragraph/32 doesn't exist."
            in response.json["message"]
        )

    def test_sort_another_section_db(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "is_active_in_organization_id": 1,
                },
                "motion_statute_paragraph/31": {
                    "meeting_id": 222,
                    "title": "title_loisueb",
                },
                "motion_statute_paragraph/32": {
                    "meeting_id": 222,
                    "title": "title_blanumop",
                },
                "motion_statute_paragraph/33": {
                    "meeting_id": 222,
                    "title": "title_polusiem",
                },
            }
        )
        response = self.request(
            "motion_statute_paragraph.sort",
            {"meeting_id": 222, "statute_paragraph_ids": [32, 31]},
        )
        self.assert_status_code(response, 400)
        assert (
            "motion_statute_paragraph sorting failed, because some elements were not included in the call."
            in response.json["message"]
        )

    def test_sort_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_statute_paragraph.sort",
            {"meeting_id": 1, "statute_paragraph_ids": [32, 31]},
        )

    def test_sort_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "motion_statute_paragraph.sort",
            {"meeting_id": 1, "statute_paragraph_ids": [32, 31]},
            Permissions.Motion.CAN_MANAGE,
        )
