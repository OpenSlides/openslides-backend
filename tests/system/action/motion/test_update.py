from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb
from pytest import raises

from openslides_backend.action.actions.motion.mixins import TextHashMixin
from openslides_backend.permissions.permissions import Permission, Permissions
from openslides_backend.shared.exceptions import ActionException
from tests.system.action.base import BaseActionTestCase
from tests.system.util import CountDatastoreCalls


class MotionUpdateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.test_models: dict[str, dict[str, Any]] = {
            # "committee/1": {"meeting_ids": [1]},
            # "meeting/1": {
            #     "meeting_user_ids": [1],
            #     "is_active_in_organization_id": 1,
            #     "committee_id": 1,
            # },
            "motion/111": {
                # "meeting_id": 1,
                "title": "title_srtgb123",
                "number": "123",
                "text": "<i>test</i>",
                "reason": "<b>test2</b>",
                "modified_final_version": "blablabla",
                "amendment_paragraphs": Jsonb({"3": "testtesttest"}),
                # "submitter_ids": [1],
                # "state_id": 1,
            },
            # "user/1": {"meeting_user_ids": [1]},
            "motion_state/111": {
                # "meeting_id": 1,
                # "motion_ids": [111],
                "allow_submitter_edit": True,
            },
        }
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "motion/111": {
                "title": "title_srtgb123",
                "sequential_number": 111,
                "meeting_id": 1,
                "state_id": 1,
                "number": "123",
                "text": "<i>test</i>",
                "reason": "<b>test2</b>",
                "modified_final_version": "blablabla",
                "amendment_paragraphs": Jsonb({"3": "testtesttest"}),
            },
            "meeting_user/1": {
                "meeting_id": 1,
                "user_id": 1,
                "motion_submitter_ids": [1],
            },
            "motion_submitter/1": {
                "meeting_id": 1,
                "motion_id": 111,
                "meeting_user_id": 1,
            },
            "motion_state/1": {
                "allow_submitter_edit": True,
            },
        }
        self.permission_test_models["motion/111"].update(
            {"meeting_id": 1, "state_id": 1, "sequential_number": 111}
        )

    def set_test_models(self) -> None:
        # self.set_user_groups(1, [1])
        self.create_motion(1, 111)
        self.set_models(self.test_models)

    def base_motion_update_permission_test_internally(
        self,
        action_data: dict[str, Any],
        permission: Permission | None = None,
    ) -> None:
        self.create_motion(1, 111)
        self.set_organization_management_level(None)
        self.set_user_groups(1, [3])
        if permission:
            self.set_group_permissions(3, [permission])
        self.set_models(self.permission_test_models)
        self.execute_action_internally("motion.update", action_data)

    def test_update_correct(self) -> None:
        self.set_test_models()
        self.set_models(
            {
                # "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
                "motion/111": {
                    # "meeting_id": 1,
                    # "title": "title_srtgb123",
                    # "number": "123",
                    # "text": "<i>test</i>",
                    # "reason": "<b>test2</b>",
                    # "modified_final_version": "blablabla",
                    # "amendment_paragraphs": Jsonb({"3": "testtesttest"}),
                    "created": datetime.fromtimestamp(1687339000),
                },
            }
        )
        with CountDatastoreCalls() as counter:
            self.execute_action_internally(
                "motion.update",
                {
                    "id": 111,
                    "title": "title_bDFsWtKL",
                    "number": "124",
                    "text": "text_eNPkDVuq",
                    "reason": "reason_ukWqADfE",
                    "modified_final_version": "mfv_ilVvBsUi",
                    "amendment_paragraphs": {
                        "3": "<html>test</html>",
                        "4": "</><</>broken>",
                    },
                    "start_line_number": 13,
                    "additional_submitter": "test",
                    "workflow_timestamp": datetime.fromtimestamp(1234567890),
                },
            )
        # self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("title") == "title_bDFsWtKL"
        assert model.get("number") == "124"
        assert model.get("text") == "text_eNPkDVuq"
        assert model.get("reason") == "reason_ukWqADfE"
        assert model.get("modified_final_version") == "mfv_ilVvBsUi"
        assert model.get("amendment_paragraphs") == {
            "3": "&lt;html&gt;test&lt;/html&gt;",
            "4": "&lt;broken&gt;",
        }
        assert model.get("start_line_number") == 13
        assert model.get("created") == datetime.fromtimestamp(
            1687339000, ZoneInfo("UTC")
        )
        assert model.get("additional_submitter") == "test"
        assert model.get("workflow_timestamp") == datetime.fromtimestamp(
            1234567890, ZoneInfo("UTC")
        )
        self.assert_history_information(
            "motion/111",
            ["Workflow_timestamp set to {}", "1234567890", "Motion updated"],
        )
        assert counter.calls == 4

    def test_update_wrong_id(self) -> None:
        self.set_test_models()
        # self.set_models(
        #     {
        #         "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
        #         "motion/111": {
        #             "meeting_id": 1,
        #             "title": "title_srtgb123",
        #             "number": "123",
        #             "text": "<i>test</i>",
        #             "reason": "<b>test2</b>",
        #             "modified_final_version": "blablabla",
        #         },
        #     }
        # )
        response = self.request("motion.update", {"id": 112, "number": "999"})
        self.assert_status_code(response, 400)
        model = self.get_model("motion/111")
        assert model.get("number") == "123"

    def test_update_text_without_previous(self) -> None:
        self.create_motion(1, 111)
        self.set_models(
            {
                # "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
                "motion/111": {
                    # "meeting_id": 1,
                    # "title": "title_srtgb123",
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
        self.assertEqual(
            "Cannot update text, because it was not set in the old values.",
            response.json["message"],
        )

    def test_update_amendment_paragraphs_without_previous(self) -> None:
        self.create_motion(1, 111)
        self.set_models(
            {
                # "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
                "motion/111": {
                    # "meeting_id": 1,
                    # "title": "title_srtgb123",
                    "number": "123",
                    "modified_final_version": "blablabla",
                },
            }
        )
        with raises(ActionException) as e_info:
            self.execute_action_internally(
                "motion.update",
                {
                    "id": 111,
                    "title": "title_bDFsWtKL",
                    "number": "124",
                    "amendment_paragraphs": {"3": "<html>test</html>"},
                },
            )
        assert (
            e_info.value.message
            == "Cannot update amendment_paragraphs, because it was not set in the old values."
        )

    def test_update_required_reason(self) -> None:
        self.create_motion(1, 111)
        self.set_models(
            {
                "meeting/1": {
                    # "name": "name_TZRIHsSD",
                    "motions_reason_required": True,
                    # "is_active_in_organization_id": 1,
                    # "committee_id": 1,
                },
                "motion/111": {
                    "title": "title_srtgb123",
                    "number": "123",
                    "modified_final_version": "blablabla",
                    # "meeting_id": 77,
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
        self.assertEqual("Reason is required to update.", response.json["message"])

    def test_update_correct_2(self) -> None:
        self.create_motion(1, 111)
        self.create_motion(1, 112)
        self.set_models(
            {
                # "meeting/2538": {
                #     "name": "name_jkPIYjFz",
                #     "is_active_in_organization_id": 1,
                #     "committee_id": 1,
                # },
                # "motion/111": {
                #     "meeting_id": 2538,
                # },
                "motion_category/4": {
                    "name": "name_GdPzDztT",
                    "meeting_id": 1,
                    "sequential_number": 4,
                    # "motion_ids": [],
                },
                "motion_block/51": {
                    "title": "title_ddyvpXch",
                    "meeting_id": 1,
                    "sequential_number": 51,
                    "list_of_speakers_id": 1,
                    # "motion_ids": [],
                },
                # "motion/112": {
                #     "meeting_id": 2538,
                # },
            }
        )

        with CountDatastoreCalls() as counter:
            self.execute_action_internally(
                "motion.update",
                {
                    "id": 111,
                    "state_extension": "ext [motion/112] [motion/113]",
                    "recommendation_extension": "ext [motion/112] [motion/113]",
                    "category_id": 4,
                    "block_id": 51,
                    "supporter_meeting_user_ids": [],
                    "additional_submitter": "additional",
                    "tag_ids": [],
                    "attachment_mediafile_ids": [],
                    "workflow_timestamp": datetime.fromtimestamp(9876543210),
                },
            )
        # self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("state_extension") == "ext [motion/112] [motion/113]"
        assert model.get("recommendation_extension") == "ext [motion/112] [motion/113]"
        assert model.get("category_id") == 4
        assert model.get("block_id") == 51
        assert model.get("supporter_meeting_user_ids") is None
        assert model.get("additional_submitter") == "additional"
        assert model.get("tag_ids") is None
        assert model.get("attachment_meeting_mediafile_ids") is None
        # motion/113 does not exist and should therefore not be present in the relations
        assert model.get("state_extension_reference_ids") == ["motion/112"]
        assert model.get("recommendation_extension_reference_ids") == ["motion/112"]
        assert model.get("workflow_timestamp") == datetime.fromtimestamp(
            9876543210, ZoneInfo("UTC")
        )
        self.assert_history_information(
            "motion/111",
            [
                "Supporters changed",
                "Workflow_timestamp set to {}",
                "9876543210",
                "Category set to {}",
                "motion_category/4",
                "Motion block set to {}",
                "motion_block/51",
                "Motion updated",
            ],
        )
        assert counter.calls == 15

    def test_update_workflow_id(self) -> None:
        self.create_motion(1, 111)
        self.set_models(
            {
                # "meeting/2538": {
                #     "name": "name_jkPIYjFz",
                #     "is_active_in_organization_id": 1,
                #     "committee_id": 1,
                # },
                "motion/111": {
                    # "meeting_id": 2538,
                    # "state_id": 88,
                    "recommendation_id": 111,
                    "created": datetime.now() - timedelta(minutes=1),
                    # "created": int(time()) - 1,
                },
                # "motion_workflow/22": {"name": "name_workflow_22", "meeting_id": 2538},
                # "motion_state/88": {
                #     # "name": "name_blaglup",
                #     # "meeting_id": 2538,
                #     # "workflow_id": 22,
                #     # "motion_ids": [111],
                #     # "motion_recommendation_ids": [111],
                # },
                "motion_state/1": {
                    # "name": "name_state_23",
                    # "meeting_id": 2538,
                    # "motion_ids": [],
                    "set_workflow_timestamp": True,
                },
                # "motion_workflow/1": {
                #     # "name": "name_workflow_35",
                #     "first_state_id": 1,
                #     # "meeting_id": 2538,
                # },
            }
        )
        response = self.request("motion.update", {"id": 111, "workflow_id": 1})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model["state_id"] == 1
        assert model.get("recommendation_id") is None
        assert model["created"] < model["workflow_timestamp"]
        self.assert_history_information_contains(
            "motion/111", "Workflow_timestamp set to {}"
        )

    def test_update_workflow_timestamp_subsequent(self) -> None:
        self.create_motion(1, 111)
        self.set_models(
            {
                # "meeting/2538": {
                #     "name": "name_jkPIYjFz",
                #     "is_active_in_organization_id": 1,
                #     "committee_id": 1,
                # },
                "motion/111": {
                    # "meeting_id": 2538,
                    # "state_id": 88,
                    "recommendation_id": 111,
                    "created": datetime.now() - timedelta(minutes=1),
                },
                # "motion_workflow/22": {"name": "name_workflow_22", "meeting_id": 2538},
                # "motion_state/88": {
                #     "name": "name_blaglup",
                #     "meeting_id": 2538,
                #     "workflow_id": 22,
                #     "motion_ids": [111],
                #     "motion_recommendation_ids": [111],
                # },
                "motion_state/1": {
                    # "name": "name_state_23",
                    # "meeting_id": 2538,
                    # "motion_ids": [],
                    "set_workflow_timestamp": True,
                },
                # "motion_workflow/35": {
                #     "name": "name_workflow_35",
                #     "first_state_id": 23,
                #     "meeting_id": 2538,
                # },
            }
        )
        self.execute_action_internally(
            "motion.update",
            {
                "id": 111,
                "title": "!",
                "workflow_timestamp": datetime.fromtimestamp(0),
            },
        )
        # self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model["workflow_timestamp"] == datetime.fromtimestamp(0, ZoneInfo("UTC"))
        response = self.request("motion.update", {"id": 111, "workflow_id": 1})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model["state_id"] == 1
        assert model.get("recommendation_id") is None
        assert model["created"] < model["workflow_timestamp"]
        self.assert_history_information_contains(
            "motion/111", "Workflow_timestamp set to {}"
        )

    def test_update_workflow_id_no_change(self) -> None:
        self.create_motion(1, 111)
        self.set_models(
            {
                # "meeting/2538": {
                #     "name": "name_jkPIYjFz",
                #     "is_active_in_organization_id": 1,
                #     "committee_id": 1,
                # },
                "motion/111": {
                    # "meeting_id": 2538,
                    # "state_id": 88,
                    "recommendation_id": 111,
                },
                # "motion_workflow/22": {"name": "name_workflow_22", "meeting_id": 2538},
                "motion_state/111": {
                    # "name": "name_blaglup",
                    # "meeting_id": 2538,
                    # "workflow_id": 22,
                    "motion_ids": [111],
                    "motion_recommendation_ids": [111],
                    "set_workflow_timestamp": True,
                },
            }
        )
        response = self.request("motion.update", {"id": 111, "workflow_id": 111})
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("state_id") == 111
        assert model.get("recommendation_id") == 111
        assert not model.get("workflow_timestamp")

    def test_update_wrong_id_2(self) -> None:
        self.create_motion(1, 111)
        # self.create_model("motion/111")
        response = self.request(
            "motion.update_metadata", {"id": 112, "state_extension": "ext_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion/111")
        assert model.get("state_extension") is None

    def test_update_metadata_missing_motion(self) -> None:
        self.create_motion(1, 111)
        self.set_models(
            {
                # "meeting/2538": {
                #     "name": "name_jkPIYjFz",
                #     "is_active_in_organization_id": 1,
                #     "committee_id": 1,
                # },
                # "motion/111": {"meeting_id": 2538},
                "motion_category/4": {
                    "name": "name_GdPzDztT",
                    "meeting_id": 1,
                    "sequential_number": 4,
                },
                "motion_block/51": {
                    "title": "title_ddyvpXch",
                    "meeting_id": 1,
                    "sequential_number": 51,
                    "list_of_speakers_id": 1,
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
                "supporter_meeting_user_ids": [],
                "tag_ids": [],
                "attachment_mediafile_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/111")
        assert model.get("recommendation_extension_reference_ids") is None

    def test_meeting_mismatch(self) -> None:
        self.create_meeting(4)
        self.create_motion(1, 1)
        self.create_motion(4, 2)
        # self.set_models(
        #     {
        #         "meeting/1": {
        #             "name": "name_GDZvcjPK",
        #             "is_active_in_organization_id": 1,
        #             "committee_id": 1,
        #         },
        #         "meeting/2": {
        #             "name": "name_Rwvrqaqj",
        #             "is_active_in_organization_id": 1,
        #             "committee_id": 1,
        #         },
        #         "motion/1": {"meeting_id": 1},
        #         "motion/2": {"meeting_id": 2},
        #     }
        # )
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
        self.create_motion(1, 1)
        # self.set_models(
        #     {
        #         "meeting/1": {
        #             "is_active_in_organization_id": 1,
        #             "committee_id": 1,
        #         },
        #         "motion/1": {"meeting_id": 1},
        #     }
        # )
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

    def test_only_motion_allowed_2(self) -> None:
        self.create_motion(1, 1)
        # self.set_models(
        #     {
        #         "meeting/1": {
        #             "is_active_in_organization_id": 1,
        #             "committee_id": 1,
        #         },
        #         "motion/1": {"meeting_id": 1},
        #     }
        # )
        response = self.request(
            "motion.update",
            {
                "id": 1,
                "state_extension": "blablabla [assignment/1] blablabla",
            },
        )
        self.assert_status_code(response, 400)
        assert "Found assignment/1 but only motion is allowed." in response.json.get(
            "message", ""
        )

    def test_reset_recommendation_extension(self) -> None:
        self.create_motion(1, 1)
        self.create_motion(1, 2)
        # self.set_models(
        #     {
        #         "meeting/1": {
        #             "is_active_in_organization_id": 1,
        #             "committee_id": 1,
        #         },
        #         "motion/1": {"meeting_id": 1},
        #         "motion/2": {"meeting_id": 1},
        #     }
        # )
        response = self.request(
            "motion.update",
            {
                "id": 1,
                "recommendation_extension": "[motion/2]",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1", {"recommendation_extension_reference_ids": ["motion/2"]}
        )
        self.assert_model_exists(
            "motion/2", {"referenced_in_motion_recommendation_extension_ids": [1]}
        )
        response = self.request(
            "motion.update",
            {
                "id": 1,
                "recommendation_extension": "",
            },
        )
        self.assert_model_exists(
            "motion/1", {"recommendation_extension_reference_ids": None}
        )
        self.assert_model_exists(
            "motion/2", {"referenced_in_motion_recommendation_extension_ids": None}
        )

    def test_set_supporter_other_meeting(self) -> None:
        self.set_test_models()
        self.create_meeting(4)
        self.set_user_groups(1, [4])
        # self.permission_test_models["meeting_user/1"]["meeting_id"] = 2
        self.set_test_models()
        response = self.request(
            "motion.update",
            {
                "id": 111,
                "supporter_meeting_user_ids": [1],
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "The following models do not belong to meeting 1: ['meeting_user/1']",
            response.json["message"],
        )

    def test_update_identical_motions(self) -> None:
        text1 = "test1"
        hash1 = TextHashMixin.get_hash(text1)
        text2 = "test2"
        hash2 = TextHashMixin.get_hash(text2)
        self.create_motion(1, 1)
        self.create_motion(1, 2)
        self.create_motion(1, 3)
        self.set_models(
            {
                # "meeting/1": {"is_active_in_organization_id": 1, "committee_id": 1},
                "motion/1": {
                    # "meeting_id": 1,
                    "text": text1,
                    "text_hash": hash1,
                    "identical_motion_ids": [2],
                },
                "motion/2": {
                    # "meeting_id": 1,
                    "text": text1,
                    "text_hash": hash1,
                    "identical_motion_ids": [1],
                },
                "motion/3": {"text": text2, "text_hash": hash2},
            }
        )
        response = self.request(
            "motion.update",
            {
                "id": 2,
                "text": text2,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"identical_motion_ids": None})
        self.assert_model_exists(
            "motion/2", {"text_hash": hash2, "identical_motion_ids": [3]}
        )
        self.assert_model_exists("motion/3", {"identical_motion_ids": [2]})

    def test_update_no_permissions(self) -> None:
        # self.create_meeting()
        self.set_organization_management_level(None)
        # self.user_id = self.create_user("user")
        # self.login(self.user_id)
        self.set_user_groups(1, [3])
        self.set_test_models()
        self.set_models({"motion_state/1": {"allow_submitter_edit": False}})
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
        self.assertEqual(
            "You are not allowed to perform action motion.update. Forbidden fields: title, text, reason",
            response.json["message"],
        )

    def test_update_permission(self) -> None:
        self.base_motion_update_permission_test_internally(
            {
                "id": 111,
                "title": "title_bDFsWtKL",
                "text": "text_eNPkDVuq",
                "reason": "reason_ukWqADfE",
                "created": datetime.fromtimestamp(1686735327),
            },
            Permissions.Motion.CAN_MANAGE,
        )
        self.assert_model_exists(
            "motion/111",
            {
                "title": "title_bDFsWtKL",
                "text": "text_eNPkDVuq",
                "reason": "reason_ukWqADfE",
                "created": datetime.fromtimestamp(1686735327, ZoneInfo("UTC")),
            },
        )

    def test_update_workflow_timestamp_permission_1(self) -> None:
        self.base_motion_update_permission_test_internally(
            {
                "id": 111,
                "workflow_timestamp": datetime.fromtimestamp(1),
            },
            Permissions.Motion.CAN_MANAGE,
        )
        self.assert_model_exists(
            "motion/111",
            {"workflow_timestamp": datetime.fromtimestamp(1, ZoneInfo("UTC"))},
        )

    def test_update_workflow_timestamp_permission_2(self) -> None:
        self.base_motion_update_permission_test_internally(
            {
                "id": 111,
                "workflow_timestamp": datetime.fromtimestamp(1),
            },
            Permissions.Motion.CAN_MANAGE_METADATA,
        )
        self.assert_model_exists(
            "motion/111",
            {"workflow_timestamp": datetime.fromtimestamp(1, ZoneInfo("UTC"))},
        )

    def test_update_workflow_timestamp_permission_3(self) -> None:
        self.base_motion_update_permission_test_internally(
            {
                "id": 111,
                "workflow_timestamp": datetime.fromtimestamp(1),
            },
        )
        self.assert_model_exists(
            "motion/111",
            {"workflow_timestamp": datetime.fromtimestamp(1, ZoneInfo("UTC"))},
        )

    def test_update_permission_created(self) -> None:
        self.setup_can_manage_metadata()
        # response = self.execute_action_internally(
        self.execute_action_internally(
            "motion.update",
            {
                "id": 111,
                "created": datetime.fromtimestamp(11223344),
            },
        )
        # self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/111", {"created": datetime.fromtimestamp(11223344, ZoneInfo("UTC"))}
        )

    def setup_can_manage_metadata(self) -> None:
        # self.create_meeting()
        # self.user_id = self.create_user("user")
        # self.login(self.user_id)
        self.set_test_models()
        self.set_organization_management_level(None)
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])

    def test_update_permission_metadata_forbidden(self) -> None:
        self.setup_can_manage_metadata()
        self.create_mediafile(1, 1)
        # self.set_models(
        #     {
        #         "mediafile/1": {"owner_id": "meeting/1"},
        #     }
        # )
        for field, value in {
            "title": "test",
            "number": "test",
            "text": "test",
            "reason": "test",
            "modified_final_version": "test",
            "attachment_mediafile_ids": [1],
        }.items():
            response = self.request(
                "motion.update",
                {
                    "id": 111,
                    field: value,
                },
            )
            self.assert_status_code(response, 403)
            self.assertEqual(
                f"You are not allowed to perform action motion.update. Forbidden fields: {field}",
                response.json["message"],
            )

    def test_update_permission_metadata_allowed(self) -> None:
        self.setup_can_manage_metadata()
        self.set_models(
            {
                "motion_category/2": {
                    "meeting_id": 1,
                    "name": "test",
                    "sequential_number": 2,
                },
                "motion_block/4": {
                    "meeting_id": 1,
                    "title": "blocky",
                    "sequential_number": 4,
                    "list_of_speakers_id": 1,
                },
                "tag/3": {"meeting_id": 1, "name": "bla"},
            }
        )
        now = datetime.now()
        # response = self.execute_action_internally(
        self.execute_action_internally(
            "motion.update",
            {
                "id": 111,
                "category_id": 2,
                "state_extension": "test",
                "recommendation_extension": "test",
                "start_line_number": 1,
                "created": now,
                "tag_ids": [3],
                "block_id": 4,
                "supporter_meeting_user_ids": [1],
            },
        )
        # self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/111",
            {
                "category_id": 2,
                "state_extension": "test",
                "recommendation_extension": "test",
                "start_line_number": 1,
                "created": now.replace(tzinfo=ZoneInfo("UTC")),
                "tag_ids": [3],
                "block_id": 4,
                "supporter_meeting_user_ids": [1],
            },
        )

    def test_update_permission_submitter_allowed(self) -> None:
        # self.create_meeting()
        # self.user_id = self.create_user("user")
        # self.login(self.user_id)
        self.set_organization_management_level(None)
        # self.set_user_groups(1, [3])
        # self.permission_test_models["motion_submitter/1"]["meeting_user_id"] = 2
        self.permission_test_models["meeting_user/2"] = {
            "meeting_id": 1,
            "user_id": 1,
            "motion_submitter_ids": [1],
        }
        # self.permission_test_models[f"user/{self.user_id}"] = {"meeting_user_ids": [2]}
        self.set_models(self.permission_test_models)
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

    def test_update_permission_metadata_and_submitter(self) -> None:
        # self.create_meeting()
        self.setup_can_manage_metadata()
        # self.user_id = self.create_user("user")
        # self.login(self.user_id)
        # self.set_user_groups(self.user_id, [3])
        # self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE_METADATA])
        # self.permission_test_models["motion_submitter/1"]["meeting_user_id"] = 1
        self.permission_test_models["meeting_user/1"] = {
            # "meeting_id": 1,
            # "user_id": self.user_id,
            "motion_submitter_ids": [1],
        }
        # self.permission_test_models[f"user/{self.user_id}"] = {"meeting_user_ids": [1]}
        self.set_models(self.permission_test_models)
        self.set_models(
            {
                "motion_category/2": {
                    "meeting_id": 1,
                    "name": "test",
                    "sequential_number": 2,
                }
            }
        )
        response = self.request(
            "motion.update",
            {
                "id": 111,
                "title": "title_bDFsWtKL",
                "text": "text_eNPkDVuq",
                "reason": "reason_ukWqADfE",
                "category_id": 2,
            },
        )
        self.assert_status_code(response, 200)

    def test_update_check_not_unique_number(self) -> None:
        self.create_motion(1, 1)
        self.create_motion(1, 2)
        self.set_models(
            {
                # "meeting/1": {
                #     "name": "name_uZXBoHMp",
                #     "is_active_in_organization_id": 1,
                #     "committee_id": 1,
                # },
                "motion/1": {"number": "T001"},
                "motion/2": {"number": "A001"},
            }
        )
        response = self.request(
            "motion.update",
            {
                "id": 1,
                "number": "A001",
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual("Number is not unique.", response.json["message"])

    def test_update_permission_with_mediafile(self) -> None:
        # self.create_meeting()
        self.setup_can_manage_metadata()
        # self.set_models(self.permission_test_models)
        # user_id = self.create_user("user")
        # self.login(user_id)
        # self.set_user_groups(user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_MANAGE])
        self.create_mediafile(1, 1)
        self.set_models(
            {
                # "mediafile/1": {"owner_id": "meeting/1", "meeting_mediafile_ids": [11]},
                "meeting_mediafile/11": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "is_public": True,
                },
            },
        )
        response = self.request(
            "motion.update",
            {
                "id": 111,
                "attachment_mediafile_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/11", {"attachment_ids": ["motion/111"]}
        )

    def test_update_with_published_orga_mediafile_generate_mediafile(self) -> None:
        # self.create_meeting()
        self.set_test_models()
        self.create_mediafile(1)
        # self.set_models(
        #     {
        #         "mediafile/1": {
        #             "owner_id": "organization/1",
        #             "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
        #         },
        #     },
        # )
        response = self.request(
            "motion.update",
            {
                "id": 111,
                "attachment_mediafile_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/1",
            {
                "attachment_ids": ["motion/111"],
                "meeting_id": 1,
                "mediafile_id": 1,
                "access_group_ids": [2],
                "inherited_access_group_ids": [2],
                "is_public": False,
            },
        )

    def test_update_with_published_orga_mediafile(self) -> None:
        # self.create_meeting()
        self.set_test_models()
        self.create_mediafile(1)
        self.set_models(
            {
                # "mediafile/1": {
                #     "owner_id": "organization/1",
                #     "meeting_mediafile_ids": [11],
                #     "published_to_meetings_in_organization_id": ONE_ORGANIZATION_ID,
                # },
                "meeting_mediafile/11": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "is_public": True,
                },
            },
        )
        response = self.request(
            "motion.update",
            {
                "id": 111,
                "attachment_mediafile_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_mediafile/11",
            {
                "attachment_ids": ["motion/111"],
                "meeting_id": 1,
                "mediafile_id": 1,
                "access_group_ids": None,
                "inherited_access_group_ids": None,
                # "is_public": None,
            },
        )
