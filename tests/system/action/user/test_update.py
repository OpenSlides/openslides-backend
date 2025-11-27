from typing import Any, Literal

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

    def two_meetings_test_fail_ADEFGH(
        self, committee_id: None | int = None, group_B_success: bool = False
    ) -> None:
        # test group A
        response = self.request(
            "user.update",
            {
                "id": 111,
                "pronoun": "I'm not gonna get updated.",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meetings {1, 4}",
            response.json["message"],
        )
        self.assert_model_exists(
            "user/111",
            {
                "pronoun": None,
            },
        )
        # test group D
        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_management_ids": [1, 2],
            },
        )
        self.assert_status_code(response, 403)
        if committee_id:
            self.assertIn(
                f"You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee {committee_id}",
                response.json["message"],
            )
            self.assert_model_exists(
                "user/111",
                {
                    "committee_management_ids": [committee_id],
                },
            )
        else:
            self.assertIn(
                "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee ",
                response.json["message"],
            )
            self.assert_model_exists(
                "user/111",
                {
                    "committee_management_ids": None,
                },
            )
        # test group E
        response = self.request(
            "user.update",
            {
                "id": 111,
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Your organization management level is not high enough to set a Level of can_manage_users.",
            response.json["message"],
        )
        self.assert_model_exists(
            "user/111",
            {
                "organization_management_level": None,
            },
        )
        # test group F
        response = self.request(
            "user.update",
            {
                "id": 111,
                "default_password": "I'm not gonna get updated.",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meetings {1, 4}",
            response.json["message"],
        )
        self.assert_model_exists(
            "user/111",
            {
                "default_password": None,
            },
        )
        # test group G
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
        self.assert_model_exists(
            "user/111",
            {
                "is_demo_user": None,
            },
        )
        # test group H
        response = self.request(
            "user.update",
            {
                "id": 111,
                "saml_id": "I'm not gonna get updated.",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The field 'saml_id' can only be used in internal action calls",
            response.json["message"],
        )
        self.assert_model_exists(
            "user/111",
            {
                "saml_id": None,
            },
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
                "locked_out": True,
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
                "locked_out": True,
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
                "Participant added to meeting {}.",
                "meeting/1",
                "Participant added to group {} and structure level {} in meeting {}.",
                "group/11",
                "structure_level/31",
                "meeting/1",
                "Proxy voting rights for {} received in meeting {}",
                "user/23",
                "meeting/1",
                "Committee management changed",
            ],
        )
        self.assert_history_information(
            "user/23", ["Vote delegated to {} in meeting {}", "user/22", "meeting/1"]
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
        self.create_meeting()
        id_ = self.create_user("username_srtgb123")
        response = self.request(
            "user.update",
            {"id": id_, "vote_weight": "2.000000", "meeting_id": 1, "group_ids": [1]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            f"user/{id_}", {"username": "username_srtgb123", "meeting_user_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": 1,
                "user_id": id_,
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
                "meeting_user_ids": [],
                "committee_management_ids": [60, 61],
                "committee_ids": [60, 61],
            },
        )
        self.assert_model_deleted("meeting_user/1111", {"group_ids": []})
        self.assert_history_information(
            "user/111",
            [
                "Participant removed from group {} in meeting {}",
                "group/600",
                "meeting/60",
                "Participant removed from meeting {}",
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
                "meeting_user_ids": [112, 113],
            },
        )
        self.assert_model_deleted("meeting_user/111")
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
            {
                "organization/1": {"gender_ids": [1, 2, 3, 4]},
                "gender/1": {"name": "male"},
                "gender/2": {"name": "female"},
                "gender/3": {"name": "diverse"},
                "gender/4": {"name": "non-binary"},
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
                "gender_id": 2,
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
                "gender_id": 2,
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

    def test_perm_group_A_cml_manage_user_with_two_committees(self) -> None:
        """May update group A fields on committee scope. User belongs to 1 meeting in 1 committee"""
        self.permission_setup()
        self.create_meeting(4)
        self.set_committee_management_level([60], self.user_id)
        self.set_user_groups(111, [1, 4])
        self.set_models({"user/111": {"committee_ids": [60, 63]}})

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
                "meeting_ids": [1, 4],
                "committee_ids": [60, 63],
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

    def test_perm_group_A_meeting_manage_user_with_only_archived_meeting_no_permission(
        self,
    ) -> None:
        """
        May not update group A fields on meeting scope. User belongs to 1 archived meeting.
        """
        self.permission_setup()
        self.set_user_groups(self.user_id, [1])
        self.set_user_groups(111, [1])
        self.set_models(
            {
                "group/1": {"permissions": [Permissions.User.CAN_UPDATE]},
                "user/111": {"committee_ids": [60], "meeting_ids": [1]},
                "meeting/1": {"is_active_in_organization_id": None},
            },
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new_username",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 60",
            response.json["message"],
        )

    def test_perm_group_A_cml_manage_user_with_only_archived_meeting(
        self,
    ) -> None:
        """May update group A fields on committee scope. User belongs to 1 archived meeting in 1 committee"""
        self.permission_setup()
        self.set_committee_management_level([60], self.user_id)
        self.set_user_groups(111, [1])
        self.set_models(
            {
                "user/111": {"committee_ids": [60], "meeting_ids": [1]},
                "meeting/1": {"is_active_in_organization_id": None},
            },
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
                "meeting_ids": [1],
                "committee_ids": [60],
            },
        )

    def test_perm_group_A_meeting_manage_user(self) -> None:
        """
        May update group A fields on meeting scope. User belongs to 1 meeting without being part of a committee.
        Testing various scenarios:
        * both default group
        * default group has user.can_update permission
        * requesting user is in admin group
        """
        self.permission_setup()
        self.set_user_groups(self.user_id, [1])
        self.set_user_groups(111, [1])

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new_username",
                "pronoun": "pronoun",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 60 or Permission user.can_update in meeting {1}",
            response.json["message"],
        )
        self.assert_model_exists(
            "user/111",
            {
                "username": "User111",
                "pronoun": None,
                "meeting_ids": [1],
                "committee_ids": None,
            },
        )

        self.update_model("group/1", {"permissions": ["user.can_update"]})
        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new_user",
                "pronoun": "pro",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "new_user",
                "pronoun": "pro",
                "meeting_ids": [1],
                "committee_ids": None,
            },
        )

        self.set_user_groups(self.user_id, [2])
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

    def test_perm_group_A_belongs_to_same_meetings(self) -> None:
        """May update group A fields on any scope as long as admin user Ann belongs to all meetings user Ben belongs to. See issue 2522."""
        self.permission_setup()  # meeting 1 + logged in test user + user 111
        self.create_meeting(4)  # meeting 4
        # Admin groups of meeting/1 and meeting/4 for requesting user
        self.set_user_groups(self.user_id, [1, 4])
        # 111 into both meetings
        self.set_user_groups(111, [1, 4])
        self.two_meetings_test_fail_ADEFGH()
        # Admin group of meeting/1 and default group for meeting/4 for request user
        self.set_user_groups(self.user_id, [2, 4])
        # 111 into both meetings (admin group for meeting/4)
        self.set_user_groups(111, [1, 5])
        self.two_meetings_test_fail_ADEFGH()
        # test group B and C
        response = self.request(
            "user.update",
            {"id": 111, "number": "I'm not gonna get updated.", "meeting_id": 4},
        )
        self.assertIn(
            "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_update for meeting 4",
            response.json["message"],
        )
        self.assert_status_code(response, 403)
        self.assert_model_exists(
            "user/111",
            {
                "number": None,
            },
        )
        # Admin groups of meeting/1 and meeting/4 for request user
        self.set_user_groups(self.user_id, [2, 5])
        # 111 into both meetings
        self.set_user_groups(111, [1, 4])
        response = self.request(
            "user.update",
            {
                "id": 111,
                "pronoun": "I'm gonna get updated.",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "pronoun": "I'm gonna get updated.",
            },
        )

    def test_perm_group_A_belongs_to_same_meetings_can_update(self) -> None:
        """
        May update group A fields on any scope as long as requesting user has
        user.can_update rights in requested users meetings.
        Also makes sure being in multiple groups of a single meeting is no problem.
        """
        self.permission_setup()  # meeting 1 + logged in test user + user 111
        self.create_meeting(4)  # meeting 4
        self.update_model(
            "group/6",
            {"permissions": ["user.can_update"]},
        )
        # Admin group of meeting/1 and default group of meeting/4 for requesting user
        self.set_user_groups(self.user_id, [2, 4])
        # 111 into both meetings
        self.set_user_groups(111, [1, 4])
        self.two_meetings_test_fail_ADEFGH()
        # Admin groups of meeting/1 and meeting/4 (via group permission) for requesting user
        self.set_user_groups(self.user_id, [2, 4, 6])
        response = self.request(
            "user.update",
            {
                "id": 111,
                "pronoun": "I'm gonna get updated.",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "pronoun": "I'm gonna get updated.",
            },
        )

    def test_perm_group_A_belongs_to_same_meetings_can_manage(self) -> None:
        """
        May update group A fields on any scope as long as requesting user has
        user.can_update rights in requested users meetings.
        Also makes sure being in multiple groups of a single meeting is no problem.
        """
        self.permission_setup()  # meeting 1 + logged in requesting user + user 111
        self.create_meeting(4)  # meeting 4
        self.update_model(
            "group/6",
            {"permissions": ["user.can_manage"]},
        )
        # Admin group of meeting/1 and default group of meeting/4 for requesting user
        self.set_user_groups(self.user_id, [2, 4])
        # 111 into both meetings
        self.set_user_groups(111, [1, 4])
        self.two_meetings_test_fail_ADEFGH()
        # Admin groups of meeting/1 and meeting/4 (via group permission) for requesting user
        self.set_user_groups(self.user_id, [1, 2, 4, 6])
        response = self.request(
            "user.update",
            {
                "id": 111,
                "pronoun": "I'm gonna get updated.",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "pronoun": "I'm gonna get updated.",
            },
        )

    def test_perm_group_A_belongs_to_same_meetings_committee_admin(self) -> None:
        """May not update group A fields on any scope as long as admin user Ann belongs
        to all meetings user Ben belongs to but Ben is committee admin. See issue 2522.
        """
        self.permission_setup()  # meeting 1 + logged in requesting user + user 111
        self.create_meeting(4)  # meeting 4
        # Admin groups of meeting/1 and meeting/4 for requesting user
        self.set_user_groups(self.user_id, [2, 5])
        # 111 into both meetings
        self.set_user_groups(111, [1, 4])
        # 111 is committee admin
        committee_id = 60
        self.set_committee_management_level([committee_id], 111)
        self.two_meetings_test_fail_ADEFGH(committee_id)
        # test group B and C
        response = self.request(
            "user.update",
            {"id": 111, "number": "I'm not gonna get updated.", "meeting_id": 4},
        )
        self.assert_status_code(response, 200)
        self.assertIn(
            "Actions handled successfully",
            response.json["message"],
        )
        self.assert_model_exists(
            "user/111",
            {
                "number": None,
            },
        )
        response = self.request(
            "user.update",
            {
                "id": 111,
                "pronoun": "I'm not gonna get updated.",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meetings {1, 4}",
            response.json["message"],
        )
        self.assert_model_exists(
            "user/111",
            {
                "pronoun": None,
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

    def test_perm_group_A_meeting_manage_user_active_and_archived_meetings_in_same_committee(
        self,
    ) -> None:
        self.perm_group_A_meeting_manage_user_active_and_archived_meetings_in_same_committee(
            Permissions.User.CAN_UPDATE
        )

    def test_perm_group_A_meeting_manage_user_active_and_archived_meetings_in_same_committee_with_parent_permission(
        self,
    ) -> None:
        self.perm_group_A_meeting_manage_user_active_and_archived_meetings_in_same_committee(
            Permissions.User.CAN_MANAGE
        )

    def perm_group_A_meeting_manage_user_active_and_archived_meetings_in_same_committee(
        self, permission: Permission
    ) -> None:
        """
        May update group A fields on meeting scope. User belongs to 1 active meeting.
        User is member of an archived meeting in the same committee, but this doesn't may affect the result.
        """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_user_groups(self.user_id, [2])
        self.set_user_groups(111, [1, 4])
        self.set_models(
            {
                "meeting/4": {
                    "is_active_in_organization_id": None,
                    "committee_id": 60,
                },
                "group/2": {"permissions": [permission]},
                "user/111": {"committee_ids": [1]},
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
        self.assert_model_exists("user/111", {"username": "new_username"})
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
            "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meetings {1, 4}",
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
                "organization/1": {"gender_ids": [2]},
                "gender/2": {"name": "female"},
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
                "gender_id": 2,
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

    def test_perm_group_F_cml_manage_user_with_two_committees(self) -> None:
        """May update group F fields on committee scope. User belongs to two meetings."""
        self.permission_setup()
        self.create_meeting(4)
        self.set_committee_management_level([60], self.user_id)
        self.set_user_groups(111, [1, 4])
        self.set_models({"user/111": {"committee_ids": [60, 63]}})

        response = self.request(
            "user.update",
            {
                "id": 111,
                "default_password": "new_one",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "default_password": "new_one",
            },
        )

    def test_perm_group_F_with_meeting_scope(self) -> None:
        """
        Test user update with various scenarios (admin in different meeting and committee no interference)
            * not in same meeting fails
            * same meeting but requesting user not in admin or permission group fails
            * same meeting requesting user with permission user.can_update works
            * same meeting both admin works
            * same meeting requesting user is committee admin works
        """
        self.permission_setup()
        self.create_meeting(4)
        self.set_user_groups(111, [2])
        self.set_user_groups(self.user_id, [5])
        self.set_committee_management_level([63], self.user_id)

        response = self.request(
            "user.update",
            {
                "id": 111,
                "default_password": "new_one",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 60 or Permission user.can_update in meeting {1}",
            response.json["message"],
        )
        self.assert_model_exists(
            "user/111",
            {
                "default_password": None,
            },
        )

        self.set_user_groups(self.user_id, [1, 5])
        response = self.request(
            "user.update",
            {
                "id": 111,
                "default_password": "new_one",
            },
        )
        self.assert_status_code(response, 403)
        self.assert_model_exists(
            "user/111",
            {
                "default_password": None,
            },
        )

        self.update_model("group/1", {"permissions": ["user.can_update"]})
        response = self.request(
            "user.update",
            {
                "id": 111,
                "default_password": "new_one",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "default_password": "new_one",
            },
        )

        self.set_user_groups(self.user_id, [2, 5])
        response = self.request(
            "user.update",
            {
                "id": 111,
                "default_password": "newer_one",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "default_password": "newer_one",
            },
        )

        self.set_committee_management_level([60], self.user_id)
        response = self.request(
            "user.update",
            {
                "id": 111,
                "default_password": "newest_one",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "default_password": "newest_one",
            },
        )

    def test_perm_group_F_with_two_meeting_across_committees(self) -> None:
        """
        May not update group F fields unless requesting user has admin rights in
        all of requested users meetings. Also requested user can be admin himself.
        """
        self.permission_setup()
        self.create_meeting(4)
        self.set_user_groups(111, [1, 4])
        self.set_user_groups(self.user_id, [2, 4])

        response = self.request(
            "user.update",
            {
                "id": 111,
                "default_password": "new_one",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meetings {1, 4}",
            response.json["message"],
        )
        self.assert_model_exists(
            "user/111",
            {
                "default_password": None,
            },
        )
        # assert meeting admin can change normal user
        self.set_user_groups(111, [1, 5])
        self.set_user_groups(self.user_id, [2, 5])
        response = self.request(
            "user.update",
            {
                "id": 111,
                "default_password": "new_one",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "default_password": "new_one",
            },
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
            "The user needs Permission user.can_update for meeting 4",
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
            "The user needs Permission user.can_update for meeting 1",
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
            "The user needs Permission user.can_update for meeting 1",
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
            "The user needs Permission user.can_update for meeting 1",
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
            "The user needs Permission user.can_update for meeting 1",
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
            {
                "organization/1": {"gender_ids": [1, 2, 3, 4]},
                "gender/1": {"name": "male"},
                "gender/2": {"name": "female"},
                "gender/3": {"name": "diverse"},
                "gender/4": {"name": "non-binary"},
            }
        )
        response = self.request("user.update", {"id": 111, "gender_id": 5})
        self.assert_status_code(response, 400)
        assert "Model 'gender/5' does not exist." in response.json["message"]

        response = self.request("user.update", {"id": 111, "gender_id": 3})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/111", {"gender_id": 3})

        response = self.request("user.update", {"id": 111, "gender_id": 4})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/111", {"gender_id": 4})

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

    def test_update_clear_user_sessions(self) -> None:
        self.permission_setup()
        self.set_user_groups(self.user_id, [2])
        response = self.request(
            "user.update",
            {
                "id": self.user_id,
                "is_active": False,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(f"user/{self.user_id}", {"is_active": False})
        self.assert_logged_out()

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
        """Testing also that user is not locked out when is_active is set to True."""
        self.permission_setup()
        self.set_user_groups(self.user_id, [2])
        self.create_user("dummy", [2])

        response = self.request(
            "user.update",
            {
                "id": self.user_id,
                "meeting_id": 1,
                "group_ids": [1],
                "is_active": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_logged_in()

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
        self.create_meeting()
        self.create_meeting(4)
        bob_id = self.create_user("bob")
        bob_muser_ids = self.set_user_groups(bob_id, [1])
        self.set_models(
            {
                f"meeting_user/{bob_muser_ids[0]}": {
                    "vote_weight": "1.000000",
                },
            }
        )
        response = self.request(
            "user.update",
            {
                "id": bob_id,
                "meeting_id": 4,
                "vote_weight": "1.500000",
                "group_ids": [4],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            f"user/{bob_id}",
            [
                "Participant added to meeting {}.",
                "meeting/4",
                "Participant added to group {} in meeting {}.",
                "group/4",
                "meeting/4",
            ],
        )

    def test_update_participant_data_in_multiple_meetings_with_existing_meetings(
        self,
    ) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.create_meeting(7)
        bob_id = self.create_user("bob")
        bob_muser_id = self.set_user_groups(bob_id, [1])[0]
        self.set_models(
            {
                f"meeting_user/{bob_muser_id}": {
                    "vote_weight": "1.000000",
                },
            }
        )
        response = self.request_multi(
            "user.update",
            [
                {
                    "id": bob_id,
                    "meeting_id": 4,
                    "vote_weight": "1.000000",
                    "group_ids": [4],
                },
                {
                    "id": bob_id,
                    "meeting_id": 7,
                    "vote_weight": "1.000000",
                    "group_ids": [7],
                },
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_history_information(
            f"user/{bob_id}",
            [
                "Participant added to meeting {}.",
                "meeting/4",
                "Participant added to group {} in meeting {}.",
                "group/4",
                "meeting/4",
                "Participant added to meeting {}.",
                "meeting/7",
                "Participant added to group {} in meeting {}.",
                "group/7",
                "meeting/7",
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
                    "is_present_in_meeting_ids": [4, 5],
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
                    "present_user_ids": [1234],
                },
                "meeting/5": {
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [5555],
                    "committee_id": 1,
                    "present_user_ids": [1234],
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
                "meeting_user_ids": [5555],
                "is_present_in_meeting_ids": [5],
            },
        )
        self.assert_model_exists(
            "meeting/4",
            {
                "present_user_ids": [],
            },
        )
        self.assert_model_exists(
            "meeting/5",
            {
                "present_user_ids": [1234],
            },
        )
        self.assert_model_deleted(
            "meeting_user/4444",
            {"group_ids": [], "speaker_ids": [24]},
        )
        self.assert_model_exists(
            "meeting_user/5555",
            {"group_ids": [53], "speaker_ids": [25], "meta_deleted": False},
        )
        self.assert_model_exists(
            "speaker/24", {"meeting_user_id": None, "meeting_id": 4}
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

    def test_update_groups_on_last_meeting_admin(self) -> None:
        self.create_meeting()
        self.create_user("username_srtgb123", [2])
        response = self.request(
            "user.update", {"id": 2, "meeting_id": 1, "group_ids": [3]}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot remove last admin from meeting(s) 1",
            response.json["message"],
        )

    def test_update_groups_on_both_last_meeting_admins(self) -> None:
        self.create_meeting()
        self.create_user("username_srtgb123", [2])
        self.create_user("username_srtgb456", [2])
        response = self.request_multi(
            "user.update",
            [
                {"id": 2, "meeting_id": 1, "group_ids": [3]},
                {"id": 3, "meeting_id": 1, "group_ids": [3]},
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot remove last admin from meeting(s) 1",
            response.json["message"],
        )

    def test_update_groups_on_last_meeting_admin_multi(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.create_user("username_srtgb123", [2])
        self.create_user("username_srtgb456", [5])
        response = self.request_multi(
            "user.update",
            [
                {"id": 2, "meeting_id": 1, "group_ids": [3]},
                {"id": 3, "meeting_id": 4, "group_ids": [6]},
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot remove last admin from meeting(s) 1, 4",
            response.json["message"],
        )

    def test_update_groups_on_last_meeting_admin_in_template_meeting(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"template_for_organization_id": 1},
                "organization/1": {"template_meeting_ids": [1]},
            }
        )
        self.create_user("username_srtgb123", [2])
        response = self.request(
            "user.update", {"id": 2, "meeting_id": 1, "group_ids": [3]}
        )
        self.assert_status_code(response, 200)

    def test_update_groups_on_last_meeting_admin_and_add_a_new_admin(self) -> None:
        self.create_meeting()
        self.create_user("username_srtgb123", [2])
        self.create_user("username_srtgb456", [1])
        response = self.request_multi(
            "user.update",
            [
                {"id": 2, "meeting_id": 1, "group_ids": [3]},
                {"id": 3, "meeting_id": 1, "group_ids": [2]},
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/1", {"user_id": 2, "group_ids": [3]})
        self.assert_model_exists("meeting_user/2", {"user_id": 3, "group_ids": [2]})

    def test_update_anonymous_group_id(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"group_ids": [1, 2, 3, 4]},
                "group/4": {"anonymous_group_for_meeting_id": 1},
            }
        )
        user_id = self.create_user("dummy", [1])
        response = self.request(
            "user.update",
            {
                "id": user_id,
                "meeting_id": 1,
                "group_ids": [1, 4],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot add explicit users to a meetings anonymous group",
            response.json["message"],
        )

    def create_data_for_locked_out_test(self) -> dict[str, tuple[int, int | None]]:
        """
        Creates two meetings and a bunch of users with different roles.
        The return dict has the format {username: (user_id,meeting_user_id)}
        """
        self.create_meeting()  # committee:60; groups: default:1, admin:2, can_manage:3
        self.create_meeting(4)  # committee:63; groups: default:4, admin:5, can_update:6
        self.add_group_permissions(3, [Permissions.User.CAN_MANAGE])
        self.add_group_permissions(6, [Permissions.User.CAN_UPDATE])
        users: dict[str, tuple[int, int | None]] = {}
        users["superad"] = (
            self.create_user("superad", [], OrganizationManagementLevel.SUPERADMIN),
            None,
        )
        users["orgaad"] = (
            self.create_user(
                "orgaad", [], OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
            ),
            None,
        )
        users["userad"] = (
            self.create_user(
                "userad", [], OrganizationManagementLevel.CAN_MANAGE_USERS
            ),
            None,
        )
        users["committeead60"] = self.create_user("committeead60"), None
        users["meetingad1"] = self.create_user("meetingad1", [2]), 1
        users["can_manage1"] = self.create_user("can_manage1", [3]), 2
        users["can_update4"] = self.create_user("can_update1", [6]), 3
        users["participant1"] = self.create_user("participant1", [1]), 4
        users["account"] = self.create_user("account"), None
        self.set_models(
            {
                "committee/60": {"manager_ids": [users["committeead60"][0]]},
                f"user/{users['committeead60'][0]}": {"committee_management_ids": [60]},
            }
        )
        self.create_user("dummy_meeting_ad", [2])
        return users

    def test_update_locked_out_on_self_error(self) -> None:
        self.create_data_for_locked_out_test()
        self.set_user_groups(1, [1])
        response = self.request(
            "user.update",
            {
                "id": 1,
                "meeting_id": 1,
                "locked_out": True,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "You may not lock yourself out of a meeting",
            response.json["message"],
        )

    def assert_lock_out_user(
        self,
        username: Literal[
            "superad",
            "orgaad",
            "userad",
            "committeead60",
            "meetingad1",
            "can_manage1",
            "can_update4",
            "participant1",
            "account",
        ],
        meeting_id: int,
        lock_out: bool | None = True,
        other_data: dict[str, Any] = {},
        add_to_meeting: int | None = None,
        lock_before: bool = False,
        errormsg: str | None = None,
    ) -> None:
        """
        Checks if the locking errors work based on the data from the create_data_for_locked_out_test function.
        Parameters are:
        - username: The name of the user that should be updated
        - meeting_id: Id of the meeting in which the user should potentially be locked
        - lock_out: Whether the 'locked_out' field should be set and to what value (None means leave out)
        - other_data: The rest of the payload
        - add_to_meeting: Will add the user to the specified meeting's default group beforehand
        - lock_before: If true, the user will be locked out of the meeting before calling the action
        - errormsg: The expected error message, if left empty the request is expected to end in success
        """
        users = self.create_data_for_locked_out_test()
        user_id, meeting_user_id = users[username]
        if add_to_meeting:
            self.set_user_groups(user_id, [meeting_id])
        if lock_before and meeting_user_id:
            self.set_models({f"meeting_user/{meeting_user_id}": {"locked_out": True}})
        data = {
            "id": user_id,
            "meeting_id": meeting_id,
            **other_data,
        }
        if lock_out is not None:
            data["locked_out"] = lock_out
        response = self.request(
            "user.update",
            data,
        )
        if errormsg is not None:
            self.assert_status_code(response, 400)
            self.assertIn(
                errormsg,
                response.json["message"],
            )
        else:
            self.assert_status_code(response, 200)

    def test_update_locked_out_foreign_cml_allowed(self) -> None:
        self.assert_lock_out_user(
            "account",
            1,
            other_data={"committee_management_ids": [63], "group_ids": [1]},
        )

    def test_update_locked_out_user_child_cml_allowed(self) -> None:
        self.create_committee(60)
        self.create_committee(63, parent_id=60)
        self.assert_lock_out_user(
            "account",
            1,
            other_data={"committee_management_ids": [63], "group_ids": [1]},
        )

    def test_update_locked_out_user_home_committee_allowed(self) -> None:
        self.assert_lock_out_user(
            "account", 1, other_data={"home_committee_id": 60, "group_ids": [1]}
        )

    def test_update_locked_out_user_child_home_committee_allowed(self) -> None:
        self.create_committee(60)
        self.create_committee(63, parent_id=60)
        self.assert_lock_out_user(
            "account", 1, other_data={"home_committee_id": 63, "group_ids": [1]}
        )

    def test_update_locked_out_user_foreign_home_committee_allowed(self) -> None:
        self.assert_lock_out_user(
            "account", 1, other_data={"home_committee_id": 63, "group_ids": [1]}
        )

    def test_update_locked_out_superadmin_error(self) -> None:
        self.assert_lock_out_user(
            "account",
            1,
            other_data={"organization_management_level": "superadmin"},
            errormsg="Cannot give OrganizationManagementLevel superadmin to user 10 as he is locked out of meeting(s) 1",
        )

    def test_update_locked_out_other_oml_error(self) -> None:
        self.assert_lock_out_user(
            "account",
            1,
            other_data={"organization_management_level": "can_manage_users"},
            errormsg="Cannot give OrganizationManagementLevel can_manage_users to user 10 as he is locked out of meeting(s) 1",
        )

    def test_update_locked_out_cml_error(self) -> None:
        self.assert_lock_out_user(
            "account",
            1,
            other_data={"committee_management_ids": [60]},
            errormsg="Cannot set user 10 as manager for committee(s) 60 due to being locked out of meeting(s) 1",
        )

    def test_create_locked_out_user_parent_cml_error(self) -> None:
        self.create_committee(59)
        self.create_committee(60, parent_id=59)
        self.assert_lock_out_user(
            "account",
            1,
            other_data={"committee_management_ids": [59]},
            errormsg="Cannot set user 10 as manager for committee(s) 59 due to being locked out of meeting(s) 1",
        )

    def test_update_locked_out_meeting_admin_error(self) -> None:
        self.assert_lock_out_user(
            "account",
            1,
            other_data={"group_ids": [2]},
            errormsg="Group(s) 2 have user.can_manage permissions and may therefore not be used by users who are locked out",
        )

    def test_update_locked_out_can_update_allowed(self) -> None:
        self.assert_lock_out_user(
            "account",
            4,
            other_data={"group_ids": [6]},
        )

    def test_update_locked_out_on_foreign_cml_allowed(self) -> None:
        self.assert_lock_out_user("committeead60", 4, add_to_meeting=4)

    def test_update_locked_out_on_superadmin_error(self) -> None:
        self.assert_lock_out_user(
            "superad",
            1,
            add_to_meeting=1,
            errormsg="Cannot lock user from meeting 1 as long as he has the OrganizationManagementLevel superadmin",
        )

    def test_update_locked_out_on_other_oml_error(self) -> None:
        self.assert_lock_out_user(
            "orgaad",
            1,
            add_to_meeting=1,
            errormsg="Cannot lock user from meeting 1 as long as he has the OrganizationManagementLevel can_manage_organization",
        )

    def test_update_locked_out_on_cml_error(self) -> None:
        self.assert_lock_out_user(
            "committeead60",
            1,
            errormsg="Cannot lock user out of meeting 1 as he is manager of the meetings committee",
        )

    def test_update_locked_out_on_meeting_admin_error(self) -> None:
        self.assert_lock_out_user(
            "meetingad1",
            1,
            errormsg="Group(s) 2 have user.can_manage permissions and may therefore not be used by users who are locked out",
        )

    def test_update_locked_out_on_can_manage_error(self) -> None:
        self.assert_lock_out_user(
            "can_manage1",
            1,
            errormsg="Group(s) 3 have user.can_manage permissions and may therefore not be used by users who are locked out",
        )

    def test_update_locked_out_on_can_update_allowed(self) -> None:
        self.assert_lock_out_user(
            "can_update4",
            4,
        )

    def test_update_locked_out_on_foreign_meeting_admin_allowed(self) -> None:
        self.assert_lock_out_user("meetingad1", 4, add_to_meeting=4)

    def test_update_locked_out_on_foreign_can_manage_allowed(self) -> None:
        self.assert_lock_out_user("can_manage1", 4, add_to_meeting=4)

    def test_update_other_oml_on_locked_out_user_error(self) -> None:
        self.assert_lock_out_user(
            "participant1",
            1,
            other_data={"organization_management_level": "can_manage_users"},
            lock_out=None,
            lock_before=True,
            errormsg="Cannot give OrganizationManagementLevel can_manage_users to user 9 as he is locked out of meeting(s) 1",
        )

    def test_update_cml_on_locked_out_user_error(self) -> None:
        self.assert_lock_out_user(
            "participant1",
            1,
            other_data={"committee_management_ids": [60]},
            lock_out=None,
            lock_before=True,
            errormsg="Cannot set user 9 as manager for committee(s) 60 due to being locked out of meeting(s) 1",
        )

    def test_update_parent_cml_on_locked_out_user_error(self) -> None:
        self.create_committee(59)
        self.create_committee(60, parent_id=59)
        self.assert_lock_out_user(
            "participant1",
            1,
            other_data={"committee_management_ids": [59]},
            lock_out=None,
            lock_before=True,
            errormsg="Cannot set user 9 as manager for committee(s) 59 due to being locked out of meeting(s) 1",
        )

    def test_update_child_cml_on_locked_out_user_error(self) -> None:
        self.create_committee(60)
        self.create_committee(61, parent_id=60)
        self.assert_lock_out_user(
            "participant1",
            1,
            other_data={"committee_management_ids": [61]},
            lock_out=None,
            lock_before=True,
        )

    def test_update_meeting_admin_on_locked_out_user_error(self) -> None:
        self.assert_lock_out_user(
            "participant1",
            1,
            other_data={"group_ids": [2]},
            lock_out=None,
            lock_before=True,
            errormsg="Group(s) 2 have user.can_manage permissions and may therefore not be used by users who are locked out",
        )

    def test_update_locked_out_remove_superadmin(self) -> None:
        self.assert_lock_out_user(
            "superad",
            1,
            other_data={"organization_management_level": None, "group_ids": [1]},
        )

    def test_update_locked_out_remove_cml(self) -> None:
        self.assert_lock_out_user(
            "committeead60",
            1,
            other_data={"committee_management_ids": None, "group_ids": [1]},
        )

    def test_update_locked_out_remove_meeting_admin(self) -> None:
        self.assert_lock_out_user(
            "meetingad1",
            1,
            other_data={"group_ids": [1]},
        )

    def test_update_locked_out_remove_can_manage(self) -> None:
        self.assert_lock_out_user(
            "can_manage1",
            1,
            other_data={"group_ids": [1]},
        )

    def test_update_oml_remove_locked_out(self) -> None:
        self.assert_lock_out_user(
            "participant1",
            1,
            other_data={"organization_management_level": "can_manage_organization"},
            lock_before=True,
            lock_out=False,
        )

    def test_update_cml_remove_locked_out(self) -> None:
        self.assert_lock_out_user(
            "participant1",
            1,
            other_data={"committee_management_ids": [60]},
            lock_before=True,
            lock_out=False,
        )

    def test_update_meeting_admin_remove_locked_out(self) -> None:
        self.assert_lock_out_user(
            "participant1",
            1,
            other_data={"group_ids": [2]},
            lock_before=True,
            lock_out=False,
        )

    def test_update_can_update_remove_locked_out(self) -> None:
        self.assert_lock_out_user(
            "account",
            4,
            other_data={"group_ids": [6]},
            lock_before=True,
            lock_out=False,
        )

    def test_update_permission_as_locked_out(self) -> None:
        self.permission_setup()
        self.create_meeting(base=4)
        meeting_user_ids = self.set_user_groups(self.user_id, [3, 6])  # Admin-groups
        self.set_group_permissions(3, [Permissions.User.CAN_UPDATE])
        self.set_group_permissions(6, [Permissions.User.CAN_UPDATE])
        self.set_user_groups(111, [1, 4])
        self.set_models(
            {
                "meeting/4": {"committee_id": 60},
                "committee/60": {"meeting_ids": [1, 4]},
                **{
                    f"meeting_user/{m_user_id}": {"locked_out": True}
                    for m_user_id in meeting_user_ids
                },
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

        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_update for meeting 1",
            response.json["message"],
        )

    def test_add_participant_as_orga_admin(self) -> None:
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, self.user_id
        )
        self.set_user_groups(self.user_id, [])
        response = self.request(
            "user.update",
            {
                "id": 111,
                "meeting_id": 1,
                "group_ids": [3],
                "vote_delegations_from_ids": [],
            },
        )

        self.assert_status_code(response, 200)
        user = self.assert_model_exists("user/111")
        assert len(meeting_user_ids := user.get("meeting_user_ids", [])) == 1
        self.assert_model_exists(
            f"meeting_user/{meeting_user_ids[0]}", {"meeting_id": 1, "group_ids": [3]}
        )

    def test_update_with_home_committee(self) -> None:
        self.create_committee(3)
        self.create_user("dracula")
        response = self.request(
            "user.update",
            {"id": 2, "home_committee_id": 3},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2", {"username": "dracula", "home_committee_id": 3}
        )

    def test_update_with_home_committee_cml(self) -> None:
        self.create_committee(3)
        self.create_user("mina")
        self.set_committee_management_level([3])
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {"id": 2, "home_committee_id": 3},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "mina", "home_committee_id": 3})

    def test_update_with_external_true(self) -> None:
        self.create_user("jonathan")
        response = self.request(
            "user.update",
            {"id": 2, "external": True},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "jonathan", "external": True})

    def test_update_with_external_true_unsets_home_committee(self) -> None:
        self.create_committee()
        self.create_user("jonathan", home_committee_id=1)
        response = self.request(
            "user.update",
            {"id": 2, "external": True},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"username": "jonathan", "external": True, "home_committee_id": None},
        )

    def test_update_with_external_false(self) -> None:
        self.create_user("jack")
        response = self.request(
            "user.update",
            {"id": 2, "external": False},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "jack", "external": False})

    def test_update_with_external_false_doesnt_unset_home_committee(self) -> None:
        self.create_committee()
        self.create_user("jack", home_committee_id=1)
        response = self.request(
            "user.update",
            {"id": 2, "external": False},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2", {"username": "jack", "external": False, "home_committee_id": 1}
        )

    def test_update_with_with_home_committee_and_external_true(self) -> None:
        self.create_committee(3)
        self.create_user("renfield")
        response = self.request(
            "user.update",
            {"id": 2, "home_committee_id": 3, "external": True},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot set external to true and set a home committee at the same time.",
            response.json["message"],
        )

    def test_update_with_home_committee_and_external_false(self) -> None:
        """Also tests for parent CML"""
        self.create_committee(2)
        self.create_committee(3, parent_id=2)
        self.create_user("vanHelsing")
        self.set_committee_management_level([2])
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {"id": 2, "home_committee_id": 3, "external": False},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"username": "vanHelsing", "home_committee_id": 3, "external": False},
        )

    def test_update_with_home_committee_wrong_CML(self) -> None:
        self.create_committee(2)
        self.create_committee(3)
        self.create_user("quincy")
        self.set_committee_management_level([2])
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {
                "id": 2,
                "home_committee_id": 3,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee {3}",
            response.json["message"],
        )

    def test_update_with_home_committee_no_perm(self) -> None:
        self.create_committee(3)
        self.create_user("arthur")
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {
                "id": 2,
                "home_committee_id": 3,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee {3}",
            response.json["message"],
        )

    def test_update_overwrite_home_committee(self) -> None:
        self.create_committee(3)
        self.create_user("dracula")
        response = self.request(
            "user.update",
            {"id": 2, "home_committee_id": 3},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2", {"username": "dracula", "home_committee_id": 3}
        )

    def test_update_overwrite_home_committee_both_cml(self) -> None:
        self.create_committee(2)
        self.create_committee(3)
        self.create_user("mina", home_committee_id=2)
        self.set_committee_management_level([2, 3])
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {"id": 2, "home_committee_id": 3},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "mina", "home_committee_id": 3})

    def test_update_overwrite_home_committee_both_parent_cml(self) -> None:
        self.create_committee(1)
        self.create_committee(2, parent_id=1)
        self.create_committee(3, parent_id=1)
        self.create_user("mina", home_committee_id=2)
        self.set_committee_management_level([1])
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {"id": 2, "home_committee_id": 3},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "mina", "home_committee_id": 3})

    def test_update_overwrite_home_committee_wrong_CML(self) -> None:
        self.create_committee(1)
        self.create_committee(2)
        self.create_committee(3)
        self.create_user("quincy", home_committee_id=1)
        self.set_committee_management_level([2])
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {
                "id": 2,
                "home_committee_id": 3,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committees {1, 3}",
            response.json["message"],
        )

    def test_update_overwrite_home_committee_old_home_committee_CML(self) -> None:
        self.create_committee(2)
        self.create_committee(3)
        self.create_user("quincy", home_committee_id=2)
        self.set_committee_management_level([2])
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {
                "id": 2,
                "home_committee_id": 3,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee {3}",
            response.json["message"],
        )

    def test_update_overwrite_home_committee_new_home_committee_CML(self) -> None:
        self.create_committee(2)
        self.create_committee(3)
        self.create_user("quincy", home_committee_id=2)
        self.set_committee_management_level([3])
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {
                "id": 2,
                "home_committee_id": 3,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee {2}",
            response.json["message"],
        )

    def test_update_overwrite_home_committee_no_perm(self) -> None:
        self.create_committee(2)
        self.create_committee(3)
        self.create_user("arthur", home_committee_id=2)
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {
                "id": 2,
                "home_committee_id": 3,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committees {2, 3}",
            response.json["message"],
        )

    def test_update_overwrite_home_committee_OML_orga(self) -> None:
        self.create_committee(2)
        self.create_committee(3)
        self.create_user("arthur", home_committee_id=2)
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request(
            "user.update",
            {
                "id": 2,
                "home_committee_id": 3,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"home_committee_id": 3})

    def test_update_overwrite_home_committee_OML_users(self) -> None:
        self.create_committee(2)
        self.create_committee(3)
        self.create_user("arthur", home_committee_id=2)
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        response = self.request(
            "user.update",
            {
                "id": 2,
                "home_committee_id": 3,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committees {2, 3}",
            response.json["message"],
        )

    def test_update_overwrite_home_committee_as_meeting_admin(self) -> None:
        self.create_committee(3)
        self.create_meeting()
        self.create_user("arthur", group_ids=[1], home_committee_id=60)
        self.set_organization_management_level(None)
        self.set_user_groups(1, [2])
        response = self.request(
            "user.update",
            {
                "id": 2,
                "home_committee_id": 3,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committees {3, 60}",
            response.json["message"],
        )

    def test_update_add_user_to_meeting_and_home_committee(self) -> None:
        self.create_committee(3)
        self.create_meeting()
        self.create_user("arthur")
        self.set_organization_management_level(None)
        self.set_user_groups(1, [2])
        self.set_committee_management_level([3])
        response = self.request(
            "user.update",
            {"id": 2, "home_committee_id": 3, "meeting_id": 1, "group_ids": [1]},
        )
        self.assert_status_code(response, 200)
        meeting_user_ids = self.assert_model_exists("user/2", {"home_committee_id": 3})[
            "meeting_user_ids"
        ]
        assert len(meeting_user_ids) == 1
        self.assert_model_exists(
            f"meeting_user/{meeting_user_ids[0]}", {"meeting_id": 1, "group_ids": [1]}
        )

    def test_update_committee_membership_calculation_with_home_committee(
        self,
    ) -> None:
        self.create_meeting()  # and committee 60
        self.create_committee(61)
        self.create_committee(62)
        self.create_meeting(4)  # and committee 63
        self.create_committee(64)
        self.create_committee(65)
        self.create_meeting(7)  # and committee 66
        testcases: list[dict[str, Any]] = [
            {
                "name": "acctJoinMeeting",
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "expected_committees": [60],
            },
            {
                "name": "acctJoinCommittee",
                "payload_hc_id": 60,
                "expected_committees": [60],
            },
            {
                "name": "acctBecomeAdmin",
                "payload_cm_ids": [60],
                "expected_committees": [60],
            },
            {
                "name": "acctJoinMeetingNCommittee",
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_hc_id": 60,
                "expected_committees": [60],
            },
            {
                "name": "acctJoinCommitteeNBecomeAdmin",
                "payload_hc_id": 60,
                "payload_cm_ids": [60],
                "expected_committees": [60],
            },
            {
                "name": "acctJoinMeetingNBecomeAdmin",
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_cm_ids": [60],
                "expected_committees": [60],
            },
            {
                "name": "acctAll",
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_hc_id": 60,
                "payload_cm_ids": [60],
                "expected_committees": [60],
            },
            {
                "name": "acctAllDifferent",
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_hc_id": 61,
                "payload_cm_ids": [62, 64],
                "expected_committees": [60, 61, 62, 64],
            },
            {
                "name": "ptcpJoinMeeting",
                "meeting_ids": [7],
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "expected_committees": [60, 66],
            },
            {
                "name": "ptcpJoinCommittee",
                "meeting_ids": [7],
                "payload_hc_id": 60,
                "expected_committees": [60, 66],
            },
            {
                "name": "ptcpBecomeAdmin",
                "meeting_ids": [7],
                "payload_cm_ids": [60],
                "expected_committees": [60, 66],
            },
            {
                "name": "ptcpJoinMeetingNCommittee",
                "meeting_ids": [4, 7],
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_hc_id": 60,
                "expected_committees": [60, 63, 66],
            },
            {
                "name": "ptcpJoinCommitteeNBecomeAdmin",
                "meeting_ids": [7],
                "payload_hc_id": 60,
                "payload_cm_ids": [60],
                "expected_committees": [60, 66],
            },
            {
                "name": "ptcpJoinMeetingNBecomeAdmin",
                "meeting_ids": [7],
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_cm_ids": [60],
                "expected_committees": [60, 66],
            },
            {
                "name": "ptcpAll",
                "meeting_ids": [7],
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_hc_id": 60,
                "payload_cm_ids": [60],
                "expected_committees": [60, 66],
            },
            {
                "name": "ptcpAllDifferent",
                "meeting_ids": [4, 7],
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_hc_id": 61,
                "payload_cm_ids": [62, 63, 64],
                "expected_committees": [60, 61, 62, 63, 64, 66],
            },
            {
                "name": "ptcpLeave",
                "meeting_ids": [7],
                "payload_m_id": 7,
                "expected_committees": [],
            },
            {
                "name": "ptcpLeaveJoinSameCommittee",
                "meeting_ids": [7],
                "payload_m_id": 7,
                "payload_hc_id": 66,
                "expected_committees": [66],
            },
            {
                "name": "ptcpLeaveJoinOtherCommittee",
                "meeting_ids": [7],
                "payload_m_id": 7,
                "payload_hc_id": 60,
                "expected_committees": [60],
            },
            {
                "name": "ptcpLeaveBecomeAdmin",
                "meeting_ids": [1],
                "payload_m_id": 1,
                "payload_cm_ids": [60],
                "expected_committees": [60],
            },
            {
                "name": "ntusJoinMeeting",
                "home_committee_id": 60,
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "expected_committees": [60],
            },
            {
                "name": "ntusJoinCommittee",
                "home_committee_id": 60,
                "payload_hc_id": 62,
                "expected_committees": [62],
            },
            {
                "name": "ntusBecomeAdmin",
                "home_committee_id": 60,
                "payload_cm_ids": [60],
                "expected_committees": [60],
            },
            {
                "name": "ntusJoinMeetingNCommittee",
                "home_committee_id": 60,
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_hc_id": 62,
                "expected_committees": [60, 62],
            },
            {
                "name": "ntusJoinCommitteeNBecomeAdmin",
                "home_committee_id": 64,
                "payload_hc_id": 60,
                "payload_cm_ids": [60],
                "expected_committees": [60],
            },
            {
                "name": "ntusJoinMeetingNBecomeAdmin",
                "home_committee_id": 60,
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_cm_ids": [60],
                "expected_committees": [60],
            },
            {
                "name": "ntusAll",
                "home_committee_id": 66,
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_hc_id": 60,
                "payload_cm_ids": [60],
                "expected_committees": [60],
            },
            {
                "name": "ntusAllDifferent",
                "home_committee_id": 60,
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_hc_id": 61,
                "payload_cm_ids": [62, 63, 64],
                "expected_committees": [60, 61, 62, 63, 64],
            },
            {
                "name": "ntusSwitch",
                "home_committee_id": 60,
                "payload_hc_id": 61,
                "expected_committees": [61],
            },
            {
                "name": "ntusLeave",
                "home_committee_id": 60,
                "payload_hc_id": 0,
                "expected_committees": [],
            },
            {
                "name": "ntusLeaveJoinSameCommitteeMeeting",
                "home_committee_id": 60,
                "payload_m_id": 1,
                "payload_group_ids": [2],
                "payload_hc_id": 0,
                "expected_committees": [60],
            },
            {
                "name": "ntusLeaveBecomeAdmin",
                "home_committee_id": 60,
                "payload_hc_id": 0,
                "payload_cm_ids": [60],
                "expected_committees": [60],
            },
            {
                "name": "ntusLeaveBecomeOtherAdmin",
                "home_committee_id": 60,
                "payload_hc_id": 0,
                "payload_cm_ids": [65],
                "expected_committees": [65],
            },
            {
                "name": "cmadJoinMeeting",
                "committee_management_ids": [60],
                "payload_m_id": 4,
                "payload_group_ids": [4],
                "expected_committees": [60, 63],
            },
            {
                "name": "cmadJoinCommittee",
                "committee_management_ids": [60],
                "payload_hc_id": 60,
                "expected_committees": [60],
            },
            {
                "name": "cmadBecomeAdmin",
                "committee_management_ids": [60],
                "payload_cm_ids": [60, 63],
                "expected_committees": [60, 63],
            },
            {
                "name": "cmadJoinMeetingNCommittee",
                "committee_management_ids": [60],
                "payload_m_id": 4,
                "payload_group_ids": [5],
                "payload_hc_id": 62,
                "expected_committees": [60, 62, 63],
            },
            {
                "name": "cmadJoinCommitteeNBecomeAdmin",
                "committee_management_ids": [60],
                "payload_hc_id": 61,
                "payload_cm_ids": [60, 66],
                "expected_committees": [60, 61, 66],
            },
            {
                "name": "cmadJoinMeetingNBecomeAdmin",
                "committee_management_ids": [60],
                "payload_m_id": 4,
                "payload_group_ids": [4],
                "payload_cm_ids": [60, 61, 62, 63],
                "expected_committees": [60, 61, 62, 63],
            },
            {
                "name": "cmadAll",
                "committee_management_ids": [60],
                "payload_m_id": 1,
                "payload_group_ids": [1],
                "payload_hc_id": 60,
                "payload_cm_ids": [60, 61],
                "expected_committees": [60, 61],
            },
            {
                "name": "cmadAllDifferent",
                "committee_management_ids": [66],
                "payload_m_id": 4,
                "payload_group_ids": [4],
                "payload_hc_id": 61,
                "payload_cm_ids": [60, 62],
                "expected_committees": [60, 61, 62, 63],
            },
            {
                "name": "cmadSwitch",
                "committee_management_ids": [60],
                "payload_cm_ids": [65],
                "expected_committees": [65],
            },
            {
                "name": "cmadRmOne",
                "committee_management_ids": [60, 61],
                "payload_cm_ids": [61],
                "expected_committees": [61],
            },
            {
                "name": "cmadRmAll",
                "committee_management_ids": [60, 61],
                "payload_cm_ids": [],
                "expected_committees": [],
            },
            {
                "name": "cmadRmJoinSameCommitteeMeeting",
                "committee_management_ids": [60],
                "payload_m_id": 1,
                "payload_group_ids": [2],
                "payload_cm_ids": [],
                "expected_committees": [60],
            },
            {
                "name": "cmadRmJoinSameCommittee",
                "committee_management_ids": [60],
                "payload_hc_id": 60,
                "payload_cm_ids": [],
                "expected_committees": [60],
            },
            {
                "name": "cmadRmJoinOtherCommittee",
                "committee_management_ids": [60],
                "payload_hc_id": 61,
                "payload_cm_ids": [],
                "expected_committees": [61],
            },
            {
                "name": "all",
                "meeting_ids": [1],
                "home_committee_id": 61,
                "committee_management_ids": [62],
                "payload_m_id": 4,
                "payload_group_ids": [6],
                "payload_hc_id": 64,
                "payload_cm_ids": [65, 66],
                "expected_committees": [60, 63, 64, 65, 66],
            },
        ]
        payloads: list[dict[str, Any]] = []
        meeting_to_user_ids: dict[int, list[int]] = {i: [] for i in range(1, 8, 3)}
        committee_to_native_user_ids: dict[int, list[int]] = {
            i: [] for i in range(60, 67)
        }
        committee_to_manager_ids: dict[int, list[int]] = {i: [] for i in range(60, 67)}
        committee_to_user_ids: dict[int, set[int]] = {i: set() for i in range(60, 67)}
        committee_to_expected_user_ids: dict[int, list[int]] = {
            i: [] for i in range(60, 67)
        }
        data: dict[str, dict[str, Any]] = {}
        for testcase in testcases:
            i = self.create_user(testcase["name"])
            committee_ids: set[int] = set()
            date: dict[str, Any] = {}
            if meeting_ids := testcase.get("meeting_ids"):
                date["meeting_ids"] = meeting_ids
                date["meeting_user_ids"] = [m_id * 100 + i for m_id in meeting_ids]
                for m_id in meeting_ids:
                    data[f"meeting_user/{m_id* 100 + i}"] = {
                        "user_id": i,
                        "meeting_id": m_id,
                        "group_ids": [m_id],
                    }
                    meeting_to_user_ids[m_id].append(i)
                    committee_ids.add(m_id + 59)
                    committee_to_user_ids[m_id + 59].add(i)
            if home_committee_id := testcase.get("home_committee_id"):
                date["home_committee_id"] = home_committee_id
                committee_ids.add(home_committee_id)
                committee_to_native_user_ids[home_committee_id].append(i)
                committee_to_user_ids[home_committee_id].add(i)
            if committee_management_ids := testcase.get("committee_management_ids"):
                date["committee_management_ids"] = committee_management_ids
                committee_ids.update(committee_management_ids)
                for c_id in committee_management_ids:
                    committee_to_manager_ids[c_id].append(i)
                    committee_to_user_ids[c_id].add(i)
            date["committee_ids"] = sorted(list(committee_ids))
            data[f"user/{i}"] = date
            payload: dict[str, Any] = {"id": i}
            if meeting_id := testcase.get("payload_m_id"):
                payload["meeting_id"] = meeting_id
                payload["group_ids"] = testcase.get("payload_group_ids", [])
            if home_committee_id := testcase.get("payload_hc_id"):
                payload["home_committee_id"] = home_committee_id
            elif home_committee_id == 0:
                payload["home_committee_id"] = None
            if (committee_management_ids := testcase.get("payload_cm_ids")) is not None:
                payload["committee_management_ids"] = committee_management_ids
            payloads.append(payload)
            for c_id in testcase["expected_committees"]:
                committee_to_expected_user_ids[c_id].append(i)
        data.update(
            {
                **{
                    f"meeting/{id_}": {
                        "user_ids": user_ids,
                        "meeting_user_ids": [id_ * 100 + u_id for u_id in user_ids],
                    }
                    for id_, user_ids in meeting_to_user_ids.items()
                },
                **{
                    f"group/{id_}": {
                        "meeting_user_ids": [id_ * 100 + u_id for u_id in user_ids],
                    }
                    for id_, user_ids in meeting_to_user_ids.items()
                },
                **{
                    f"committee/{id_}": {
                        "user_ids": sorted(list(user_ids)),
                        "native_user_ids": committee_to_native_user_ids[id_],
                        "manager_ids": committee_to_manager_ids[id_],
                    }
                    for id_, user_ids in committee_to_user_ids.items()
                },
            }
        )
        self.set_models(data)

        response = self.request_multi("user.update", payloads)

        self.assert_status_code(response, 200)
        for i, ids in committee_to_expected_user_ids.items():
            comm = sorted(self.get_model(f"committee/{i}").get("user_ids", []))
            assert comm == ids
        for i, testcase in enumerate(testcases, 2):
            user = sorted(self.get_model(f"user/{i}").get("committee_ids", []))
            assert user == testcase["expected_committees"]

    def test_update_with_home_committee_as_multi_meeting_admin_group_A(self) -> None:
        self.create_committee(8)
        self.create_meeting()
        self.create_meeting(4)
        self.create_meeting(7)
        alice_id = self.create_user("alice", [1, 4, 7], home_committee_id=8)
        self.set_user_groups(1, [2, 5, 8])
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {
                "id": alice_id,
                "first_name": "Alice",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 8",
            response.json["message"],
        )

    def test_update_with_home_committee_as_multi_committee_admin_group_A(self) -> None:
        self.create_committee(8)
        self.create_meeting()
        self.create_meeting(4)
        self.create_meeting(7)
        alice_id = self.create_user("alice", [1, 4, 7], home_committee_id=8)
        self.set_committee_management_level([60, 63, 66])
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {
                "id": alice_id,
                "first_name": "Alice",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 8",
            response.json["message"],
        )

    def test_update_with_home_committee_as_multi_meeting_admin_group_F(self) -> None:
        self.create_committee(8)
        self.create_meeting()
        self.create_meeting(4)
        self.create_meeting(7)
        alice_id = self.create_user("alice", [1, 4, 7], home_committee_id=8)
        self.set_user_groups(1, [2, 5, 8])
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {
                "id": alice_id,
                "default_password": "defP",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 8",
            response.json["message"],
        )

    def test_update_with_home_committee_as_multi_committee_admin_group_F(self) -> None:
        self.create_committee(8)
        self.create_meeting()
        self.create_meeting(4)
        self.create_meeting(7)
        alice_id = self.create_user("alice", [1, 4, 7], home_committee_id=8)
        self.set_committee_management_level([60, 63, 66])
        self.set_organization_management_level(None)
        response = self.request(
            "user.update",
            {
                "id": alice_id,
                "default_password": "defP",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 8",
            response.json["message"],
        )


class UserUpdateHomeCommitteePermissionTest(BaseActionTestCase):
    committeePerms: set[int] = set()
    baseCommitteePerms: set[int] = set()
    meetingPerms: set[int] = set()
    ownOml: OrganizationManagementLevel | None = None
    userOml: OrganizationManagementLevel | None = None
    lock_meeting_1: bool = False

    def setUp(self) -> None:
        super().setUp()
        self.lowerOml = self.userOml and (not self.ownOml or self.ownOml < self.userOml)
        if not self.baseCommitteePerms:
            self.baseCommitteePerms = self.committeePerms
        self.create_meeting()
        self.create_meeting(4)
        self.create_user(
            "Bob", organization_management_level=self.userOml, home_committee_id=60
        )
        self.set_organization_management_level(self.ownOml)
        if self.baseCommitteePerms:
            self.set_committee_management_level(
                committee_ids=list(self.baseCommitteePerms)
            )
        if self.meetingPerms:
            self.set_user_groups(1, [id_ + 1 for id_ in self.meetingPerms])
        if self.lock_meeting_1:
            self.set_models({"meeting/1": {"locked_from_inside": True}})

    def update_with_home_committee_group_A(self) -> None:
        response = self.request(
            "user.update",
            {
                "id": 2,
                "username": "BobTheBuilder",
            },
        )
        if self.lowerOml:
            self.assertIn(
                "Your organization management level is not high enough to change a user with a Level of superadmin!",
                response.json["message"],
            )
        elif 60 not in self.committeePerms and not self.ownOml:
            self.assert_status_code(response, 403)
            self.assertIn(
                "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 60",
                response.json["message"],
            )
        else:
            self.assert_status_code(response, 200)
            self.assert_model_exists("user/2", {"username": "BobTheBuilder"})

    def update_with_home_committee_group_B(self) -> None:
        m_user_ids = self.set_user_groups(2, [1])
        response = self.request(
            "user.update",
            {
                "id": 2,
                "meeting_id": 1,
                "number": "No.1",
            },
        )
        no_low_level_perms = (
            1 not in self.meetingPerms and 60 not in self.committeePerms
        )
        if self.lock_meeting_1 and 1 not in self.meetingPerms:
            self.assert_status_code(response, 403)
            self.assertIn(
                "The user needs Permission user.can_update for meeting 1",
                response.json["message"],
            )
        elif no_low_level_perms and not self.ownOml:
            # Fails in group C check
            self.assert_status_code(response, 403)
            self.assertIn(
                "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_update for meeting 1",
                response.json["message"],
            )
        elif (
            no_low_level_perms
            and self.ownOml == OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            # Fails in group B check
            self.assert_status_code(response, 403)
            self.assertIn(
                "You are not allowed to perform action user.update. Missing permission: Permission user.can_update in meeting 1",
                response.json["message"],
            )
        else:
            self.assert_status_code(response, 200)
            self.assert_model_exists(
                f"meeting_user/{m_user_ids[0]}", {"number": "No.1"}
            )

    def update_with_home_committee_group_B_other_committee_meeting(self) -> None:
        m_user_ids = self.set_user_groups(2, [4])
        response = self.request(
            "user.update",
            {
                "id": 2,
                "meeting_id": 4,
                "number": "No.1",
            },
        )
        no_low_level_perms = (
            4 not in self.meetingPerms and 63 not in self.committeePerms
        )
        if no_low_level_perms and not self.ownOml:
            # Fails in group C check
            self.assert_status_code(response, 403)
            self.assertIn(
                "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_update for meeting 4",
                response.json["message"],
            )
        elif (
            no_low_level_perms
            and self.ownOml == OrganizationManagementLevel.CAN_MANAGE_USERS
        ):
            # Fails in group B check
            self.assert_status_code(response, 403)
            self.assertIn(
                "You are not allowed to perform action user.update. Missing permission: Permission user.can_update in meeting 4",
                response.json["message"],
            )
        else:
            self.assert_status_code(response, 200)
            self.assert_model_exists(
                f"meeting_user/{m_user_ids[0]}", {"number": "No.1"}
            )

    def update_with_home_committee_group_C(self) -> None:
        self.set_user_groups(2, [1])
        response = self.request(
            "user.update",
            {"id": 2, "meeting_id": 1, "group_ids": [1]},
        )
        if self.lock_meeting_1 and 1 not in self.meetingPerms:
            self.assert_status_code(response, 403)
            self.assertIn(
                "The user needs Permission user.can_update for meeting 1",
                response.json["message"],
            )
        elif (
            1 not in self.meetingPerms
            and 60 not in self.committeePerms
            and not self.ownOml
        ):
            self.assert_status_code(response, 403)
            self.assertIn(
                "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_update for meeting 1",
                response.json["message"],
            )
        else:
            self.assert_status_code(response, 200)
            meeting_users = [
                self.get_model(f"meeting_user/{id_}")
                for id_ in self.get_model("user/2")["meeting_user_ids"]
            ]
            assert (
                meeting_user := meeting_users[
                    [m_user["meeting_id"] == 1 for m_user in meeting_users].index(True)
                ]
            )
            assert meeting_user.get("meeting_id") == 1
            assert meeting_user.get("group_ids") == [1]

    def update_with_home_committee_group_D(self) -> None:
        response = self.request(
            "user.update",
            {
                "id": 2,
                "committee_management_ids": [60],
            },
        )
        if self.lowerOml:
            self.assertIn(
                "Your organization management level is not high enough to change a user with a Level of superadmin!",
                response.json["message"],
            )
        elif 60 not in self.committeePerms and not self.ownOml:
            self.assert_status_code(response, 403)
            self.assertIn(
                "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee 60",
                response.json["message"],
            )
        else:
            self.assert_status_code(response, 200)
            self.assert_model_exists("user/2", {"committee_management_ids": [60]})

    def update_with_home_committee_group_D_other_committee(self) -> None:
        response = self.request(
            "user.update",
            {
                "id": 2,
                "committee_management_ids": [63],
            },
        )
        if self.lowerOml:
            self.assertIn(
                "Your organization management level is not high enough to change a user with a Level of superadmin!",
                response.json["message"],
            )
        elif 63 not in self.committeePerms and not self.ownOml:
            self.assert_status_code(response, 403)
            self.assertIn(
                "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee 63",
                response.json["message"],
            )
        else:
            self.assert_status_code(response, 200)
            self.assert_model_exists("user/2", {"committee_management_ids": [63]})

    def update_with_home_committee_group_E(self) -> None:
        response = self.request(
            "user.update",
            {
                "id": 2,
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
        if self.lowerOml:
            self.assertIn(
                "Your organization management level is not high enough to change a user with a Level of superadmin!",
                response.json["message"],
            )
        elif not self.ownOml:
            self.assert_status_code(response, 403)
            self.assertIn(
                "Your organization management level is not high enough to set a Level of can_manage_users",
                response.json["message"],
            )
        else:
            self.assert_status_code(response, 200)
            self.assert_model_exists(
                "user/2",
                {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                },
            )

    def update_with_home_committee_group_F(self) -> None:
        response = self.request(
            "user.update",
            {
                "id": 2,
                "default_password": "defP",
            },
        )
        if self.lowerOml:
            self.assertIn(
                "Your organization management level is not high enough to change a user with a Level of superadmin!",
                response.json["message"],
            )
        elif 60 not in self.committeePerms and not self.ownOml:
            self.assert_status_code(response, 403)
            self.assertIn(
                "You are not allowed to perform action user.update. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 60",
                response.json["message"],
            )
        else:
            self.assert_status_code(response, 200)
            self.assert_model_exists("user/2", {"default_password": "defP"})

    def update_with_home_committee_group_G(self) -> None:
        response = self.request(
            "user.update",
            {
                "id": 2,
                "is_demo_user": True,
            },
        )
        if self.lowerOml:
            self.assertIn(
                "Your organization management level is not high enough to change a user with a Level of superadmin!",
                response.json["message"],
            )
        elif not self.ownOml or self.ownOml < OrganizationManagementLevel.SUPERADMIN:
            self.assert_status_code(response, 403)
            self.assertIn(
                "You are not allowed to perform action user.update. Missing OrganizationManagementLevel: superadmin",
                response.json["message"],
            )
        else:
            self.assert_status_code(response, 200)
            self.assert_model_exists("user/2", {"is_demo_user": True})


class UserUpdateHomeCommitteePermissionTestNoPermissions(
    UserUpdateHomeCommitteePermissionTest
):
    def test_update_with_home_committee_group_A_no_perm(self) -> None:
        self.update_with_home_committee_group_A()

    def test_update_with_home_committee_group_B_no_perm(self) -> None:
        self.update_with_home_committee_group_B()


class UserUpdateHomeCommitteePermissionTestAsMeetingAdmin(
    UserUpdateHomeCommitteePermissionTest
):
    meetingPerms: set[int] = {1}

    def test_update_with_home_committee_group_A_as_meeting_admin(self) -> None:
        self.update_with_home_committee_group_A()

    def test_update_with_home_committee_group_B_as_meeting_admin(self) -> None:
        self.update_with_home_committee_group_B()

    def test_update_with_home_committee_group_B_other_committee_meeting_as_meeting_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_B_other_committee_meeting()

    def test_update_with_home_committee_group_C_as_meeting_admin(self) -> None:
        self.update_with_home_committee_group_C()

    def test_update_with_home_committee_group_F_as_meeting_admin(self) -> None:
        self.update_with_home_committee_group_F()


class UserUpdateHomeCommitteePermissionTestAsCommitteeAdmin(
    UserUpdateHomeCommitteePermissionTest
):
    committeePerms: set[int] = {60}

    def test_update_with_home_committee_group_A_as_committee_admin(self) -> None:
        self.update_with_home_committee_group_A()

    def test_update_with_home_committee_group_B_as_committee_admin(self) -> None:
        self.update_with_home_committee_group_B()

    def test_update_with_home_committee_group_B_other_committee_meeting_as_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_B_other_committee_meeting()

    def test_update_with_home_committee_group_C_as_committee_admin(self) -> None:
        self.update_with_home_committee_group_C()

    def test_update_with_home_committee_group_D_as_committee_admin(self) -> None:
        self.update_with_home_committee_group_D()

    def test_update_with_home_committee_group_D_other_committee_as_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_D_other_committee()

    def test_update_with_home_committee_group_E_as_committee_admin(self) -> None:
        self.update_with_home_committee_group_E()

    def test_update_with_home_committee_group_F_as_committee_admin(self) -> None:
        self.update_with_home_committee_group_F()

    def test_update_with_home_committee_group_G_as_committee_admin(self) -> None:
        self.update_with_home_committee_group_G()


class UserUpdateHomeCommitteePermissionTestAsForeignCommitteeAdmin(
    UserUpdateHomeCommitteePermissionTest
):
    committeePerms: set[int] = {63}

    def test_update_with_home_committee_group_A_as_foreign_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_A()

    def test_update_with_home_committee_group_B_as_foreign_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_B()

    def test_update_with_home_committee_group_C_as_foreign_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_C()

    def test_update_with_home_committee_group_D_as_foreign_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_D()

    def test_update_with_home_committee_group_D_other_committee_as_foreign_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_D_other_committee()


class UserUpdateHomeCommitteePermissionTestAsUserAdmin(
    UserUpdateHomeCommitteePermissionTest
):
    ownOml: OrganizationManagementLevel | None = (
        OrganizationManagementLevel.CAN_MANAGE_USERS
    )

    def test_update_with_home_committee_group_A_as_user_admin(self) -> None:
        self.update_with_home_committee_group_A()

    def test_update_with_home_committee_group_B_as_user_admin(self) -> None:
        self.update_with_home_committee_group_B()

    def test_update_with_home_committee_group_C_as_user_admin(self) -> None:
        self.update_with_home_committee_group_C()

    def test_update_with_home_committee_group_D_as_user_admin(self) -> None:
        self.update_with_home_committee_group_D()

    def test_update_with_home_committee_group_E_as_user_admin(self) -> None:
        self.update_with_home_committee_group_E()

    def test_update_with_home_committee_group_F_as_user_admin(self) -> None:
        self.update_with_home_committee_group_F()


class UserUpdateHomeCommitteePermissionTestAsOrgaAdmin(
    UserUpdateHomeCommitteePermissionTest
):
    ownOml: OrganizationManagementLevel | None = (
        OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    )

    def test_update_with_home_committee_group_E_as_orga_admin(self) -> None:
        self.update_with_home_committee_group_E()

    def test_update_with_home_committee_group_F_as_orga_admin(self) -> None:
        self.update_with_home_committee_group_F()

    def test_update_with_home_committee_group_G_as_orga_admin(self) -> None:
        self.update_with_home_committee_group_G()


class UserUpdateHomeCommitteePermissionTestAsSuperadmin(
    UserUpdateHomeCommitteePermissionTest
):
    ownOml: OrganizationManagementLevel | None = OrganizationManagementLevel.SUPERADMIN

    def test_update_with_home_committee_group_F_as_superadmin(self) -> None:
        self.update_with_home_committee_group_F()

    def test_update_with_home_committee_group_G_as_superadmin(self) -> None:
        self.update_with_home_committee_group_G()


class UserUpdateHomeCommitteePermissionTestAsLowerOml(
    UserUpdateHomeCommitteePermissionTest
):
    ownOml: OrganizationManagementLevel | None = (
        OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    )
    userOml: OrganizationManagementLevel | None = OrganizationManagementLevel.SUPERADMIN

    def test_update_with_home_committee_group_A_as_lower_oml(self) -> None:
        self.update_with_home_committee_group_A()

    def test_update_with_home_committee_group_B_as_lower_oml(self) -> None:
        self.update_with_home_committee_group_B()

    def test_update_with_home_committee_group_E_as_lower_oml(self) -> None:
        self.update_with_home_committee_group_E()

    def test_update_with_home_committee_group_F_as_lower_oml(self) -> None:
        self.update_with_home_committee_group_F()


class UserUpdateHomeCommitteeTraditionalOrgaScopePermissionTestAsMeetingAdmin(
    UserUpdateHomeCommitteePermissionTest
):
    meetingPerms: set[int] = {1}

    def setUp(self) -> None:
        super().setUp()
        self.set_user_groups(2, [4])

    def test_update_with_home_committee_old_orga_scope_group_B_as_meeting_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_B()

    def test_update_with_home_committee_old_orga_scope_group_B_other_committee_meeting_as_meeting_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_B_other_committee_meeting()

    def test_update_with_home_committee_old_orga_scope_group_C_as_meeting_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_C()

    def test_update_with_home_committee_old_orga_scope_group_F_as_meeting_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_F()


class UserUpdateHomeCommitteeTraditionalOrgaScopePermissionTestAsCommitteeAdmin(
    UserUpdateHomeCommitteePermissionTest
):
    committeePerms: set[int] = {60}

    def setUp(self) -> None:
        super().setUp()
        self.set_user_groups(2, [4])

    def test_update_with_home_committee_old_orga_scope_group_A_as_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_A()

    def test_update_with_home_committee_old_orga_scope_group_B_as_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_B()

    def test_update_with_home_committee_old_orga_scope_group_B_other_committee_meeting_as_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_B_other_committee_meeting()

    def test_update_with_home_committee_old_orga_scope_group_C_as_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_C()

    def test_update_with_home_committee_old_orga_scope_group_D_as_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_D()

    def test_update_with_home_committee_old_orga_scope_group_F_as_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_F()


class UserUpdateHomeCommitteeLockedMeetingPermissionTestAsMeetingAdmin(
    UserUpdateHomeCommitteePermissionTest
):
    meetingPerms: set[int] = {1}
    lock_meeting_1 = True

    def test_update_with_home_committee_locked_meeting_group_B_as_meeting_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_B()

    def test_update_with_home_committee_locked_meeting_group_C_as_meeting_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_C()


class UserUpdateHomeCommitteeLockedMeetingPermissionTestAsCommitteeAdmin(
    UserUpdateHomeCommitteePermissionTest
):
    committeePerms: set[int] = {60}
    lock_meeting_1 = True

    def test_update_with_home_committee_locked_meeting_group_B_as_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_B()

    def test_update_with_home_committee_locked_meeting_group_C_as_committee_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_C()


class UserUpdateHomeCommitteeLockedMeetingPermissionTestAsUserManager(
    UserUpdateHomeCommitteePermissionTest
):
    ownOml: OrganizationManagementLevel | None = (
        OrganizationManagementLevel.CAN_MANAGE_USERS
    )
    lock_meeting_1 = True

    def test_update_with_home_committee_locked_meeting_group_B_as_user_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_B()

    def test_update_with_home_committee_locked_meeting_group_C_as_user_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_C()


class UserUpdateHomeCommitteeLockedMeetingPermissionTestAsOrgaAdmin(
    UserUpdateHomeCommitteePermissionTest
):
    ownOml: OrganizationManagementLevel | None = (
        OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    )
    lock_meeting_1 = True

    def test_update_with_home_committee_locked_meeting_group_B_as_orga_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_B()

    def test_update_with_home_committee_locked_meeting_group_C_as_orga_admin(
        self,
    ) -> None:
        self.update_with_home_committee_group_C()


class UserUpdateHomeCommitteePermissionTestAsParentCommitteeAdmin(
    UserUpdateHomeCommitteePermissionTest
):
    baseCommitteePerms: set[int] = {50}
    committeePerms: set[int] = {50, 60}

    def setUp(self) -> None:
        super().setUp()
        self.create_committee(50)
        self.create_committee(60, parent_id=50)

    def test_update_with_home_committee_group_A_as_parent_committee_admin(self) -> None:
        self.update_with_home_committee_group_A()

    def test_update_with_home_committee_group_B_as_parent_committee_admin(self) -> None:
        self.update_with_home_committee_group_B()

    def test_update_with_home_committee_group_C_as_parent_committee_admin(self) -> None:
        self.update_with_home_committee_group_C()

    def test_update_with_home_committee_group_D_as_parent_committee_admin(self) -> None:
        self.update_with_home_committee_group_D()

    def test_update_with_home_committee_group_E_as_parent_committee_admin(self) -> None:
        self.update_with_home_committee_group_E()

    def test_update_with_home_committee_group_F_as_parent_committee_admin(self) -> None:
        self.update_with_home_committee_group_F()

    def test_update_with_home_committee_group_G_as_parent_committee_admin(self) -> None:
        self.update_with_home_committee_group_G()
