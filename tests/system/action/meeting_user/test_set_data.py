from decimal import Decimal

import pytest

from tests.system.action.base import BaseActionTestCase


class MeetingUserSetData(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(10)

    def test_set_data_with_meeting_user(self) -> None:
        self.set_models(
            {
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "structure_level/31": {"name": "structy", "meeting_id": 10},
            }
        )
        test_dict = {
            "meeting_id": 10,
            "user_id": 1,
            "comment": "test bla",
            "number": "XII",
            "structure_level_ids": [31],
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/5", {**test_dict, "vote_weight": Decimal("1.5")}
        )

    def test_set_data_with_meeting_user_and_id(self) -> None:
        self.set_models(
            {
                "meeting_user/5": {"user_id": 1, "meeting_id": 10},
                "structure_level/31": {"name": "structy", "meeting_id": 10},
            }
        )
        test_dict = {
            "id": 5,
            "comment": "test bla",
            "number": "XII",
            "structure_level_ids": [31],
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/5",
            {
                "meeting_id": 10,
                "user_id": 1,
                **test_dict,
                "vote_weight": Decimal("1.5"),
            },
        )

    def test_set_data_with_meeting_user_and_wrong_meeting_id(self) -> None:
        self.set_models(
            {
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
                "structure_level/31": {"name": "structy", "meeting_id": 10},
            }
        )
        test_dict = {
            "meeting_id": 10,
            "user_id": 1,
            "comment": "test bla",
            "number": "XII",
            "structure_level_ids": [31],
            "about_me": "A very long description.",
            "vote_weight": "1.500000",
        }
        response = self.request("meeting_user.set_data", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/1", {**test_dict, "vote_weight": Decimal("1.5")}
        )

    def test_set_data_missing_identifiers(self) -> None:
        self.set_models(
            {
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
                "meeting_user/5": {
                    "user_id": 1,
                    "meeting_id": 10,
                    "vote_weight": "1.000000",
                },
            }
        )
        response = self.request("meeting_user.set_data", {"vote_weight": "0.000000"})
        self.assert_status_code(response, 400)
        self.assert_model_exists("meeting_user/5", {"vote_weight": Decimal("1.000000")})

    def test_set_data_anonymous_group_id(self) -> None:
        self.set_models(
            {
                "meeting/10": {"anonymous_group_id": 4},
                "group/4": {"name": "groupy", "meeting_id": 10},
            }
        )
        self.create_user("dummy", [10])
        response = self.request(
            "meeting_user.set_data",
            {
                "id": 1,
                "group_ids": [4],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot add explicit users to a meetings anonymous group",
            response.json["message"],
        )

    def test_set_data_anonymous_group_id_2(self) -> None:
        self.set_models(
            {
                "meeting/10": {"anonymous_group_id": 4},
                "group/4": {"name": "groupy", "meeting_id": 10},
            }
        )
        user_id = self.create_user("dummy")
        response = self.request(
            "meeting_user.set_data",
            {
                "user_id": user_id,
                "meeting_id": 10,
                "group_ids": [10, 4],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot add explicit users to a meetings anonymous group",
            response.json["message"],
        )
