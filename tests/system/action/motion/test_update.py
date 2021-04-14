from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model: Dict[str, Dict[str, Any]] = {
            "motion/111": {
                "meeting_id": 1,
                "title": "title_srtgb123",
                "number": "123",
                "text": "<i>test</i>",
                "reason": "<b>test2</b>",
                "modified_final_version": "blablabla",
                "amendment_paragraph_$": ["3"],
                "amendment_paragraph_$3": "testtesttest",
                "submitter_ids": [1],
                "state_id": 1,
            },
            "motion_submitter/1": {"meeting_id": 1, "motion_id": 111, "user_id": 1},
            "motion_state/1": {
                "meeting_id": 1,
                "motion_ids": [111],
                "allow_submitter_edit": True,
            },
        }

    def test_update_correct(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "motion/111": {
                    "meeting_id": 1,
                    "title": "title_srtgb123",
                    "number": "123",
                    "text": "<i>test</i>",
                    "reason": "<b>test2</b>",
                    "modified_final_version": "blablabla",
                    "amendment_paragraph_$": ["3"],
                    "amendment_paragraph_$3": "testtesttest",
                },
            }
        )
        response = self.request(
            "motion.update",
            {
                "id": 111,
                "title": "title_bDFsWtKL",
                "number": "124",
                "text": "text_eNPkDVuq",
                "reason": "reason_ukWqADfE",
                "modified_final_version": "mfv_ilVvBsUi",
                "amendment_paragraph_$": {3: "<html>test</html>"},
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("title") == "title_bDFsWtKL"
        assert model.get("number") == "124"
        assert model.get("text") == "text_eNPkDVuq"
        assert model.get("reason") == "reason_ukWqADfE"
        assert model.get("modified_final_version") == "mfv_ilVvBsUi"
        assert model.get("amendment_paragraph_$3") == "&lt;html&gt;test&lt;/html&gt;"
        assert model.get("amendment_paragraph_$") == ["3"]

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "motion/111": {
                    "meeting_id": 1,
                    "title": "title_srtgb123",
                    "number": "123",
                    "text": "<i>test</i>",
                    "reason": "<b>test2</b>",
                    "modified_final_version": "blablabla",
                },
            }
        )
        response = self.request("motion.update", {"id": 112, "number": "999"})
        self.assert_status_code(response, 400)
        model = self.get_model("motion/111")
        assert model.get("number") == "123"

    def test_update_text_without_previous(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "motion/111": {
                    "meeting_id": 1,
                    "title": "title_srtgb123",
                    "number": "123",
                    "reason": "<b>test2</b>",
                },
            }
        )
        response = self.request(
            "motion.update",
            {
                "id": 111,
                "title": "title_bDFsWtKL",
                "number": "124",
                "text": "text_eNPkDVuq",
                "reason": "reason_ukWqADfE",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot update text, because it was not set in the old values.",
            response.json["message"],
        )

    def test_update_amendment_paragraphs_without_previous(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "motion/111": {
                    "meeting_id": 1,
                    "title": "title_srtgb123",
                    "number": "123",
                    "modified_final_version": "blablabla",
                },
            }
        )
        response = self.request(
            "motion.update",
            {
                "id": 111,
                "title": "title_bDFsWtKL",
                "number": "124",
                "amendment_paragraph_$": {3: "<html>test</html>"},
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot update amendment_paragraph_$, because it was not set in the old values.",
            response.json["message"],
        )

    def test_update_required_reason(self) -> None:
        self.set_models(
            {
                "meeting/77": {
                    "name": "name_TZRIHsSD",
                    "motions_reason_required": True,
                },
                "motion/111": {
                    "title": "title_srtgb123",
                    "number": "123",
                    "modified_final_version": "blablabla",
                    "meeting_id": 77,
                    "reason": "balblabla",
                },
            }
        )
        response = self.request(
            "motion.update",
            {
                "id": 111,
                "title": "title_bDFsWtKL",
                "number": "124",
                "reason": "",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn("Reason is required to update.", response.json["message"])

    def test_update_correct_2(self) -> None:
        self.set_models(
            {
                "meeting/2538": {"name": "name_jkPIYjFz"},
                "motion/111": {
                    "meeting_id": 2538,
                },
                "motion_category/4": {
                    "meeting_id": 2538,
                    "name": "name_GdPzDztT",
                    "motion_ids": [],
                },
                "motion_block/51": {
                    "meeting_id": 2538,
                    "title": "title_ddyvpXch",
                    "motion_ids": [],
                },
                "motion/112": {
                    "meeting_id": 2538,
                },
            }
        )

        response = self.request(
            "motion.update",
            {
                "id": 111,
                "state_extension": "test_blablab_noon",
                "recommendation_extension": "ext_sldennt [motion/112]",
                "category_id": 4,
                "block_id": 51,
                "supporter_ids": [],
                "tag_ids": [],
                "attachment_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("state_extension") == "test_blablab_noon"
        assert model.get("recommendation_extension") == "ext_sldennt [motion/112]"
        assert model.get("category_id") == 4
        assert model.get("block_id") == 51
        assert model.get("supporter_ids") == []
        assert model.get("tag_ids") == []
        assert model.get("attachment_ids") == []
        assert model.get("recommendation_extension_reference_ids") == ["motion/112"]

    def test_update_workflow_id(self) -> None:
        self.set_models(
            {
                "meeting/2538": {"name": "name_jkPIYjFz"},
                "motion/111": {
                    "meeting_id": 2538,
                    "state_id": 88,
                    "recommendation_id": 88,
                },
                "motion_workflow/22": {"name": "name_workflow_22", "meeting_id": 2538},
                "motion_state/88": {
                    "name": "name_blaglup",
                    "meeting_id": 2538,
                    "workflow_id": 22,
                    "motion_ids": [111],
                    "motion_recommendation_ids": [111],
                },
                "motion_state/23": {
                    "name": "name_state_23",
                    "meeting_id": 2538,
                    "motion_ids": [],
                },
                "motion_workflow/35": {
                    "name": "name_workflow_35",
                    "first_state_id": 23,
                    "meeting_id": 2538,
                },
            }
        )
        response = self.request("motion.update", {"id": 111, "workflow_id": 35})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("state_id") == 23
        assert model.get("recommendation_id") is None

    def test_update_workflow_id_no_change(self) -> None:
        self.set_models(
            {
                "meeting/2538": {"name": "name_jkPIYjFz"},
                "motion/111": {
                    "meeting_id": 2538,
                    "state_id": 88,
                    "recommendation_id": 88,
                },
                "motion_workflow/22": {"name": "name_workflow_22", "meeting_id": 2538},
                "motion_state/88": {
                    "name": "name_blaglup",
                    "meeting_id": 2538,
                    "workflow_id": 22,
                    "motion_ids": [111],
                    "motion_recommendation_ids": [111],
                },
            }
        )
        response = self.request("motion.update", {"id": 111, "workflow_id": 22})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("state_id") == 88
        assert model.get("recommendation_id") == 88

    def test_update_wrong_id_2(self) -> None:
        self.create_model("motion/111")
        response = self.request(
            "motion.update_metadata", {"id": 112, "state_extension": "ext_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion/111")
        assert model.get("state_extension") is None

    def test_update_metadata_missing_motion(self) -> None:
        self.set_models(
            {
                "meeting/2538": {"name": "name_jkPIYjFz"},
                "motion/111": {"meeting_id": 2538},
                "motion_category/4": {"name": "name_GdPzDztT", "meeting_id": 2538},
                "motion_block/51": {"title": "title_ddyvpXch", "meeting_id": 2538},
            }
        )

        response = self.request(
            "motion.update",
            {
                "id": 111,
                "state_extension": "test_blablab_noon",
                "recommendation_extension": "ext_sldennt [motion/112]",
                "category_id": 4,
                "block_id": 51,
                "supporter_ids": [],
                "tag_ids": [],
                "attachment_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("recommendation_extension_reference_ids") == []

    def test_meeting_missmatch(self) -> None:
        self.set_models(
            {
                "meeting/1": {"name": "name_GDZvcjPK"},
                "meeting/2": {"name": "name_Rwvrqaqj"},
                "motion/1": {"meeting_id": 1},
                "motion/2": {"meeting_id": 2},
            }
        )
        response = self.request(
            "motion.update",
            {
                "id": 1,
                "recommendation_extension": "blablabla [motion/2] blablabla",
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "The following models do not belong to meeting 1: ['motion/2']"
            in response.json.get("message", "")
        )

    def test_only_motion_allowed(self) -> None:
        self.set_models(
            {"meeting/1": {"name": "name_uZXBoHMp"}, "motion/1": {"meeting_id": 1}}
        )
        response = self.request(
            "motion.update",
            {
                "id": 1,
                "recommendation_extension": "blablabla [assignment/1] blablabla",
            },
        )
        self.assert_status_code(response, 400)
        assert "Found assignment/1 but only motion is allowed." in response.json.get(
            "message", ""
        )

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "motion.update",
            {
                "id": 111,
                "title": "title_bDFsWtKL",
                "text": "text_eNPkDVuq",
                "reason": "reason_ukWqADfE",
            },
        )

    def test_update_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "motion.update",
            {
                "id": 111,
                "title": "title_bDFsWtKL",
                "text": "text_eNPkDVuq",
                "reason": "reason_ukWqADfE",
            },
            Permissions.Motion.CAN_MANAGE,
        )

    def test_update_permission_metadata_no_wl(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.set_models(self.permission_test_model)
        response = self.request(
            "motion.update",
            {
                "id": 111,
                "title": "title_bDFsWtKL",
                "text": "text_eNPkDVuq",
                "reason": "reason_ukWqADfE",
            },
        )
        self.assert_status_code(response, 403)
        assert "Forbidden fields:" in response.json["message"]

    def test_update_permission_metadata_and_wl(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        self.set_models(self.permission_test_model)
        self.set_models({"motion_category/2": {"meeting_id": 1}})
        response = self.request(
            "motion.update",
            {
                "id": 111,
                "category_id": 2,
            },
        )
        self.assert_status_code(response, 200)

    def test_update_permission_submitter_and_wl(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.permission_test_model["motion_submitter/1"]["user_id"] = self.user_id
        self.set_models(self.permission_test_model)
        response = self.request(
            "motion.update",
            {
                "id": 111,
                "title": "title_bDFsWtKL",
                "text": "text_eNPkDVuq",
                "reason": "reason_ukWqADfE",
            },
        )
        self.assert_status_code(response, 200)
