import pytest

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

    def test_set_data_with_meeting_user_and_id(self) -> None:
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
            "id": 5,
            "comment": "test bla",
            "number": "XII",
            "structure_level": "A",
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/5", {"meeting_id": 10, "user_id": 1, **test_dict}
        )

    def test_set_data_with_meeting_user_and_wrong_meeting_id(self) -> None:
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
            "id": 5,
            "meeting_id": 12,
            "comment": "test bla",
        }
        with pytest.raises(AssertionError, match="Not permitted to change meeting_id."):
            self.request("meeting_user.set_data", test_dict)

    def test_set_data_with_meeting_user_and_wrong_user_id(self) -> None:
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
            "id": 5,
            "user_id": 3,
            "comment": "test bla",
        }
        with pytest.raises(AssertionError, match="Not permitted to change user_id."):
            self.request("meeting_user.set_data", test_dict)

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

    def test_set_data_missing_identifiers(self) -> None:
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
            "comment": "test bla",
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 400)
        assert (
            "Identifier for meeting_user instance required, but neither id nor meeting_id/user_id is given."
            == response.json["message"]
        )

    def test_prevent_zero_vote_weight(self) -> None:
        self.set_models(
            {
                "meeting/10": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5],
                },
                "meeting_user/5": {
                    "user_id": 1,
                    "meeting_id": 10,
                    "vote_weight": "1.000000",
                },
            }
        )
        response = self.request("meeting_user.set_data", {"vote_weight": "0.000000"})
        self.assert_status_code(response, 400)
        self.assert_model_exists("meeting_user/5", {"vote_weight": "1.000000"})
