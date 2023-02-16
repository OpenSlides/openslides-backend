from tests.system.action.base import BaseActionTestCase


class MeetingUserSetData(BaseActionTestCase):
    def test_set_data_with_meeting_user(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                },
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
            }
        )
        test_dict = {
            "meeting_id": 10,
            "user_id": 1,
            "comment": "test bla",
            "number": "XII",
            "structure_level": "A",
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/5", test_dict)

    def test_set_data_without_meeting_user(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [],
                },
            }
        )
        test_dict = {
            "meeting_id": 10,
            "user_id": 1,
            "comment": "test bla",
            "number": "XII",
            "structure_level": "A",
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/1", test_dict)
