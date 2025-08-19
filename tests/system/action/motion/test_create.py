from typing import Any

from openslides_backend.action.actions.motion.mixins import TextHashMixin
from openslides_backend.action.mixins.delegation_based_restriction_mixin import (
    DelegationBasedRestriction,
)
from openslides_backend.models.models import AgendaItem
from openslides_backend.permissions.base_classes import Permission
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()

    def test_create_good_case_required_fields(self) -> None:
        self.set_models({"motion_state/1": {"set_workflow_timestamp": True}})
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 1,
                "agenda_create": True,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion = self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "submitter_ids": [1],
                "state_id": 1,
            },
        )
        assert motion.get("workflow_timestamp")
        assert (
            motion["workflow_timestamp"] == motion["last_modified"] == motion["created"]
        )
        self.assert_model_exists(
            "motion_submitter/1",
            {"meeting_user_id": 1, "meeting_id": 1, "motion_id": 1},
        )
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": 1, "user_id": 1, "motion_submitter_ids": [1]},
        )
        self.assert_model_exists(
            "agenda_item/1", {"meeting_id": 1, "content_object_id": "motion/1"}
        )
        self.assert_history_information("motion/1", ["Motion created"])

    def test_create_simple_fields(self) -> None:
        self.set_user_groups(1, [1])
        self.create_mediafile(8, 1)
        self.create_motion(1)
        self.set_models(
            {
                "motion_category/124": {
                    "name": "name_wbtlHQro",
                    "meeting_id": 1,
                    "sequential_number": 124,
                },
                "motion_block/78": {
                    "title": "title_kXTvKvjc",
                    "meeting_id": 1,
                    "sequential_number": 78,
                },
                "tag/56": {"name": "name_56", "meeting_id": 1},
                "meeting_mediafile/80": {
                    "meeting_id": 1,
                    "mediafile_id": 8,
                    "is_public": False,
                },
                "meeting/1": {"motions_create_enable_additional_submitter_text": True},
                "motion_state/1": {"set_workflow_timestamp": True},
            }
        )
        motion = {
            "title": "test_Xcdfgee",
            "meeting_id": 1,
            "number": "001",
            "sort_parent_id": 1,
            "category_id": 124,
            "block_id": 78,
            "supporter_meeting_user_ids": [1],
            "tag_ids": [56],
            "text": "test",
            "reason": "test",
            "additional_submitter": "test",
        }

        response = self.request(
            "motion.create", motion | {"attachment_mediafile_ids": [8]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/2",
            {
                **motion,
                "attachment_meeting_mediafile_ids": [80],
                "submitter_ids": None,
                "additional_submitter": "test",
            },
        )

    def test_create_normal_and_additional_submitter(self) -> None:
        """Also checks that this works with just Motion.CAN_CREATE, Permissions.Motion.CAN_MANAGE_METADATA permissions."""
        self.update_model(
            "meeting/1", {"motions_create_enable_additional_submitter_text": True}
        )
        bob_id = self.setup_permission_test(
            [
                Permissions.Motion.CAN_CREATE,
                Permissions.Motion.CAN_MANAGE_METADATA,
                Permissions.User.CAN_SEE,
            ]
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "reason": "test",
                "additional_submitter": "test",
                "submitter_ids": [bob_id],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1", {"additional_submitter": "test", "submitter_ids": [1]}
        )
        self.assert_model_exists(
            "motion_submitter/1", {"motion_id": 1, "meeting_user_id": 1}
        )
        self.assert_model_exists("meeting_user/1", {"meeting_id": 1, "user_id": bob_id})

    def test_create_additional_submitter_forbidden_in_meeting(self) -> None:
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "reason": "test",
                "additional_submitter": "test",
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("motion/1")
        self.assertEqual(
            "This meeting doesn't allow additional_submitter to be set in creation",
            response.json["message"],
        )

    def test_create_empty_data(self) -> None:
        response = self.request("motion.create", {})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("motion/1")
        self.assertEqual(
            "Action motion.create: data must contain ['meeting_id', 'title'] properties",
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
        self.assert_model_not_exists("motion/1")
        self.assertEqual(
            "Action motion.create: data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_with_set_number(self) -> None:
        self.set_models(
            {
                "meeting/1": {"motions_number_min_digits": 1},
                "motion_state/1": {"set_number": True, "set_workflow_timestamp": True},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "title_test1",
                "meeting_id": 1,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion = self.assert_model_exists("motion/1", {"state_id": 1, "number": "1"})
        assert motion.get("workflow_timestamp")
        self.assertEqual(motion.get("workflow_timestamp"), motion.get("created"))

    def test_create_workflow_id_from_meeting(self) -> None:
        response = self.request(
            "motion.create", {"title": "title_test1", "meeting_id": 1, "text": "test"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion/1", {"state_id": 1})

    def test_create_missing_text(self) -> None:
        response = self.request(
            "motion.create", {"title": "test_Xcdfgee", "meeting_id": 1}
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("motion/1")
        self.assertEqual("Text is required", response.json["message"])

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
        self.assert_model_not_exists("motion/1")
        self.assertEqual(
            "You can't give amendment_paragraphs in this context",
            response.json["message"],
        )

    def test_create_reason_missing(self) -> None:
        self.set_models({"meeting/1": {"motions_reason_required": True}})
        response = self.request(
            "motion.create",
            {"title": "test_Xcdfgee", "meeting_id": 1, "text": "text"},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("motion/1")
        self.assertEqual("Reason is required", response.json["message"])

    def test_create_with_submitters(self) -> None:
        self.set_models(
            {
                "user/56": {"username": "user_56", "meeting_ids": [1]},
                "user/57": {"username": "user_57", "meeting_ids": [1]},
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
        self.assert_model_exists("motion/1", {"submitter_ids": [1, 2]})
        self.assert_model_exists(
            "motion_submitter/1",
            {"meeting_id": 1, "meeting_user_id": 13, "motion_id": 1, "weight": 1},
        )
        self.assert_model_exists(
            "motion_submitter/2",
            {"meeting_id": 1, "meeting_user_id": 14, "motion_id": 1, "weight": 2},
        )

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
        self.assert_model_not_exists("motion/1")
        self.assertEqual(
            "Action motion.create: data must not contain {'origin_id'} properties",
            response.json["message"],
        )

    def setup_hash_test(self, count: int = 1) -> None:
        self.text = "test"
        self.hash = TextHashMixin.get_hash(self.text)
        for i in range(1, count + 1):
            self.create_motion(
                meeting_id=1,
                base=i,
                motion_data={"text": self.text, "text_hash": self.hash},
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
        self.assert_model_exists("motion/3", {"text_hash": self.hash})
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
        motion = self.assert_model_exists("motion/2", {"identical_motion_ids": None})
        self.assertNotEqual(motion["text_hash"], self.hash)

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
            {"meeting_id": 10, "text_hash": self.hash, "identical_motion_ids": None},
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

    def test_create_permission_simple_fields_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
            },
        )

    def setup_permission_test(
        self, permissions: list[Permission], additional_data: dict[str, Any] = {}
    ) -> int:
        """
        Sets up a user with the given permissions in group 3 of a meeting.
        Additional model data can be given.
        Logs in the user and returns his id.
        """
        user_id = self.create_user("user")
        self.login(user_id)
        self.set_user_groups(user_id, [3])
        self.set_group_permissions(3, permissions)
        if additional_data:
            self.set_models(additional_data)
        return user_id

    def test_create_no_permission_submitter(self) -> None:
        """
        Asserts that the requesting user needs at least Motion.CAN_CREATE and
        Motion.CAN_MANAGE_METADATA when sending submitter_ids and additional_submitter.
        Also additionally for submitter_ids User.CAN_SEE.
        """
        user_id = self.setup_permission_test([Permissions.Motion.CAN_CREATE])
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "reason": "test",
                "additional_submitter": "test",
                "submitter_ids": [1, user_id],
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action motion.create. Forbidden fields: additional_submitter with possibly needed permission(s): motion.can_manage, motion.can_manage_metadata, submitter_ids with possibly needed permission(s): motion.can_manage, motion.can_manage_metadata, user.can_see"
            == response.json["message"]
        )
        self.assert_model_not_exists("motion/1")
        self.assert_model_not_exists("motion_submitter/1")
        self.assert_model_exists(
            "meeting_user/1", {"meeting_id": 1, "user_id": user_id}
        )

    def test_create_no_user_can_see_submitter(self) -> None:
        """
        Asserts that the requesting user needs at least Motion.CAN_CREATE and
        Motion.CAN_MANAGE_METADATA, User.CAN_SEE when sending submitter_ids.
        Also asserts that the error message contains Motion.CAN_MANAGE as possible permission.
        """
        user_id = self.setup_permission_test(
            [Permissions.Motion.CAN_CREATE, Permissions.Motion.CAN_MANAGE_METADATA]
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "reason": "test",
                "submitter_ids": [1, user_id],
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action motion.create. Forbidden fields: submitter_ids with possibly needed permission(s): motion.can_manage, user.can_see"
            == response.json["message"]
        )
        self.assert_model_not_exists("motion/1")
        self.assert_model_not_exists("motion_submitter/1")
        self.assert_model_exists(
            "meeting_user/1", {"meeting_id": 1, "user_id": user_id}
        )

    def test_create_no_permission_additional_submitter_enabled(self) -> None:
        """
        Asserts that the requesting user needs at least Motion.CAN_CREATE and
        Motion.CAN_MANAGE_METADATA when sending submitter_ids and additional_submitter.
        Also additionally for submitter_ids User.CAN_SEE.
        """
        user_id = self.setup_permission_test([Permissions.Motion.CAN_CREATE])
        self.update_model(
            "meeting/1", {"motions_create_enable_additional_submitter_text": True}
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "reason": "test",
                "additional_submitter": "test",
                "submitter_ids": [1, user_id],
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action motion.create. Forbidden fields: additional_submitter with possibly needed permission(s): motion.can_manage, motion.can_manage_metadata, submitter_ids with possibly needed permission(s): motion.can_manage, motion.can_manage_metadata, user.can_see"
            == response.json["message"]
        )
        self.assert_model_not_exists("motion/1")
        self.assert_model_not_exists("motion_submitter/1")
        self.assert_model_exists(
            "meeting_user/1", {"meeting_id": 1, "user_id": user_id}
        )

    def test_create_permission_agenda_allowed(self) -> None:
        self.setup_permission_test(
            [
                Permissions.AgendaItem.CAN_MANAGE,
                Permissions.Motion.CAN_CREATE,
                Permissions.Motion.CAN_MANAGE_METADATA,
            ]
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "agenda_create": True,
                "agenda_type": AgendaItem.INTERNAL_ITEM,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "agenda_item_id": 1,
            },
        )
        self.assert_model_exists("agenda_item/1", {"content_object_id": "motion/1"})

    def test_create_permission_agenda_forbidden(self) -> None:
        self.setup_permission_test(
            [
                Permissions.Motion.CAN_CREATE,
                Permissions.Motion.CAN_MANAGE_METADATA,
            ]
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "agenda_create": True,
                "agenda_type": AgendaItem.INTERNAL_ITEM,
            },
        )
        self.assert_status_code(response, 403)
        self.assert_model_not_exists("motion/1")
        self.assertEqual(
            "You are not allowed to perform action motion.create. Forbidden fields: agenda_create with possibly needed permission(s): agenda_item.can_manage, motion.can_manage, agenda_type with possibly needed permission(s): agenda_item.can_manage, motion.can_manage",
            response.json["message"],
        )

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
        self.assert_model_not_exists("motion/1")
        self.assertEqual(
            "You are not allowed to perform action motion.create. Forbidden fields: number with possibly needed permission(s): motion.can_manage",
            response.json["message"],
        )

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
        self.assert_model_exists(
            "motion/1", {"title": "test_Xcdfgee", "meeting_id": 1, "text": "test"}
        )

    def test_create_permission_with_can_create_and_mediafile_can_see(self) -> None:
        self.create_mediafile(1, 1)
        self.setup_permission_test(
            [Permissions.Motion.CAN_CREATE, Permissions.Mediafile.CAN_SEE],
            {
                "meeting_mediafile/11": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "is_public": False,
                },
            },
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "attachment_mediafile_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "attachment_meeting_mediafile_ids": [11],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/11", {"attachment_ids": ["motion/1"]}
        )

    def test_create_permission_with_can_create_and_not_mediafile_can_see(self) -> None:
        self.create_mediafile(1, 1)
        self.setup_permission_test(
            [Permissions.Motion.CAN_CREATE],
            {
                "meeting_mediafile/11": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "is_public": False,
                },
            },
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "attachment_mediafile_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        self.assert_model_not_exists("motion/1")
        self.assertEqual(
            "You are not allowed to perform action motion.create. Forbidden fields: attachment_mediafile_ids with possibly needed permission(s): mediafile.can_see, motion.can_manage",
            response.json["message"],
        )

    def test_create_permission_no_double_error(self) -> None:
        self.create_mediafile(1, 1)
        self.setup_permission_test(
            [Permissions.Motion.CAN_CREATE],
            {
                "meeting_mediafile/11": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "is_public": False,
                },
            },
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "attachment_mediafile_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action motion.create. Forbidden fields: attachment_mediafile_ids with possibly needed permission(s): mediafile.can_see, motion.can_manage"
        )
        self.assert_model_not_exists("motion/1")

    def test_create_check_not_unique_number(self) -> None:
        self.create_motion(1, 1, motion_data={"number": "T001"})
        self.create_motion(1, 2, motion_data={"number": "A001"})
        response = self.request(
            "motion.create",
            {
                "title": "Title",
                "text": "<p>of motion</p>",
                "number": "A001",
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual("Number is not unique.", response.json["message"])
        self.assert_model_not_exists("motion/3")

    def test_create_amendment_paragraphs_where_not_allowed(self) -> None:
        self.create_motion(1)
        response = self.request(
            "motion.create",
            {
                "title": "Title",
                "text": "<p>of motion</p>",
                "number": "A001",
                "amendment_paragraphs": {4: "text"},
                "meeting_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assertEqual(
            "You can't give amendment_paragraphs in this context",
            response.json["message"],
        )
        self.assert_model_not_exists("motion/2")

    def create_delegator_test_data(
        self,
        is_delegator: bool = False,
        perm: Permission = Permissions.Motion.CAN_CREATE,
        delegator_setting: DelegationBasedRestriction = "users_forbid_delegator_as_submitter",
        disable_delegations: bool = False,
    ) -> None:
        self.set_models(
            {
                "meeting_user/1": {"user_id": 1, "meeting_id": 1},
                "meeting/1": {
                    delegator_setting: True,
                    **(
                        {}
                        if disable_delegations
                        else {"users_enable_vote_delegations": True}
                    ),
                },
                "motion_state/1": {"set_workflow_timestamp": True},
            }
        )
        if is_delegator:
            self.create_user("delegatee", [1])
            self.set_models(
                {
                    "meeting_user/1": {"vote_delegated_to_id": 2},
                    "meeting_user/2": {"vote_delegations_from_ids": [1]},
                }
            )
        self.set_organization_management_level(None)
        self.set_group_permissions(1, [perm])
        self.set_user_groups(1, [1])

    def test_create_delegator_setting(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "users_forbid_delegator_as_submitter": True,
                    "users_enable_vote_delegations": True,
                },
                "motion_state/1": {"set_workflow_timestamp": True},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 1,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "submitter_ids": [1],
            },
        )

    def test_create_delegator_setting_with_no_delegation(self) -> None:
        self.create_delegator_test_data()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 1,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "submitter_ids": [1],
            },
        )

    def test_create_delegator_setting_with_delegation(self) -> None:
        self.create_delegator_test_data(is_delegator=True)
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 1,
                "text": "test",
            },
        )
        self.assert_status_code(response, 403)
        assert (
            response.json["message"]
            == "You are not allowed to perform action motion.create. Missing Permission: motion.can_manage"
        )
        self.assert_model_not_exists("motion/1")

    def test_create_delegator_setting_with_delegation_delegations_turned_off(
        self,
    ) -> None:
        self.create_delegator_test_data(is_delegator=True, disable_delegations=True)
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 1,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "submitter_ids": [1],
            },
        )

    def test_create_delegator_setting_with_motion_manager_delegation(
        self,
    ) -> None:
        self.create_delegator_test_data(
            is_delegator=True, perm=Permissions.Motion.CAN_MANAGE
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 1,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "submitter_ids": [1],
            },
        )

    def test_create_with_irrelevant_delegator_setting(self) -> None:
        self.create_delegator_test_data(
            is_delegator=True, delegator_setting="users_forbid_delegator_as_supporter"
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 1,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "motion/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "submitter_ids": [1],
            },
        )

    def base_assign_external_self_test(self, oml: OrganizationManagementLevel) -> None:
        bob_id = self.create_user("bob", organization_management_level=oml)
        self.login(bob_id)
        response = self.request_multi(
            "motion.create",
            [
                {
                    "title": "Submitter is me",
                    "meeting_id": 1,
                    "text": "test",
                },
                {
                    "title": "Submitter is me 2",
                    "meeting_id": 1,
                    "text": "test 2",
                    "submitter_ids": [bob_id],
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/1", {"user_id": bob_id, "motion_submitter_ids": [1, 2]}
        )
        self.assert_model_exists(
            "motion_submitter/1", {"meeting_user_id": 1, "motion_id": 1}
        )
        self.assert_model_exists(
            "motion_submitter/2", {"meeting_user_id": 1, "motion_id": 2}
        )
        self.assert_model_exists(
            "motion/1",
            {
                "title": "Submitter is me",
                "meeting_id": 1,
                "text": "test",
                "submitter_ids": [1],
            },
        )
        self.assert_model_exists(
            "motion/2",
            {
                "title": "Submitter is me 2",
                "meeting_id": 1,
                "text": "test 2",
                "submitter_ids": [2],
            },
        )

    def test_create_assign_self_with_external_superadmin(self) -> None:
        self.base_assign_external_self_test(OrganizationManagementLevel.SUPERADMIN)

    def test_create_assign_self_with_external_orga_admin(self) -> None:
        self.base_assign_external_self_test(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
