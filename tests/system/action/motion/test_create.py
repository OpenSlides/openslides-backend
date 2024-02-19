from typing import Any

from openslides_backend.action.actions.motion.mixins import TextHashMixin
from openslides_backend.permissions.base_classes import Permission
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def add_workflow(self) -> None:
        self.set_models(
            {
                "motion_workflow/12": {
                    "meeting_id": 1,
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {
                    "workflow_id": 12,
                    "meeting_id": 1,
                    "set_workflow_timestamp": True,
                },
            }
        )

    def test_create_good_case_required_fields(self) -> None:
        self.add_workflow()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 12,
                "agenda_create": True,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion = self.get_model("motion/1")
        assert motion.get("title") == "test_Xcdfgee"
        assert motion.get("meeting_id") == 1
        assert motion.get("workflow_timestamp") is not None
        assert motion.get("workflow_timestamp") == motion.get("last_modified")
        assert motion.get("created") == motion.get("last_modified")
        assert motion.get("submitter_ids") == [1]
        assert motion.get("state_id") == 34
        assert "agenda_create" not in motion
        submitter = self.get_model("motion_submitter/1")
        assert submitter.get("meeting_user_id") == 1
        assert submitter.get("meeting_id") == 1
        assert submitter.get("motion_id") == 1
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": 1, "user_id": 1, "motion_submitter_ids": [1]},
        )
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 1)
        self.assertEqual(agenda_item.get("content_object_id"), "motion/1")
        self.assert_history_information("motion/1", ["Motion created"])

    def test_create_simple_fields(self) -> None:
        self.add_workflow()
        self.set_user_groups(1, [1])
        self.set_models(
            {
                "motion/1": {
                    "title": "title_eJveLQIh",
                    "meeting_id": 1,
                },
                "motion_category/124": {"name": "name_wbtlHQro", "meeting_id": 1},
                "motion_block/78": {"title": "title_kXTvKvjc", "meeting_id": 1},
                "tag/56": {"name": "name_56", "meeting_id": 1},
                "mediafile/8": {"owner_id": "meeting/1"},
                "meeting/1": {"mediafile_ids": [8]},
                "meeting_user/1": {"meeting_id": 1, "user_id": 1},
            }
        )

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 12,
                "number": "001",
                "sort_parent_id": 1,
                "category_id": 124,
                "block_id": 78,
                "supporter_meeting_user_ids": [1],
                "tag_ids": [56],
                "attachment_ids": [8],
                "text": "test",
                "reason": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/2")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 1
        assert model.get("number") == "001"
        assert model.get("sort_parent_id") == 1
        assert model.get("category_id") == 124
        assert model.get("block_id") == 78
        assert model.get("supporter_meeting_user_ids") == [1]
        assert model.get("tag_ids") == [56]
        assert model.get("attachment_ids") == [8]

    def test_create_empty_data(self) -> None:
        response = self.request("motion.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'title'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "motion.create",
            {
                "title": "title_test1",
                "meeting_id": 1,
                "wrong_field": "text_AefohteiF8",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_workflow_id(self) -> None:
        self.add_workflow()
        response = self.request(
            "motion.create",
            {
                "title": "title_test1",
                "meeting_id": 1,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion = self.get_model("motion/1")
        assert motion.get("state_id") == 34
        assert motion.get("created")

    def test_create_workflow_id_from_meeting(self) -> None:
        response = self.request(
            "motion.create", {"title": "title_test1", "meeting_id": 1, "text": "test"}
        )
        self.assert_status_code(response, 200)
        motion = self.get_model("motion/1")
        assert motion.get("state_id") == 1

    def test_create_missing_default_workflow(self) -> None:
        self.set_models({"meeting/42": {"is_active_in_organization_id": 1}})
        response = self.request(
            "motion.create",
            {"title": "test_Xcdfgee", "meeting_id": 42, "text": "text"},
        )
        self.assert_status_code(response, 400)
        assert (
            "No matching default workflow defined on this meeting"
            in response.json["message"]
        )

    def test_create_missing_text(self) -> None:
        response = self.request(
            "motion.create", {"title": "test_Xcdfgee", "meeting_id": 1}
        )
        self.assert_status_code(response, 400)
        assert "Text is required" in response.json["message"]

    def test_create_with_amendment_paragraphs(self) -> None:
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "text",
                "amendment_paragraphs": {4: "text"},
            },
        )
        self.assert_status_code(response, 400)
        assert "give amendment_paragraphs in this context" in response.json["message"]

    def test_create_reason_missing(self) -> None:
        self.set_models(
            {
                "meeting/1": {"motions_reason_required": True},
            }
        )
        response = self.request(
            "motion.create",
            {"title": "test_Xcdfgee", "meeting_id": 1, "text": "text"},
        )
        self.assert_status_code(response, 400)
        assert "Reason is required" in response.json["message"]

    def test_create_lead_motion_and_statute_paragraph_id_given(self) -> None:
        self.set_models(
            {
                "motion_statute_paragraph/1": {"meeting_id": 1},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "text",
                "lead_motion_id": 1,
                "statute_paragraph_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        assert "both of lead_motion_id and statute_paragraph_id." in response.json.get(
            "message", ""
        )

    def test_create_with_submitters(self) -> None:
        self.set_models(
            {
                "user/56": {"meeting_ids": [1]},
                "user/57": {"meeting_ids": [1]},
                "meeting_user/13": {"meeting_id": 1, "user_id": 56},
                "meeting_user/14": {"meeting_id": 1, "user_id": 57},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "text",
                "submitter_ids": [56, 57],
            },
        )
        self.assert_status_code(response, 200)
        motion = self.get_model("motion/1")
        assert motion.get("submitter_ids") == [1, 2]
        submitter_1 = self.get_model("motion_submitter/1")
        assert submitter_1.get("meeting_id") == 1
        assert submitter_1.get("meeting_user_id") == 13
        assert submitter_1.get("motion_id") == 1
        assert submitter_1.get("weight") == 1
        submitter_2 = self.get_model("motion_submitter/2")
        assert submitter_2.get("meeting_id") == 1
        assert submitter_2.get("meeting_user_id") == 14
        assert submitter_2.get("motion_id") == 1
        assert submitter_2.get("weight") == 2

    def test_create_with_origin_id(self) -> None:
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "origin_id": 12,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "data must not contain {'origin_id'} properties" in response.json["message"]
        )

    def setup_hash_test(self, count: int = 1) -> None:
        self.text = "test"
        self.hash = TextHashMixin.get_hash(self.text)
        self.set_models(
            {
                **{
                    f"motion/{i}": {
                        "title": f"test{i}",
                        "meeting_id": 1,
                        "text": self.text,
                        "text_hash": self.hash,
                    }
                    for i in range(1, count + 1)
                }
            }
        )

    def test_create_single_identical_motion(self) -> None:
        self.setup_hash_test()
        response = self.request(
            "motion.create",
            {
                "title": "test",
                "meeting_id": 1,
                "text": self.text,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2", {"text_hash": self.hash, "identical_motion_ids": [1]}
        )
        self.assert_model_exists("motion/1", {"identical_motion_ids": [2]})

    def test_create_multiple_identical_motions(self) -> None:
        self.setup_hash_test(2)
        response = self.request(
            "motion.create",
            {
                "title": "test",
                "meeting_id": 1,
                "text": self.text,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/3", {"text_hash": self.hash, "identical_motion_ids": [1, 2]}
        )

    def test_create_identical_motion_with_tags(self) -> None:
        self.setup_hash_test()
        response = self.request(
            "motion.create",
            {
                "title": "test",
                "meeting_id": 1,
                "text": f"<p>{self.text}</p>",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2", {"text_hash": self.hash, "identical_motion_ids": [1]}
        )

    def test_create_identical_with_extra_space(self) -> None:
        self.setup_hash_test()
        response = self.request(
            "motion.create",
            {
                "title": "test",
                "meeting_id": 1,
                "text": self.text + " ",
            },
        )
        self.assert_status_code(response, 200)
        motion = self.get_model("motion/2")
        self.assertNotEqual(motion["text_hash"], self.hash)
        self.assertEqual(motion.get("identical_motion_ids", []), [])

    def test_create_identical_motion_in_other_meeting(self) -> None:
        self.setup_hash_test()
        self.create_meeting(10)
        response = self.request(
            "motion.create",
            {
                "title": "test",
                "meeting_id": 10,
                "text": self.text,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2",
            {"meeting_id": 10, "text_hash": self.hash, "identical_motion_ids": []},
        )

    def test_create_no_permission(self) -> None:
        self.base_permission_test(
            {},
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
            },
        )

    def test_create_permission_simple_fields(self) -> None:
        self.base_permission_test(
            {},
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
            },
            Permissions.Motion.CAN_CREATE,
        )

    def setup_permission_test(
        self, permissions: list[Permission], additional_data: dict[str, Any] = {}
    ) -> None:
        user_id = self.create_user("user")
        self.login(user_id)
        self.set_user_groups(user_id, [3])
        self.set_group_permissions(3, permissions)
        if additional_data:
            self.set_models(additional_data)

    def test_create_permission_missing_can_manage(self) -> None:
        self.setup_permission_test([Permissions.Motion.CAN_CREATE])
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "number": "X13",
                "meeting_id": 1,
                "text": "test",
            },
        )
        self.assert_status_code(response, 403)
        assert "Forbidden fields: number" in response.json["message"]

    def test_create_permission_with_can_manage(self) -> None:
        self.setup_permission_test(
            [Permissions.Motion.CAN_CREATE, Permissions.Motion.CAN_MANAGE]
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "number": "X13",
                "meeting_id": 1,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)

    def test_create_permission_with_can_create_and_mediafile_can_see(self) -> None:
        self.setup_permission_test(
            [Permissions.Motion.CAN_CREATE, Permissions.Mediafile.CAN_SEE],
            {
                "mediafile/1": {
                    "owner_id": "meeting/1",
                },
            },
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "attachment_ids": [1],
            },
        )
        self.assert_status_code(response, 200)

    def test_create_permission_with_can_create_and_not_mediafile_can_see(self) -> None:
        self.setup_permission_test(
            [Permissions.Motion.CAN_CREATE],
            {
                "mediafile/1": {
                    "owner_id": "meeting/1",
                },
            },
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "attachment_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        assert "Forbidden fields: attachment_ids" in response.json["message"]

    def test_create_permission_no_double_error(self) -> None:
        self.setup_permission_test(
            [Permissions.Motion.CAN_CREATE],
            {
                "mediafile/1": {
                    "owner_id": "meeting/1",
                },
            },
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "attachment_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action motion.create. Forbidden fields: attachment_ids"
        )
