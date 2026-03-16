
from tests.system.action.base import BaseActionTestCase


class EqualFieldsActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.create_meeting(4)

    def foreign_meeting_user_motion_create_test(
        self, field: str, collection: str
    ) -> None:
        self.create_user("bob", [5])
        self.set_user_groups(1, [2])
        self.set_models(
            {
                "meeting/1": {
                    "motions_create_enable_additional_submitter_text": True,
                    "motions_supporters_min_amount": 1,
                }
            }
        )
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
            "Relation violates required constraint: The following models do not belong to meeting 1: ['meeting_user/1']",
            response.json["message"],
        )

    def test_motion_create_foreign_submitter_meeting_user_error(self) -> None:
        self.foreign_meeting_user_motion_create_test(
            "submitter_meeting_user_ids", "motion_submitter"
        )

    def test_motion_create_foreign_supporter_meeting_user_error(self) -> None:
        self.foreign_meeting_user_motion_create_test(
            "supporter_meeting_user_ids", "motion_supporter"
        )

    def setup_chat_group_test(self) -> None:
        self.set_models(
            {
                "organization/1": {"enable_chat": True},
                "chat_group/1": {"meeting_id": 1, "name": "Chat me up, baby!"},
            }
        )

    def test_create_group_no_chat(self) -> None:
        response = self.request("group.create", {"name": "Grrrrrr", "meeting_id": 4})
        self.assert_status_code(response, 200)

    def test_create_chat_no_group(self) -> None:
        self.setup_chat_group_test()
        response = self.request(
            "chat_group.create", {"name": "Chat me up too, please?", "meeting_id": 1}
        )
        self.assert_status_code(response, 200)

    def test_create_chat_with_same_meeting_read_group(self) -> None:
        self.setup_chat_group_test()
        response = self.request(
            "chat_group.create",
            {"name": "Chat me up too, please?", "meeting_id": 1, "read_group_ids": [2]},
        )
        self.assert_status_code(response, 200)

    def test_create_chat_with_other_meeting_read_group(self) -> None:
        self.setup_chat_group_test()
        response = self.request(
            "chat_group.create",
            {"name": "Chat me up too, please?", "meeting_id": 1, "read_group_ids": [5]},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Relation violates required constraint: The following models do not belong to meeting 1: ['group/5']",
            response.json["message"],
        )

    def test_update_add_group_to_chat_read_group(self) -> None:
        self.setup_chat_group_test()
        response = self.request("chat_group.update", {"id": 1, "read_group_ids": [2]})
        self.assert_status_code(response, 200)

    def test_update_add_other_meeting_group_to_chat_read_group(self) -> None:
        self.setup_chat_group_test()
        response = self.request("chat_group.update", {"id": 1, "read_group_ids": [5]})
        self.assertIn(
            "Relation violates required constraint: The following models do not belong to meeting 1: ['group/5']",
            response.json["message"],
        )

    def test_delete_poll_option_user(self) -> None:
        self.create_topic(1, 1)
        bob_id = self.create_user("bob", [1])
        self.set_models(
            {
                "poll/1": {
                    "type": "named",
                    "pollmethod": "Y",
                    "backend": "long",
                    "state": "finished",
                    "meeting_id": 1,
                    "content_object_id": "topic/1",
                    "title": "Poll 1",
                    "onehundred_percent_base": "YNA",
                },
                "option/1": {
                    "meeting_id": 1,
                    "poll_id": 1,
                    "content_object_id": f"user/{bob_id}",
                },
                "option/2": {"meeting_id": 1, "poll_id": 1},
            }
        )
        response = self.request("user.delete", {"id": bob_id})
        self.assert_status_code(response, 200)

    def test_create_option_wrong_meeting_on_user(self) -> None:
        self.create_topic(1, 1)
        bob_id = self.create_user("bob", [5])
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "YN",
                "onehundred_percent_base": "valid",
                "options": [
                    {
                        "content_object_id": f"user/{bob_id}",
                        "Y": "10.000000",
                        "N": "5.000000",
                    },
                    {"text": "text", "Y": "10.000000"},
                ],
                "meeting_id": 1,
                "content_object_id": "topic/1",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            f"Relation violates required constraint: The following models do not belong to meeting 1: ['user/2']",
            response.json["message"],
        )

    def test_project_wrong_meeting_by_content_meeting(self) -> None:
        response = self.request(
            "projector.project",
            {
                "ids": [4],
                "content_object_id": "meeting/1",
                "meeting_id": 4,
                "stable": True,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Relation violates required constraint: The following models do not belong to meeting 1: ['meeting/4']",
            response.json["message"],
        )
