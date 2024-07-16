from typing import Any

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permission, Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class UserUpdateActionTest(BaseActionTestCase):
    def permission_setup(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("test", group_ids=[1])
        self.login(self.user_id)
        self.set_models(
            {
                "user/111": {"username": "User111"},
            }
        )

    def test_update_correct(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
        )
        response = self.request(
            "user.update", {"id": 111, "username": "username_Xcdfgee"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("username") == "username_Xcdfgee"
        self.assert_history_information("user/111", ["Personal data changed"])

    def test_update_some_more_fields(self) -> None:
        self.set_models(
            {
                "user/111": {"username": "username_srtgb123"},
                "meeting/110": {"name": "name_DsJFXoot"},
                "committee/78": {"name": "name_xXRGTLAJ"},
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 111,
                "pronoun": "Test",
                "username": "username_Xcdfgee",
                "default_vote_weight": "1.700000",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                "committee_management_ids": [78],
                "member_number": "1234-5768-9abc",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "username_Xcdfgee",
                "pronoun": "Test",
                "default_vote_weight": "1.700000",
                "committee_ids": [78],
                "committee_management_ids": [78],
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                "member_number": "1234-5768-9abc",
            },
        )

    def test_update_with_meeting_user_fields(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "C1", "meeting_ids": [1]},
                "committee/2": {"name": "C2", "meeting_ids": [2]},
                "meeting/1": {
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "user_ids": [23],
                    "meeting_user_ids": [223],
                    "structure_level_ids": [31],
                },
                "meeting/2": {"committee_id": 2, "is_active_in_organization_id": 1},
                "user/22": {
                    "committee_ids": [1],
                    "committee_management_ids": [1],
                },
                "user/23": {
                    "meeting_ids": [1],
                    "meeting_user_ids": [223],
                    "committee_ids": [1],
                },
                "meeting_user/223": {"meeting_id": 1, "user_id": 23, "group_ids": [11]},
                "group/11": {"meeting_id": 1, "meeting_user_ids": [223]},
                "structure_level/31": {"meeting_id": 1},
            }
        )
        request_fields = {
            "group_ids": [11],
            "number": "number",
            "structure_level_ids": [31],
            "vote_weight": "1.000000",
        }
        response = self.request(
            "user.update",
            {
                "id": 22,
                "committee_management_ids": [2],
                "meeting_id": 1,
                "vote_delegations_from_ids": [223],
                "comment": "comment<iframe></iframe>",
                "about_me": "<p>about</p><iframe></iframe>",
                **request_fields,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/22",
            {
                "committee_management_ids": [2],
                "committee_ids": [1, 2],
                "meeting_ids": [1],
                "meeting_user_ids": [224],
            },
        )
        self.assert_model_exists(
            "meeting_user/224",
            {
                "user_id": 22,
                "meeting_id": 1,
                "vote_delegations_from_ids": [223],
                "comment": "comment&lt;iframe&gt;&lt;/iframe&gt;",
                "about_me": "<p>about</p>&lt;iframe&gt;&lt;/iframe&gt;",
                **request_fields,
            },
        )
        self.assert_model_exists(
            "user/23",
            {
                "committee_ids": [1],
                "meeting_ids": [1],
                "meeting_user_ids": [223],
            },
        )
        self.assert_model_exists(
            "meeting_user/223",
            {
                "user_id": 23,
                "meeting_id": 1,
                "group_ids": [11],
                "vote_delegated_to_id": 224,
            },
        )
        self.assert_history_information(
            "user/22",
            [
                "Participant added to meeting {}",
                "meeting/1",
                "Committee management changed",
            ],
        )

    def test_update_set_and_reset_vote_forwarded(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "C1", "meeting_ids": [1]},
                "meeting/1": {
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "user_ids": [22, 23],
                    "meeting_user_ids": [222, 223],
                },
                "user/22": {
                    "meeting_ids": [1],
                    "meeting_user_ids": [223],
                },
                "user/23": {
                    "meeting_ids": [1],
                    "meeting_user_ids": [223],
                },
                "meeting_user/222": {"meeting_id": 1, "user_id": 22, "group_ids": [11]},
                "meeting_user/223": {"meeting_id": 1, "user_id": 23, "group_ids": [11]},
                "group/11": {"meeting_id": 1, "meeting_user_ids": [222, 223]},
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 22,
                "meeting_id": 1,
                "vote_delegated_to_id": 223,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/222",
            {
                "user_id": 22,
                "meeting_id": 1,
                "vote_delegated_to_id": 223,
            },
        )
        self.assert_model_exists(
            "meeting_user/223",
            {
                "user_id": 23,
                "meeting_id": 1,
                "vote_delegations_from_ids": [222],
            },
        )

        response = self.request(
            "user.update",
            {
                "id": 22,
                "meeting_id": 1,
                "vote_delegated_to_id": None,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/222",
            {
                "user_id": 22,
                "meeting_id": 1,
                "vote_delegated_to_id": None,
            },
        )
        self.assert_model_exists(
            "meeting_user/223",
            {
                "user_id": 23,
                "meeting_id": 1,
                "vote_delegations_from_ids": [],
            },
        )

    def test_update_vote_weight(self) -> None:
        self.set_models(
            {
                "user/111": {"username": "username_srtgb123"},
                "meeting/1": {
                    "name": "test_meeting_1",
                    "is_active_in_organization_id": 1,
                },
            }
        )
        response = self.request(
            "user.update", {"id": 111, "vote_weight": "2.000000", "meeting_id": 1}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111", {"username": "username_srtgb123", "meeting_user_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": 1,
                "user_id": 111,
                "vote_weight": "2.000000",
            },
        )

    def test_update_prevent_zero_vote_weight(self) -> None:
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                    "default_vote_weight": "1.000000",
                },
                "meeting/1": {
                    "name": "test_meeting_1",
                    "is_active_in_organization_id": 1,
                },
            }
        )
        response = self.request(
            "user.update",
            {"id": 111, "default_vote_weight": "0.000000", "meeting_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("user/111", {"default_vote_weight": "1.000000"})

    def test_update_self_vote_delegation(self) -> None:
        self.set_models(
            {
                "user/111": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "meeting_user/11": {"meeting_id": 1, "user_id": 111},
                "meeting/1": {
                    "name": "test_meeting_1",
                    "is_active_in_organization_id": 1,
                },
            }
        )
        response = self.request(
            "user.update", {"id": 111, "vote_delegated_to_id": 11, "meeting_id": 1}
        )
        self.assert_status_code(response, 400)
        assert (
            "User 111 can't delegate the vote to himself." in response.json["message"]
        )

    def test_update_self_vote_delegation_2(self) -> None:
        self.set_models(
            {
                "user/111": {"username": "username_srtgb123", "meeting_user_ids": [11]},
                "meeting_user/11": {"meeting_id": 1, "user_id": 111},
                "meeting/1": {
                    "name": "test_meeting_1",
                    "is_active_in_organization_id": 1,
                },
            }
        )
        response = self.request(
            "user.update",
            {"id": 111, "vote_delegations_from_ids": [11], "meeting_id": 1},
        )
        self.assert_status_code(response, 400)
        assert (
            "User 111 can't delegate the vote to himself." in response.json["message"]
        )

    def test_committee_manager_without_committee_ids(self) -> None:
        """Giving committee management level requires committee_ids"""
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                    "meeting_user_ids": [1111],
                    "meeting_ids": [60],
                },
                "meeting_user/1111": {
                    "meeting_id": 60,
                    "user_id": 111,
                    "group_ids": [600],
                },
                "committee/60": {
                    "name": "c60",
                    "meeting_ids": [60],
                    "user_ids": [111],
                },
                "committee/61": {"name": "c61"},
                "meeting/60": {
                    "user_ids": [111],
                    "group_ids": [600],
                    "committee_id": 60,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [1111],
                },
                "group/600": {"meeting_user_ids": [1111], "meeting_id": 60},
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "usersname",
                "committee_management_ids": [60, 61],
                "meeting_id": 60,
                "group_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "meeting_ids": [],
                "meeting_user_ids": [1111],
                "committee_management_ids": [60, 61],
                "committee_ids": [60, 61],
            },
        )
        self.assert_model_exists(
            "meeting_user/1111", {"group_ids": [], "meta_deleted": False}
        )
        self.assert_history_information(
            "user/111",
            [
                "Participant removed from group {} in meeting {}",
                "group/600",
                "meeting/60",
                "Personal data changed",
                "Committee management changed",
            ],
        )

    def test_committee_manager_remove_committee_ids(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "C1", "user_ids": [111]},
                "user/111": {
                    "committee_ids": [1],
                    "committee_management_ids": [1],
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_management_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111", {"committee_management_ids": [], "committee_ids": []}
        )
        self.assert_model_exists("committee/1", {"user_ids": []})

    def test_committee_manager_add_and_remove_both(self) -> None:
        """test with 2 actions in 2 transaction"""
        self.set_models(
            {
                "committee/1": {
                    "name": "remove user",
                    "user_ids": [123],
                    "meeting_ids": [11],
                },
                "committee/2": {
                    "name": "remove cml from_user",
                    "user_ids": [123],
                    "meeting_ids": [22],
                },
                "committee/3": {"name": "add user", "meeting_ids": [33]},
                "committee/4": {"name": "add user with cml"},
                "meeting/11": {
                    "user_ids": [123],
                    "group_ids": [111],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [111, 112],
                },
                "meeting/22": {
                    "user_ids": [123],
                    "group_ids": [222],
                    "committee_id": 2,
                    "is_active_in_organization_id": 1,
                },
                "meeting/33": {
                    "user_ids": [],
                    "group_ids": [333],
                    "committee_id": 3,
                    "is_active_in_organization_id": 1,
                },
                "group/111": {"meeting_user_ids": [111], "meeting_id": 11},
                "group/222": {"meeting_user_ids": [112], "meeting_id": 22},
                "group/333": {"meeting_user_ids": [], "meeting_id": 33},
                "user/123": {
                    "meeting_ids": [11, 22],
                    "committee_ids": [1, 2],
                    "committee_management_ids": [1, 2],
                    "meeting_user_ids": [111, 112],
                },
                "meeting_user/111": {
                    "meeting_id": 11,
                    "user_id": 123,
                    "group_ids": [111],
                },
                "meeting_user/112": {
                    "meeting_id": 22,
                    "user_id": 123,
                    "group_ids": [222],
                },
            }
        )

        response = self.request_json(
            [
                {
                    "action": "user.update",
                    "data": [
                        {
                            "id": 123,
                            "committee_management_ids": [4],
                            "meeting_id": 33,
                            "group_ids": [333],
                        }
                    ],
                },
                {
                    "action": "user.update",
                    "data": [
                        {
                            "id": 123,
                            "meeting_id": 11,
                            "group_ids": [],
                        }
                    ],
                },
            ],
            atomic=False,
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/123",
            {
                "committee_management_ids": [4],
                "meeting_ids": [22, 33],
                "committee_ids": [2, 3, 4],
                "meeting_user_ids": [111, 112, 113],
            },
        )
        self.assert_model_exists("committee/1", {"user_ids": []})
        self.assert_model_exists("committee/2", {"user_ids": [123]})
        self.assert_model_exists("committee/3", {"user_ids": [123]})
        self.assert_model_exists("committee/4", {"user_ids": [123]})
        self.assert_model_exists("meeting/11", {"user_ids": []})
        self.assert_model_exists("meeting/22", {"user_ids": [123]})
        self.assert_model_exists("meeting/33", {"user_ids": [123]})

    def test_update_broken_email(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
        )
        response = self.request("user.update", {"id": 111, "email": "broken@@"})
        self.assert_status_code(response, 400)
        assert "email must be valid email." in response.json["message"]

    def test_wrong_id(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
        )
        response = self.request(
            "user.update", {"id": 112, "username": "username_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model 'user/112' does not exist.",
            response.json["message"],
        )
        model = self.get_model("user/111")
        assert model.get("username") == "username_srtgb123"

    def test_username_already_given(self) -> None:
        self.create_model("user/222")
        response = self.request("user.update", {"id": 222, "username": "admin"})
        self.assert_status_code(response, 400)
        self.assertIn(
            "A user with the username admin already exists.", response.json["message"]
        )

    def test_member_number_already_given(self) -> None:
        self.create_model("user/221", {"member_number": "abcdefghij"})
        self.create_model("user/222", {"member_number": "klmnopqrst"})
        response = self.request(
            "user.update", {"id": 222, "member_number": "abcdefghij"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A user with the member_number abcdefghij already exists.",
            response.json["message"],
        )

    def test_clear_member_number(self) -> None:
        self.create_model("user/222", {"member_number": "klmnopqrst"})
        response = self.request("user.update", {"id": 222, "member_number": None})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/222", {"member_number": None})

    def test_same_username(self) -> None:
        response = self.request("user.update", {"id": 1, "username": "admin"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"username": "admin"})

    def test_update_check_pronoun_too_long(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
        )
        response = self.request(
            "user.update", {"id": 111, "pronoun": "123456789012345678901234567890123"}
        )
        self.assert_status_code(response, 400)
        assert (
            "data.pronoun must be shorter than or equal to 32 characters"
            in response.json["message"]
        )

    def test_perm_nothing(self) -> None:
        self.permission_setup()
        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "username_Neu",
                "meeting_id": 1,
                "vote_weight": "1.000000",
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_update for meeting 1",
            response.json["message"],
        )

    def test_perm_auth_error(self) -> None:
        self.permission_setup()
        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "username_Neu",
                "meeting_id": 1,
                "vote_weight": "1.000000",
                "group_ids": [1],
            },
            anonymous=True,
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Anonymous is not allowed to execute user.update",
            response.json["message"],
        )

    def test_perm_superadmin(self) -> None:
        """
        SUPERADMIN may set fields of all groups and may set an other user as SUPERADMIN, too.
        The SUPERADMIN don't need to belong to a meeting in any way to change data!
        """
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )
        self.set_models(
            {"user/111": {"username": "User111"}},
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "username_new",
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "meeting_id": 1,
                "vote_weight": "1.000000",
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "username_new",
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "meeting_user_ids": [2],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "vote_weight": "1.000000",
                "group_ids": [1],
            },
        )

    def test_perm_superadmin_withdraw_own_right(self) -> None:
        """
        SUPERADMIN may not withdraw his own OML right "superadmin",
        see Issue1350
        """
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )

        response = self.request(
            "user.update",
            {
                "id": self.user_id,
                # "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
                "organization_management_level": None,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A user is not allowed to withdraw his own 'superadmin'-Organization-Management-Level.",
            response.json["message"],
        )

    def test_perm_superadmin_self_setting_inactive(self) -> None:
        """
        SUPERADMIN may not set himself inactive,
        see Issue1350
        """
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )

        response = self.request(
            "user.update",
            {
                "id": self.user_id,
                "is_active": False,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A superadmin is not allowed to set himself inactive.",
            response.json["message"],
        )

    def test_perm_group_A_oml_manage_user(self) -> None:
        """May update group A fields on organsisation scope, because belongs to 2 meetings in 2 committees, requiring OML level permission"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )
        self.set_user_groups(111, [1, 6])
        self.set_models(
            {"organization/1": {"genders": ["male", "female", "diverse", "non-binary"]}}
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new_username",
                "title": "new title",
                "first_name": "new first_name",
                "last_name": "new last_name",
                "is_active": True,
                "is_physical_person": True,
                "default_password": "new default_password",
                "gender": "female",
                "email": "info@openslides.com ",  # space intentionally, will be stripped
                "default_vote_weight": "1.234000",
                "can_change_own_password": False,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "new_username",
                "title": "new title",
                "first_name": "new first_name",
                "last_name": "new last_name",
                "is_active": True,
                "is_physical_person": True,
                "default_password": "new default_password",
                "gender": "female",
                "email": "info@openslides.com",
                "default_vote_weight": "1.234000",
                "can_change_own_password": False,
            },
        )

    def test_perm_group_A_cml_manage_user(self) -> None:
        """May update group A fields on committee scope. User belongs to 1 meeting in 1 committee"""
        self.permission_setup()
        self.set_committee_management_level([60], self.user_id)
        self.set_user_groups(111, [1])
        self.set_models({"user/111": {"committee_ids": [60]}})

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new_username",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "new_username",
                "meeting_ids": [1],
                "committee_ids": [60],
            },
        )

    def test_perm_group_A_cml_manage_user_archived_meeting_in_other_committee(
        self,
    ) -> None:
        """
        May update group A fields on committee scope. User belongs to 1 meeting in 1 committee
        User is member of an archived meeting in an other committee, but this doesn't may affect the result.
        """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60], self.user_id)
        self.set_user_groups(111, [1, 4])
        self.set_models(
            {
                "user/111": {"committee_ids": [60]},
                "meeting/4": {"is_active_in_organization_id": None},
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new_username",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "new_username",
                "committee_ids": [60],
            },
        )
        user111 = self.get_model("user/111")
        self.assertCountEqual(user111["meeting_ids"], [1, 4])

    def test_perm_group_A_meeting_manage_user(self) -> None:
        """May update group A fields on meeting scope. User belongs to 1 meeting without being part of a committee"""
        self.permission_setup()
        self.set_user_groups(self.user_id, [2])
        self.set_user_groups(111, [1])

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new_username",
                "pronoun": "pronoun",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "new_username",
                "pronoun": "pronoun",
                "meeting_ids": [1],
                "committee_ids": None,
            },
        )

    def test_perm_group_A_meeting_manage_user_archived_meeting(self) -> None:
        self.perm_group_A_meeting_manage_user_archived_meeting(
            Permissions.User.CAN_UPDATE
        )

    def test_perm_group_A_meeting_manage_user_archived_meeting_with_parent_permission(
        self,
    ) -> None:
        self.perm_group_A_meeting_manage_user_archived_meeting(
            Permissions.User.CAN_MANAGE
        )

    def perm_group_A_meeting_manage_user_archived_meeting(
        self, permission: Permission
    ) -> None:
        """
        May update group A fields on meeting scope. User belongs to 1 meeting without being part of a committee
        User is member of an archived meeting in an other committee, but this doesn't may affect the result.
        """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_user_groups(self.user_id, [2])
        self.set_user_groups(111, [1, 4])
        self.set_models(
            {
                "meeting/4": {"is_active_in_organization_id": None},
                "group/2": {"permissions": [permission]},
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new_username",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "new_username",
                "committee_ids": None,
            },
        )
        user111 = self.get_model("user/111")
        self.assertCountEqual(user111["meeting_ids"], [1, 4])

    def test_perm_group_A_no_permission(self) -> None:
        """May not update group A fields on organization scope, although having both committee permissions"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60, 63], 111)
        self.set_user_groups(111, [1, 6])
        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new_username",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
            response.json["message"],
        )

    def test_perm_group_A_locked_meeting(self) -> None:
        """May update group A fields on a user who is in a locked meeting"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )
        self.set_user_groups(111, [1, 6])
        self.set_models(
            {
                "organization/1": {
                    "genders": ["male", "female", "diverse", "non-binary"]
                },
                "meeting/4": {"locked_from_inside": True},
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new_username",
                "title": "new title",
                "first_name": "new first_name",
                "last_name": "new last_name",
                "is_active": True,
                "is_physical_person": True,
                "default_password": "new default_password",
                "gender": "female",
                "email": "info@openslides.com ",  # space intentionally, will be stripped
                "default_vote_weight": "1.234000",
                "can_change_own_password": False,
            },
        )
        self.assert_status_code(response, 200)

    def test_perm_group_F_default_password_for_superadmin_no_permission(self) -> None:
        """May not update the default_password for superadmin without having permission oml.SUPERADMIN"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, 111
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "default_password": "new_one",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Your organization management level is not high enough to change a user with a Level of superadmin!",
            response.json["message"],
        )

    def test_perm_group_B_user_can_update(self) -> None:
        """update group B fields for 2 meetings with simple user.can_update permissions"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_organization_management_level(None, self.user_id)
        self.set_models(
            {
                "user/5": {"username": "user5"},
                "user/6": {"username": "user6"},
                "meeting/1": {
                    "structure_level_ids": [31],
                },
                "structure_level/31": {"meeting_id": 1},
            }
        )
        self.set_user_groups(
            self.user_id, [2, 5]
        )  # Admin groups of meeting/1 and meeting/4
        self.set_user_groups(5, [1, 6])
        self.set_user_groups(6, [1, 6])
        self.set_user_groups(111, [1, 6])
        self.set_models(
            {
                "meeting_user/8": {
                    "user_id": 111,
                    "meeting_id": 4,
                    "number": "number1 in 4",
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "number": "number1",
                "structure_level_ids": [31],
                "vote_weight": "12.002345",
                "about_me": "about me 1",
                "comment": "comment for meeting/1",
                "vote_delegations_from_ids": [3, 5],  # from user/5 and 6 in meeting/1
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "User111",
                "meeting_ids": [1, 4],
            },
        )
        self.assert_model_exists(
            "meeting_user/7",
            {
                "user_id": 111,
                "meeting_id": 1,
                "vote_delegations_from_ids": [3, 5],
                "number": "number1",
                "structure_level_ids": [31],
                "vote_weight": "12.002345",
                "about_me": "about me 1",
                "comment": "comment for meeting/1",
            },
        )
        self.assert_model_exists(
            "meeting_user/8",
            {"user_id": 111, "meeting_id": 4, "number": "number1 in 4"},
        )
        self.assert_model_exists(
            "meeting_user/3", {"user_id": 5, "meeting_id": 1, "vote_delegated_to_id": 7}
        )
        self.assert_model_exists(
            "meeting_user/5", {"user_id": 6, "meeting_id": 1, "vote_delegated_to_id": 7}
        )

    def test_perm_group_B_user_can_update_no_permission(self) -> None:
        """Group B fields needs explicit user.can_update permission for meeting"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_organization_management_level(None, self.user_id)
        self.set_user_groups(
            self.user_id, [3, 6]
        )  # Empty groups of meeting/1 and meeting/4
        self.set_user_groups(111, [1, 4])  # Default groups of meeting/1 and meeting/4
        self.set_group_permissions(3, [Permissions.User.CAN_UPDATE])

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 4,
                "number": "number1 in 4",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_update for meeting 4",
            response.json["message"],
        )

    def test_perm_group_B_locked_meeting(self) -> None:
        """Group B fields needs explicit user.can_update permission for a locked meeting"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )
        self.set_user_groups(
            self.user_id, [3, 6]
        )  # Empty groups of meeting/1 and meeting/4
        self.set_user_groups(111, [1, 4])  # Default groups of meeting/1 and meeting/4
        self.set_group_permissions(3, [Permissions.User.CAN_UPDATE])
        self.set_models({"meeting/4": {"locked_from_inside": True}})

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 4,
                "number": "number1 in 4",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "TODO: fill in",
            response.json["message"],
        )

    def test_perm_group_C_oml_manager(self) -> None:
        """May update group C group_ids by OML permission"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111", {"meeting_user_ids": [2], "meeting_ids": [1]}
        )
        self.assert_model_exists("meeting_user/2", {"group_ids": [1], "user_id": 111})

    def test_perm_group_C_committee_manager(self) -> None:
        """May update group C group_ids by committee permission"""
        self.permission_setup()
        self.set_committee_management_level([60], self.user_id)

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/2",
            {"group_ids": [1], "user_id": 111},
        )

    def test_perm_group_C_user_can_update(self) -> None:
        """May update group C group_ids by user.can_update permission with admin group of all related meetings"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_user_groups(self.user_id, [2, 5])  # Admin-groups
        self.set_user_groups(111, [2, 3, 5, 6])
        self.set_models(
            {
                "meeting/4": {"committee_id": 60},
                "committee/60": {"meeting_ids": [1, 4]},
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111", {"meeting_ids": [1, 4], "meeting_user_ids": [3, 4]}
        )
        self.assert_model_exists("meeting_user/3", {"meeting_id": 1, "group_ids": [1]})
        self.assert_model_exists(
            "meeting_user/4", {"meeting_id": 4, "group_ids": [5, 6]}
        )

    def test_perm_group_C_no_permission(self) -> None:
        """May not update group C group_ids"""
        self.permission_setup()

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_update for meeting 1",
            response.json["message"],
        )

    def test_perm_group_C_locked_meeting(self) -> None:
        """May not update group C group_ids in locked_meetings"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )
        self.set_models({"meeting/1": {"locked_from_inside": True}})

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "TODO: fill in",
            response.json["message"],
        )

    def test_perm_group_C_locked_meeting_and_meeting_member(self) -> None:
        """May not update group C group_ids in a locked meeting without appropriate meeting-internal permission"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )
        self.set_user_groups(self.user_id, [1])
        self.set_models({"meeting/1": {"locked_from_inside": True}})

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "TODO: fill in",
            response.json["message"],
        )

    def test_perm_group_C_locked_meeting_cml(self) -> None:
        """Committee manager may not update group C group_ids if the meeting is locked"""
        self.permission_setup()
        self.set_committee_management_level([60], self.user_id)
        self.set_models({"meeting/1": {"locked_from_inside": True}})

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "TODO: fill in",
            response.json["message"],
        )

    def test_perm_group_C_locked_meeting_cml_and_meeting_member(self) -> None:
        """Meeting manager may not update group C group_ids, if the meeting is locked and he doesn't have the correct meeting-internal permissions"""
        self.permission_setup()
        self.set_committee_management_level([60], self.user_id)
        self.set_user_groups(self.user_id, [1])
        self.set_models({"meeting/1": {"locked_from_inside": True}})

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "TODO: fill in",
            response.json["message"],
        )

    def test_perm_group_C_locked_meeting_admin(self) -> None:
        """May update group C group_ids in a locked meeting as the meeting admin"""
        self.permission_setup()
        self.set_user_groups(self.user_id, [2])
        self.set_models({"meeting/1": {"locked_from_inside": True}})

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)

    def test_perm_group_C_locked_meeting_other_meeting(self) -> None:
        """
        May update group C group_ids for a non-locked meeting,
        even if the user is in another meeting, which is locked
        """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )
        self.set_user_groups(
            self.user_id, [3, 6]
        )  # Empty groups of meeting/1 and meeting/4
        self.set_user_groups(111, [1, 4])  # Default groups of meeting/1 and meeting/4
        self.set_group_permissions(3, [Permissions.User.CAN_UPDATE])
        self.set_models({"meeting/4": {"locked_from_inside": True}})

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)

    def test_perm_group_C_special_1(self) -> None:
        """group C group_ids adding meeting in same committee with committee permission"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60], self.user_id)
        self.set_models(
            {
                "committee/60": {"meeting_ids": [1, 4]},
                "meeting/4": {"committee_id": 60},
                "user/111": {"meeting_user_ids": [2], "meeting_ids": [1]},
                "meeting_user/2": {"meeting_id": 1, "user_id": 111, "group_ids": [1]},
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 4,
                "group_ids": [5],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {"meeting_ids": [1, 4], "meeting_user_ids": [2, 3]},
        )
        self.assert_model_exists(
            "meeting_user/3",
            {"meeting_id": 4, "user_id": 111, "group_ids": [5]},
        )

    def test_perm_group_C_special_2_no_permission(self) -> None:
        """group C group_ids adding meeting in other committee
        with committee permission for both. Error 403, because touching
        2 committees requires OML permission
        """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60], self.user_id)
        self.set_models(
            {
                "user/111": {"meeting_user_ids": [2], "meeting_ids": [1]},
                "meeting_user/2": {"meeting_id": 1, "user_id": 111, "group_ids": [1]},
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 4,
                "group_ids": [5],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_update for meeting 4",
            response.json["message"],
        )

    def test_perm_group_C_special_3_both_permissions(self) -> None:
        """group C group_ids adding meeting in same committee
        with meeting permission for both, which is allowed.
        """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_user_groups(self.user_id, [2, 5])  # Admin groups meeting/1 and 4
        self.set_models(
            {
                "committee/60": {"meeting_ids": [1, 4]},
                "meeting/4": {"committee_id": 60},
                "user/111": {
                    "meeting_ids": [1],
                    "meeting_user_ids": [3],
                },
                "meeting_user/3": {
                    "user_id": 111,
                    "meeting_id": 1,
                    "group_ids": [1],
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 4,
                "group_ids": [5],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {"meeting_ids": [1, 4], "meeting_user_ids": [3, 4]},
        )
        self.assert_model_exists(
            "meeting_user/4",
            {"meeting_id": 4, "user_id": 111, "group_ids": [5]},
        )

    def test_perm_group_D_permission_with_OML(self) -> None:
        """May update Group D committee fields with OML level permission"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_management_ids": [60],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "committee_management_ids": [60],
                "committee_ids": [60],
            },
        )

    def test_perm_group_D_permission_with_CML(self) -> None:
        """May update Group D committee fields with CML permission for all committees"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60, 63], self.user_id)

        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_management_ids": [60, 63],
            },
        )
        self.assert_status_code(response, 200)
        user111 = self.assert_model_exists("user/111")
        self.assertCountEqual(user111.get("committee_management_ids", []), [60, 63])
        self.assertCountEqual(user111.get("committee_ids", []), [60, 63])

    def test_perm_group_D_no_permission(self) -> None:
        """May not update Group D committee fields, because of missing CML permission for one committee"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60], self.user_id)
        self.set_committee_management_level([60], 111)

        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_management_ids": [63],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee 63",
            response.json["message"],
        )

    def test_perm_group_D_locked_meeting(self) -> None:
        """May update Group D committee fields if there is a locked meeting"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60], self.user_id)
        self.set_committee_management_level([60], 111)
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )
        self.set_models({"meeting/4": {"locked_from_inside": True}})

        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_management_ids": [63],
            },
        )
        self.assert_status_code(response, 200)

    def test_perm_group_D_permission_with_CML_and_untouched_committee(
        self,
    ) -> None:
        """
        May update Group D committee fields with CML permission for all committees.
        committee 63 without permission is untouched in payload and doesn't matter.
        In committee_ids it seems touched, but remains unchanged in committe_ids
        """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60], self.user_id)
        self.set_committee_management_level([63], 111)

        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_management_ids": [60, 63],
            },
        )
        self.assert_status_code(response, 200)
        user111 = self.assert_model_exists("user/111")
        self.assertCountEqual(user111.get("committee_ids", []), [60, 63])
        self.assertCountEqual(user111.get("committee_management_ids", []), [60, 63])

    def test_perm_group_D_permission_with_CML_missing_permission(
        self,
    ) -> None:
        """
        Misses committee 63 permission, because the request try to remove it from committee_ids
        """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60], self.user_id)
        self.set_committee_management_level([63], 111)

        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_management_ids": [60],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee 63",
            response.json["message"],
        )

    def test_perm_group_E_OML_high_enough(self) -> None:
        """OML level to set is sufficient"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
            },
        )
        self.assert_history_information(
            "user/111", ["Organization Management Level changed"]
        )

    def test_perm_group_E_OML_not_high_enough(self) -> None:
        """OML level to set is higher than level of request user"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Your organization management level is not high enough to set a Level of can_manage_organization.",
            response.json["message"],
        )

    def test_perm_group_E_locked_meeting(self) -> None:
        """May edit OML, even if the user is in a locked meeting"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )
        self.set_models({"meeting/1": {"locked_from_inside": True}})

        response = self.request(
            "user.update",
            {
                "id": 111,
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            },
        )
        self.assert_status_code(response, 200)

    def test_perm_group_F_demo_user_permission(self) -> None:
        """demo_user only editable by Superadmin"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "is_demo_user": True,
            },
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "is_demo_user": True,
            },
        )

    def test_perm_group_F_locked_meeting(self) -> None:
        """demo_user is editable by Superadmin, even on users in locked meetings"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )
        self.set_models({"meeting/1": {"locked_from_inside": True}})

        response = self.request(
            "user.update",
            {
                "id": 111,
                "is_demo_user": True,
            },
        )

        self.assert_status_code(response, 200)

    def test_no_perm_group_H_internal_saml_id(self) -> None:
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "saml_id": "test saml id",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The field 'saml_id' can only be used in internal action calls",
            response.json["message"],
        )

    def test_perm_group_F_demo_user_no_permission(self) -> None:
        """demo_user only editable by Superadmin"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, self.user_id
        )
        self.update_model(
            f"user/{self.user_id}",
            {
                "committee_management_ids": [60],
            },
        )
        self.set_user_groups(self.user_id, [2, 3])  # All including admin group

        response = self.request(
            "user.update",
            {
                "id": 111,
                "is_demo_user": True,
            },
        )

        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing OrganizationManagementLevel: superadmin",
            response.json["message"],
        )

    def test_update_forbidden_username(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
        )
        response = self.request("user.update", {"id": 111, "username": "   "})
        self.assert_status_code(response, 400)
        assert "This username is forbidden." in response.json["message"]
        model = self.get_model("user/111")
        assert model.get("username") == "username_srtgb123"

    def test_update_username_with_spaces(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
        )
        response = self.request("user.update", {"id": 111, "username": "test name"})
        self.assert_status_code(response, 400)
        assert "Username may not contain spaces" in response.json["message"]
        model = self.get_model("user/111")
        assert model.get("username") == "username_srtgb123"

    def test_update_gender(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
        )
        self.set_models(
            {"organization/1": {"genders": ["male", "female", "diverse", "non-binary"]}}
        )
        response = self.request("user.update", {"id": 111, "gender": "test"})
        self.assert_status_code(response, 400)
        assert (
            "Gender 'test' is not in the allowed gender list."
            in response.json["message"]
        )

        response = self.request("user.update", {"id": 111, "gender": "diverse"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/111", {"gender": "diverse"})

        response = self.request("user.update", {"id": 111, "gender": "non-binary"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/111", {"gender": "non-binary"})

    def test_update_not_in_update_is_present_in_meeting_ids(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username111"},
        )
        response = self.request(
            "user.update", {"id": 111, "is_present_in_meeting_ids": [1]}
        )
        self.assert_status_code(response, 400)
        assert (
            "data must not contain {'is_present_in_meeting_ids'} properties"
            in response.json["message"]
        )

    def test_update_change_group(self) -> None:
        self.create_meeting()
        user_id = self.create_user_for_meeting(1)
        # assert user is already in meeting
        self.assert_model_exists("meeting/1", {"user_ids": [user_id]})
        # change user group from 1 (default_group) to 2 in meeting 1
        response = self.request(
            "user.update", {"id": user_id, "meeting_id": 1, "group_ids": [2]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/1", {"user_id": user_id, "group_ids": [2]}
        )
        self.assert_model_exists("meeting/1", {"user_ids": [user_id]})

    def test_update_change_superadmin(self) -> None:
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, self.user_id
        )
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, 111
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "first_name": "Testy",
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "Your organization management level is not high enough to change a user with a Level of superadmin!"
            in response.json["message"]
        )

    def test_update_demote_superadmin(self) -> None:
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, self.user_id
        )
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, 111
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "Your organization management level is not high enough to change a user with a Level of superadmin!"
            in response.json["message"]
        )

    def test_update_change_superadmin_meeting_specific(self) -> None:
        self.permission_setup()
        self.set_user_groups(self.user_id, [2])
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, self.user_id
        )
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, 111
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "comment": "test",
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/111", {"meeting_user_ids": [2]})
        self.assert_model_exists(
            "meeting_user/2", {"comment": "test", "group_ids": [1]}
        )

    def test_update_hit_user_limit(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"limit_of_users": 3},
                "user/2": {"is_active": True},
                "user/3": {"is_active": True},
                "user/4": {"is_active": False},
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 4,
                "is_active": True,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "The number of active users cannot exceed the limit of users."
            == response.json["message"]
        )

    def test_update_user_limit_okay(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"limit_of_users": 4},
                "user/2": {"is_active": True},
                "user/3": {"is_active": True},
                "user/4": {"is_active": False},
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 4,
                "is_active": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/4", {"is_active": True})
        self.assert_history_information("user/4", ["Set active"])

    def test_update_negative_default_vote_weight(self) -> None:
        self.create_model("user/111", {"username": "user111"})
        response = self.request(
            "user.update", {"id": 111, "default_vote_weight": "-1.123000"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "default_vote_weight must be bigger than or equal to 0.",
            response.json["message"],
        )

    def test_update_negative_vote_weight(self) -> None:
        self.set_models(
            {
                "user/111": {"username": "user111"},
                "meeting/110": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 110,
                "vote_weight": "-6.000000",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "vote_weight must be bigger than or equal to 0.",
            response.json["message"],
        )

    def test_update_committee_membership_complex(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "name": "C1",
                    "meeting_ids": [1],
                    "user_ids": [222, 223],
                },
                "committee/2": {
                    "name": "C2",
                    "meeting_ids": [2],
                    "user_ids": [222],
                },
                "committee/3": {
                    "name": "C3",
                    "meeting_ids": [3],
                    "user_ids": [222, 223],
                },
                "meeting/1": {
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "user_ids": [222, 223],
                    "meeting_user_ids": [1, 11],
                },
                "meeting/2": {
                    "committee_id": 2,
                    "is_active_in_organization_id": 1,
                    "user_ids": [222],
                    "meeting_user_ids": [2],
                },
                "meeting/3": {
                    "committee_id": 3,
                    "is_active_in_organization_id": 1,
                    "user_ids": [222, 223],
                    "meeting_user_ids": [3, 12],
                },
                "group/11": {"meeting_id": 1, "meeting_user_ids": [1, 11]},
                "group/22": {"meeting_id": 2, "meeting_user_ids": [2]},
                "group/33": {"meeting_id": 3, "meeting_user_ids": [3, 12]},
                "user/222": {
                    "meeting_ids": [1, 2, 3],
                    "committee_ids": [1, 2, 3],
                    "meeting_user_ids": [1, 2, 3],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 222,
                    "group_ids": [11],
                },
                "meeting_user/2": {
                    "meeting_id": 2,
                    "user_id": 222,
                    "group_ids": [22],
                },
                "meeting_user/3": {
                    "meeting_id": 3,
                    "user_id": 222,
                    "group_ids": [33],
                },
                "user/223": {
                    "meeting_ids": [1, 3],
                    "committee_ids": [1, 3],
                    "committee_management_ids": [1, 3],
                    "meeting_user_ids": [11, 12],
                },
                "meeting_user/11": {
                    "meeting_id": 1,
                    "user_id": 223,
                    "group_ids": [11],
                },
                "meeting_user/12": {
                    "meeting_id": 3,
                    "user_id": 223,
                    "group_ids": [33],
                },
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 223,
                "committee_management_ids": [2, 3],
                "meeting_id": 2,
                "group_ids": [22],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/223",
            {
                "committee_management_ids": [2, 3],
                "meeting_ids": [1, 3, 2],
                "committee_ids": [1, 3, 2],
                "meeting_user_ids": [11, 12, 13],
            },
        )
        self.assert_model_exists(
            "meeting_user/13", {"meeting_id": 2, "user_id": 223, "group_ids": [22]}
        )

        self.assert_model_exists("group/11", {"meeting_user_ids": [1, 11]})
        self.assert_model_exists("group/22", {"meeting_user_ids": [2, 13]})
        self.assert_model_exists("group/33", {"meeting_user_ids": [3, 12]})
        self.assert_model_exists(
            "meeting/1", {"user_ids": [222, 223], "meeting_user_ids": [1, 11]}
        )
        self.assert_model_exists(
            "meeting/2", {"user_ids": [222, 223], "meeting_user_ids": [2, 13]}
        )
        self.assert_model_exists(
            "meeting/3", {"user_ids": [222, 223], "meeting_user_ids": [3, 12]}
        )
        self.assert_model_exists("committee/1", {"user_ids": [222, 223]})
        self.assert_model_exists("committee/2", {"user_ids": [222, 223]})
        self.assert_model_exists("committee/3", {"user_ids": [222, 223]})

    def test_update_empty_default_vote_weight(self) -> None:
        response = self.request(
            "user.update",
            {
                "id": 1,
                "default_vote_weight": None,
            },
        )
        self.assert_status_code(response, 200)
        user = self.get_model("user/1")
        assert "default_vote_weight" not in user

    def test_update_strip_space(self) -> None:
        response = self.request(
            "user.update",
            {
                "id": 1,
                "first_name": " first name test ",
                "last_name": " last name test ",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "first_name": "first name test",
                "last_name": "last name test",
            },
        )

    def test_update_no_OML_set(self) -> None:
        self.permission_setup()
        self.set_user_groups(self.user_id, [2])

        response = self.request(
            "user.update",
            {
                "id": self.user_id,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)

    def test_update_history_user_updated_in_meeting(self) -> None:
        self.set_models(
            {
                "user/111": {"username": "user111", "meeting_user_ids": [10]},
                "meeting/110": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [10],
                },
                "meeting_user/10": {
                    "user_id": 111,
                    "meeting_id": 110,
                },
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 110,
                "vote_weight": "2.000000",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            "user/111", ["Participant data updated in meeting {}", "meeting/110"]
        )

    def test_update_history_add_group(self) -> None:
        self.create_meeting()
        self.create_meeting(base=10)
        user_id = self.create_user(username="test")
        self.set_user_groups(user_id, [2, 10, 11, 12])

        response = self.request(
            "user.update",
            {
                "id": user_id,
                "meeting_id": 1,
                "group_ids": [2, 3],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            f"user/{user_id}",
            ["Participant added to group {} in meeting {}", "group/3", "meeting/1"],
        )

    def test_update_history_add_group_to_default_group(self) -> None:
        self.create_meeting()
        self.create_meeting(base=10)
        user_id = self.create_user(username="test")
        self.set_user_groups(user_id, [1, 10, 11, 12])

        response = self.request(
            "user.update",
            {
                "id": user_id,
                "meeting_id": 1,
                "group_ids": [2],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            f"user/{user_id}",
            ["Participant added to group {} in meeting {}", "group/2", "meeting/1"],
        )

    def test_update_history_add_multiple_groups(self) -> None:
        self.create_meeting()
        self.create_meeting(base=10)
        user_id = self.create_user(username="test")
        self.set_user_groups(user_id, [1, 10, 11, 12])

        response = self.request(
            "user.update",
            {
                "id": user_id,
                "meeting_id": 1,
                "group_ids": [2, 3],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            f"user/{user_id}",
            ["Participant added to multiple groups in meeting {}", "meeting/1"],
        )

    def test_update_history_add_multiple_groups_with_default_group(self) -> None:
        self.create_meeting()
        user_id = self.create_user(username="test")
        self.set_models(
            {
                f"user/{user_id}": {
                    "meeting_user_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": user_id,
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": user_id,
                "meeting_id": 1,
                "group_ids": [1, 2],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            f"user/{user_id}",
            ["Participant added to group {} in meeting {}", "group/2", "meeting/1"],
        )

    def test_update_history_remove_group(self) -> None:
        self.create_meeting()
        user_id = self.create_user_for_meeting(1)
        self.assert_model_exists(
            f"user/{user_id}", {"meeting_ids": [1], "meeting_user_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/1", {"user_id": user_id, "meeting_id": 1, "group_ids": [1]}
        )

        response = self.request(
            "user.update",
            {
                "id": user_id,
                "meeting_id": 1,
                "group_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            f"user/{user_id}",
            ["Participant removed from meeting {}", "meeting/1"],
        )

    def test_update_fields_with_equal_value_no_history(self) -> None:
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                    "title": "test",
                    "is_active": True,
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                    "committee_management_ids": [78],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 111,
                    "meeting_id": 1,
                    "structure_level_ids": [31],
                    "group_ids": [1],
                },
                "group/1": {"meeting_user_ids": [11], "meeting_id": 1},
                "meeting/1": {
                    "group_ids": [1],
                    "is_active_in_organization_id": 1,
                    "committee_id": 78,
                    "structure_level_ids": [31],
                },
                "structure_level/31": {
                    "meeting_id": 1,
                },
                "committee/78": {"meeting_ids": [1]},
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 111,
                "title": "test",
                "is_active": True,
                "meeting_id": 1,
                "group_ids": [1],
                "structure_level_ids": [31],
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                "committee_management_ids": [78],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_history_information("user/111", None)

    def test_update_empty_cml_no_history(self) -> None:
        self.set_models(
            {
                "user/111": {
                    "committee_management_ids": [],
                },
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_management_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_history_information("user/111", None)

    def test_update_participant_data_with_existing_meetings(self) -> None:
        self.set_models(
            {
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "meeting/2": {"committee_id": 1, "is_active_in_organization_id": 1},
                "committee/1": {"meeting_ids": [1]},
                "user/222": {"meeting_user_ids": [42]},
                "meeting_user/42": {
                    "user_id": 222,
                    "meeting_id": 1,
                    "vote_weight": "1.000000",
                },
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 222,
                "meeting_id": 2,
                "vote_weight": "1.500000",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            "user/222",
            [
                "Participant added to meeting {}",
                "meeting/2",
            ],
        )

    def test_update_participant_data_in_multiple_meetings_with_existing_meetings(
        self,
    ) -> None:
        self.set_models(
            {
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "meeting/2": {"committee_id": 1, "is_active_in_organization_id": 1},
                "meeting/3": {"committee_id": 1, "is_active_in_organization_id": 1},
                "committee/1": {"meeting_ids": [1]},
                "user/222": {"meeting_user_ids": [42]},
                "meeting_user/42": {
                    "user_id": 222,
                    "meeting_id": 1,
                    "vote_weight": "1.000000",
                },
            }
        )
        response = self.request_multi(
            "user.update",
            [
                {
                    "id": 222,
                    "meeting_id": 2,
                    "vote_weight": "1.000000",
                },
                {
                    "id": 222,
                    "meeting_id": 3,
                    "vote_weight": "1.000000",
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            "user/222",
            [
                "Participant added to meeting {}",
                "meeting/2",
                "Participant added to meeting {}",
                "meeting/3",
            ],
        )

    def test_update_saml_id__can_change_own_password_error(self) -> None:
        self.create_model(
            "user/111",
            {"username": "srtgb123", "saml_id": "111"},
        )
        response = self.request(
            "user.update", {"id": 111, "can_change_own_password": True}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "user 111 is a Single Sign On user and may not set the local default_passwort or the right to change it locally.",
            response.json["message"],
        )

    def test_update_saml_id_default_password_error(self) -> None:
        self.create_model(
            "user/111",
            {"username": "srtgb123", "saml_id": "111"},
        )
        response = self.request(
            "user.update", {"id": 111, "default_password": "secret"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "user 111 is a Single Sign On user and may not set the local default_passwort or the right to change it locally.",
            response.json["message"],
        )

    def test_group_removal_with_speaker(self) -> None:
        self.set_models(
            {
                "user/1234": {
                    "username": "username_abcdefgh123",
                    "meeting_user_ids": [4444, 5555],
                },
                "meeting_user/4444": {
                    "meeting_id": 4,
                    "user_id": 1234,
                    "speaker_ids": [14, 24],
                    "group_ids": [42],
                },
                "meeting_user/5555": {
                    "meeting_id": 5,
                    "user_id": 1234,
                    "speaker_ids": [25],
                    "group_ids": [53],
                },
                "meeting/4": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [4444],
                    "committee_id": 1,
                },
                "meeting/5": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5555],
                    "committee_id": 1,
                },
                "committee/1": {"meeting_ids": [4, 5]},
                "speaker/14": {"meeting_user_id": 4444, "meeting_id": 4},
                "speaker/24": {
                    "meeting_user_id": 4444,
                    "meeting_id": 4,
                    "begin_time": 987654321,
                },
                "speaker/25": {"meeting_user_id": 5555, "meeting_id": 5},
                "group/42": {"meeting_id": 4, "meeting_user_ids": [4444]},
                "group/53": {"meeting_id": 5, "meeting_user_ids": [5555]},
            }
        )
        response = self.request(
            "user.update", {"id": 1234, "group_ids": [], "meeting_id": 4}
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1234",
            {
                "username": "username_abcdefgh123",
                "meeting_user_ids": [4444, 5555],
            },
        )
        self.assert_model_exists(
            "meeting_user/4444",
            {"group_ids": [], "speaker_ids": [24], "meta_deleted": False},
        )
        self.assert_model_exists(
            "meeting_user/5555",
            {"group_ids": [53], "speaker_ids": [25], "meta_deleted": False},
        )
        self.assert_model_exists(
            "speaker/24", {"meeting_user_id": 4444, "meeting_id": 4}
        )
        self.assert_model_exists(
            "speaker/25", {"meeting_user_id": 5555, "meeting_id": 5}
        )
        self.assert_model_deleted("speaker/14")

    def test_partial_group_removal_with_speaker(self) -> None:
        self.set_models(
            {
                "user/1234": {
                    "username": "username_abcdefgh123",
                    "meeting_user_ids": [4444],
                },
                "meeting_user/4444": {
                    "meeting_id": 4,
                    "user_id": 1234,
                    "speaker_ids": [14, 24],
                    "group_ids": [42, 43],
                },
                "meeting/4": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [4444],
                    "committee_id": 1,
                },
                "committee/1": {"meeting_ids": [4]},
                "speaker/14": {"meeting_user_id": 4444, "meeting_id": 4},
                "speaker/24": {
                    "meeting_user_id": 4444,
                    "meeting_id": 4,
                    "begin_time": 987654321,
                },
                "group/42": {"meeting_id": 4, "meeting_user_ids": [4444]},
                "group/43": {"meeting_id": 4, "meeting_user_ids": [4444]},
            }
        )
        response = self.request(
            "user.update", {"id": 1234, "group_ids": [43], "meeting_id": 4}
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1234",
            {
                "username": "username_abcdefgh123",
                "meeting_user_ids": [4444],
            },
        )
        self.assert_model_exists(
            "meeting_user/4444",
            {"group_ids": [43], "speaker_ids": [14, 24], "meta_deleted": False},
        )
        self.assert_model_exists(
            "speaker/24", {"meeting_user_id": 4444, "meeting_id": 4}
        )
        self.assert_model_exists(
            "speaker/14", {"meeting_user_id": 4444, "meeting_id": 4}
        )

    def test_update_with_internal_fields(self) -> None:
        self.create_meeting()
        self.create_user("dummy2", [1])
        self.create_user("dummy3", [1])
        self.set_models(
            {
                "user/1": {
                    "poll_candidate_ids": [1],
                    "option_ids": [1],
                    "vote_ids": [1, 2],
                },
                "user/2": {"delegated_vote_ids": [2]},
                "meeting/1": {
                    "poll_ids": [1],
                    "option_ids": [1, 2],
                    "poll_candidate_list_ids": [1],
                    "poll_candidate_ids": [1],
                    "vote_ids": [1, 2],
                },
                "poll/1": {"meeting_id": 1, "option_ids": [1, 2]},
                "option/1": {
                    "meeting_id": 1,
                    "vote_ids": [1],
                    "content_object_id": "user/1",
                },
                "option/2": {
                    "meeting_id": 1,
                    "vote_ids": [2],
                    "content_object_id": "poll_candidate_list/1",
                },
                "poll_candidate_list/1": {
                    "meeting_id": 1,
                    "option_id": 2,
                    "poll_candidate_ids": [1],
                },
                "poll_candidate/1": {
                    "poll_candidate_list_id": 1,
                    "meeting_id": 1,
                    "user_id": 1,
                    "weight": 3,
                },
                "vote/1": {"meeting_id": 1, "option_id": 1, "user_id": 1},
                "vote/2": {
                    "meeting_id": 1,
                    "option_id": 2,
                    "user_id": 1,
                    "delegated_user_id": 2,
                },
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 3,
                "is_present_in_meeting_ids": [1],
                "option_ids": [1],
                "poll_candidate_ids": [1],
                "poll_voted_ids": [1],
                "vote_ids": [1],
                "delegated_vote_ids": [2],
            },
            internal=True,
        )
        self.assert_status_code(response, 200)
        expected: dict[str, dict[str, Any]] = {
            "user/3": {
                "is_present_in_meeting_ids": [1],
                "option_ids": [1],
                "poll_candidate_ids": [1],
                "poll_voted_ids": [1],
                "vote_ids": [1],
                "delegated_vote_ids": [2],
            },
            "meeting/1": {
                "present_user_ids": [3],
            },
            "poll/1": {"voted_ids": [3]},
            "option/1": {"content_object_id": "user/3"},
            "poll_candidate/1": {
                "user_id": 3,
            },
            "vote/1": {"user_id": 3},
            "vote/2": {"delegated_user_id": 3},
        }
        for fqid, model in expected.items():
            self.assert_model_exists(fqid, model)

    def test_update_with_internal_fields_error(self) -> None:
        self.create_meeting()
        self.create_user("dummy2", [1])
        self.create_user("dummy3", [1])
        response = self.request(
            "user.update",
            {
                "id": 3,
                "is_present_in_meeting_ids": [1],
                "option_ids": [1],
                "poll_candidate_ids": [1],
                "poll_voted_ids": [1],
                "vote_ids": [1],
                "delegated_vote_ids": [2],
            },
            internal=False,
        )
        self.assert_status_code(response, 400)
        message: str = response.json["message"]
        assert message.startswith("data must not contain {")
        assert message.endswith("} properties")
        for field in [
            "'is_present_in_meeting_ids'",
            "'option_ids'",
            "'poll_candidate_ids'",
            "'poll_voted_ids'",
            "'vote_ids'",
            "'delegated_vote_ids'",
        ]:
            self.assertIn(field, message)
