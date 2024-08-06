from tests.system.action.base import BaseActionTestCase


class MeetingUserCreate(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models(
            {
                "committee/1": {"meeting_ids": [10]},
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                    "structure_level_ids": [31],
                    "group_ids": [21],
                },
                "group/21": {"meeting_id": 10},
                "structure_level/31": {"meeting_id": 10},
            }
        )
        test_dict = {
            "user_id": 1,
            "meeting_id": 10,
            "comment": "test blablaba",
            "number": "XII",
            "structure_level_ids": [31],
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
            "group_ids": [21],
        }
        response = self.request("meeting_user.create", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/1", test_dict)
        self.assert_model_exists("user/1", {"committee_ids": [1]})

    def test_create_anonymous_group_id(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"group_ids": [1, 2, 3, 4]},
                "group/4": {"anonymous_group_for_meeting_id": 1},
            }
        )
        user_id = self.create_user("dummy")
        response = self.request(
            "meeting_user.create",
            {
                "user_id": user_id,
                "meeting_id": 1,
                "group_ids": [4],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot add explicit users to a meetings anonymous group",
            response.json["message"],
        )
