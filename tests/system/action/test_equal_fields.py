from typing import Any

from openslides_backend.action.actions.motion.mixins import TextHashMixin
from openslides_backend.action.mixins.delegation_based_restriction_mixin import (
    DelegationBasedRestriction,
)
from openslides_backend.models.models import AgendaItem
from openslides_backend.permissions.base_classes import Permission
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class EqualFieldsActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_meeting(4)

    def foreign_meeting_user_motion_create_test(self, field:str, collection: str)->None:
        self.create_user("bob",[5])
        self.set_user_groups(1,[2])
        self.set_models({
            "meeting/1": {
                "motions_create_enable_additional_submitter_text": True,
                "motions_supporters_min_amount": 1,
            }
        })
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "text": "test",
                "reason": "test",
                "additional_submitter": "test",
                field: [1],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            f"""Invalid data for '{collection}/1': The relation meeting_user_ids requires the following fields to be equal:
 {collection}/1/meeting_ids: 1 
 meeting_user/1/meeting_ids: 4""",
            response.json["message"],
        )

    def test_motion_create_foreign_submitter_meeting_user_error(self)-> None:
        self.foreign_meeting_user_motion_create_test("submitter_meeting_user_ids", "motion_submitter")

    def test_motion_create_foreign_supporter_meeting_user_error(self)-> None:
        self.foreign_meeting_user_motion_create_test("supporter_meeting_user_ids", "motion_supporter")

    def setup_chat_group_test(self) -> None:
        self.set_models({
            "chat_group/1": {
                "meeting_id": 1,
                "name": "Chat me up, baby!"
            }
        })
    
    def test_create_group_no_chat(self) -> None:
        response = self.request("group.create", {"name": "Grrrrrr", "meeting_id": 4})
        self.assert_status_code(response, 200)

    def test_create_chat_no_group(self) -> None:
        response = self.request("chat_group.create", {"name": "Chat me up too, please?", "meeting_id": 1})
        self.assert_status_code(response, 200)

    def test_create_chat_with_same_meeting_read_group(self) -> None:
        response = self.request("chat_group.create", {"name": "Chat me up too, please?", "meeting_id": 1, "read_group_ids": [2]})
        self.assert_status_code(response, 200)

    def test_create_chat_with_other_meeting_read_group(self) -> None:
        response = self.request("chat_group.create", {"name": "Chat me up too, please?", "meeting_id": 1, "read_group_ids": [5]})
        self.assert_status_code(response, 400)
        self.assertIn(
            f"""Invalid data for 'chat_group/1': The relation meeting_user_ids requires the following fields to be equal:
 chat_group/1/meeting_ids: 1 
 meeting_user/1/meeting_ids: 4""",
            response.json["message"],
        )
