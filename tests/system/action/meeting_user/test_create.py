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
