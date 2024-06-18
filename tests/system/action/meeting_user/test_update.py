from tests.system.action.base import BaseActionTestCase


class MeetingUserUpdate(BaseActionTestCase):
    def test_update(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "id": 1,
                    "meeting_ids": [10],
                },
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                    "committee_id": 1,
                    "default_group_id": 22,
                    "structure_level_ids": [31],
                },
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "group/21": {"meeting_id": 10},
                "group/22": {"meeting_id": 10, "default_group_for_meeting_id": 10},
                "structure_level/31": {"meeting_id": 10},
            }
        )
        test_dict = {
            "id": 5,
            "comment": "test bla",
            "number": "XII",
            "structure_level_ids": [31],
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
            "group_ids": [21],
        }
        response = self.request("meeting_user.update", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/5", test_dict)
