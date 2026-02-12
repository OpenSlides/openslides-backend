from decimal import Decimal
from typing import Any

from openslides_backend.action.util.crypto import PASSWORD_CHARS
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase

from ..test_internal_actions import BaseInternalActionTest


class UserCreateActionTest(BaseActionTestCase):
    def permission_setup(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("test", group_ids=[1])
        self.login(self.user_id)

    def test_create_username(self) -> None:
        """
        Also checks if a default_password is generated and the correct hashed password stored
        """
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/2")
        assert model.get("username") == "test_Xcdfgee"
        assert (password := model.get("default_password")) is not None
        assert all(char in PASSWORD_CHARS for char in password)
        assert self.auth.is_equal(password, model.get("password", ""))
        assert response.json["results"][0][0] == {"id": 2}
        self.assert_history_information("user/2", ["Account created"])

    def test_create_first_and_last_name(self) -> None:
        response = self.request(
            "user.create",
            {
                "first_name": " John Aloas ",
                "last_name": " Smith Brick ",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "JohnAloasSmithBrick"})

    def test_create_name_with_connecting_minus(self) -> None:
        response = self.request(
            "user.create",
            {
                "first_name": " John-Aloas ",
                "last_name": " Smith-Brick ",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "JohnAloasSmithBrick"})

    def test_create_first_name_and_count(self) -> None:
        self.set_models(
            {"user/2": {"username": "John"}, "user/3": {"username": "John1"}}
        )
        response = self.request(
            "user.create",
            {
                "first_name": "John",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/4", {"username": "John2"})

    def test_create_some_more_fields(self) -> None:
        """
        Also checks if the correct password is stored from the given default_password
        """
        self.create_meeting(110)
        self.create_meeting(114)
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_DsJFXoot",
                    "committee_id": 78,
                    "is_active_in_organization_id": 1,
                },
                "meeting/114": {
                    "name": "name_xXRGTLAJ",
                    "committee_id": 79,
                    "is_active_in_organization_id": 1,
                },
                "committee/78": {"name": "name_TSXpBGdt", "meeting_ids": [110]},
                "committee/79": {"name": "name_hOldWvVF", "meeting_ids": [114]},
            }
        )
        response = self.request(
            "user.create",
            {
                "pronoun": "Test",
                "username": "test_Xcdfgee",
                "default_vote_weight": "1.500000",
                "organization_management_level": "can_manage_users",
                "default_password": "password",
                "committee_management_ids": [78],
                "meeting_id": 114,
                "group_ids": [114],
                "member_number": "abcdefg1234567",
            },
        )
        self.assert_status_code(response, 200)
        user2 = self.assert_model_exists(
            "user/2",
            {
                "pronoun": "Test",
                "username": "test_Xcdfgee",
                "default_vote_weight": Decimal("1.500000"),
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                "default_password": "password",
                "committee_management_ids": [78],
                "meeting_user_ids": [1],
                "member_number": "abcdefg1234567",
                "committee_ids": [78, 79],
            },
        )
        assert self.auth.is_equal(
            user2.get("default_password", ""), user2.get("password", "")
        )
        result = response.json["results"][0][0]
        assert result == {"id": 2, "meeting_user_id": 1}
        self.assert_model_exists(
            "meeting_user/1", {"meeting_id": 114, "user_id": 2, "group_ids": [114]}
        )
        self.assert_model_exists(
            "committee/78", {"meeting_ids": [110], "user_ids": [2]}
        )
        self.assert_model_exists(
            "committee/79", {"meeting_ids": [114], "user_ids": [2]}
        )
        self.assert_history_information(
            "user/2",
            [
                "Account created",
                "Participant added to meeting {}.",
                "meeting/114",
                "Participant added to group {} in meeting {}.",
                "group/114",
                "meeting/114",
            ],
        )

    def test_create_comment(self) -> None:
        self.create_meeting()
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "comment": "blablabla",
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2", {"username": "test_Xcdfgee", "meeting_user_ids": [1]}
        )
        result = response.json["results"][0][0]
        assert result == {"id": 2, "meeting_user_id": 1}
        self.assert_model_exists(
            "meeting_user/1", {"meeting_id": 1, "user_id": 2, "comment": "blablabla"}
        )

    def test_create_comment_without_meeting_id(self) -> None:
        self.create_meeting()
        response = self.request(
            "user.create",
            {"username": "test_Xcdfgee", "group_ids": [3]},
        )
        self.assert_status_code(response, 400)
        assert (
            "Missing meeting_id in instance, because meeting related fields used"
            in response.json["message"]
        )

    def test_create_with_meeting_user_fields(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "committee/2": {"name": "C2"},
                "user/222": {"username": "timtari"},
                "structure_level/31": {"name": "Gondor", "meeting_id": 1},
            }
        )
        self.set_user_groups(222, [1])
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "meeting_id": 1,
                "group_ids": [3],
                "vote_delegations_from_ids": [1],
                "comment": "comment<iframe></iframe>",
                "number": "number1",
                "structure_level_ids": [31],
                "about_me": "<p>about</p><iframe></iframe>",
                "vote_weight": "1.000000",
                "committee_management_ids": [2],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/223",
            {
                "committee_management_ids": [2],
                "committee_ids": [2, 60],
                "meeting_user_ids": [2],
                "meeting_ids": [1],
            },
        )
        result = response.json["results"][0][0]
        assert result == {"id": 223, "meeting_user_id": 2}
        self.assert_model_exists(
            "meeting_user/2",
            {
                "group_ids": [3],
                "vote_delegations_from_ids": [1],
                "comment": "comment&lt;iframe&gt;&lt;/iframe&gt;",
                "number": "number1",
                "structure_level_ids": [31],
                "about_me": "<p>about</p>&lt;iframe&gt;&lt;/iframe&gt;",
                "vote_weight": Decimal("1.000000"),
            },
        )
        self.assert_model_exists("user/222", {"meeting_user_ids": [1]})
        self.assert_model_exists("meeting_user/1", {"vote_delegated_to_id": 2})
        self.assert_model_exists("group/3", {"meeting_user_ids": [2]})
        self.assert_model_exists("meeting/1", {"user_ids": [222, 223]})

    def test_invalid_committee_management_ids(self) -> None:
        self.create_committee()
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "committee_management_ids": [2],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn("'committee/2' does not exist.", response.json["message"])

    def test_invalid_invalid_meeting_for_meeting_user(self) -> None:
        self.create_meeting()
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "meeting_id": 2,
                "comment": "comment",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "'meeting/2' does not exist",
            response.json["message"],
        )

    def test_create_invalid_group_id(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.set_models(
            {
                "committee/60": {"meeting_ids": [1, 4]},
                "meeting/4": {"committee_id": 60},
            }
        )
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "meeting_id": 4,
                "group_ids": [3],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 4: ['group/3']",
            response.json["message"],
        )

    def test_create_broken_email(self) -> None:
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "email": "broken@@",
            },
        )
        self.assert_status_code(response, 400)
        assert "email must be valid email." in response.json["message"]

    def test_create_empty_data(self) -> None:
        response = self.request("user.create", {})
        self.assert_status_code(response, 400)
        assert "Need username or first_name or last_name" in response.json["message"]

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "user.create", {"wrong_field": "text_AefohteiF8", "username": "test1"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_username_already_exists(self) -> None:
        response = self.request(
            "user.create",
            {
                "username": "admin",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"] == "A user with the username admin already exists."
        )

    def test_member_number_already_exists(self) -> None:
        response = self.request(
            "user.create",
            {"username": "user1", "member_number": "14m4m3m832"},
        )
        self.assert_status_code(response, 200)
        response = self.request(
            "user.create",
            {"username": "user2", "member_number": "14m4m3m832"},
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "A user with the member_number 14m4m3m832 already exists."
        )

    def test_member_number_none(self) -> None:
        response = self.request(
            "user.create",
            {"username": "user2", "member_number": None},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"member_number": None})

    def test_user_create_with_empty_vote_delegation_from_ids(self) -> None:
        self.create_meeting()
        response = self.request(
            "user.create",
            {
                "username": "testname",
                "meeting_id": 1,
                "group_ids": [3],
                "vote_delegations_from_ids": [],
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2", {"username": "testname", "meeting_user_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/1",
            {"meeting_id": 1, "user_id": 2, "vote_delegations_from_ids": None},
        )

    def test_create_committee_manager_without_committee_ids(self) -> None:
        """create has to add a missing committee to the user, because cml permission is demanded"""
        self.set_models(
            {
                "committee/60": {"name": "c60"},
                "committee/63": {"name": "c63"},
            }
        )

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "committee_management_ids": [60, 63],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "committee_ids": [60, 63],
                "committee_management_ids": [60, 63],
            },
        )
        self.assert_model_exists("committee/60", {"manager_ids": [2], "user_ids": [2]})
        self.assert_model_exists("committee/63", {"manager_ids": [2], "user_ids": [2]})

    def test_create_empty_username(self) -> None:
        response = self.request("user.create", {"username": ""})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.username must be longer than or equal to 1 characters",
            response.json["message"],
        )

    def test_create_user_without_explicit_scope(self) -> None:
        response = self.request("user.create", {"username": "user/2"})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "meeting_ids": None,
                "organization_management_level": None,
                "committee_management_ids": None,
            },
        )

    def test_create_strip_spaces(self) -> None:
        response = self.request(
            "user.create",
            {
                "first_name": " first name test ",
                "last_name": " last name test ",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "firstnametestlastnametest",
                "first_name": "first name test",
                "last_name": "last name test",
            },
        )

    def test_create_permission_nothing(self) -> None:
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "username",
                "meeting_id": 1,
                "vote_weight": "1.000000",
                "group_ids": [1],
            },
            custom_error_message="The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_manage for meeting 1",
        )

    def test_create_permission_auth_error(self) -> None:
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "username_Neu",
                "meeting_id": 1,
                "vote_weight": "1.000000",
                "group_ids": [1],
            },
            anonymous=True,
            custom_error_message="Anonymous is not allowed to execute user.create",
        )

    def test_create_permission_superadmin(self) -> None:
        """
        SUPERADMIN may set fields of all groups and may set an other user as SUPERADMIN, too.
        The SUPERADMIN don't need to belong to a meeting in any way to change data!
        """
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "username_new",
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "meeting_id": 1,
                "vote_weight": "1.000000",
                "group_ids": [1],
            },
            permission=OrganizationManagementLevel.SUPERADMIN,
        )
        self.assert_model_exists(
            "user/3",
            {
                "username": "username_new",
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "meeting_user_ids": [2],
                "meeting_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "user_id": 3,
                "meeting_id": 1,
                "vote_weight": Decimal("1.000000"),
                "group_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "user_id": 3,
                "meeting_id": 1,
                "vote_weight": Decimal("1.000000"),
                "group_ids": [1],
            },
        )

    def test_create_permission_group_A_oml_manage_user(self) -> None:
        """May create group A fields on organsisation scope, because belongs to 2 meetings in 2 committees, requiring OML level permission"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
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

        response = self.request_json(
            [
                {
                    "action": "user.create",
                    "data": [
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
                            "meeting_id": 1,
                            "group_ids": [1],
                        }
                    ],
                },
                {
                    "action": "user.update",
                    "data": [
                        {
                            "id": 3,
                            "meeting_id": 4,
                            "group_ids": [4],
                        }
                    ],
                },
            ],
            atomic=False,
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/3",
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
                "default_vote_weight": Decimal("1.234000"),
                "can_change_own_password": False,
                "committee_ids": [60, 63],
                "meeting_ids": [1, 4],
                "meeting_user_ids": [2, 3],
            },
        )
        self.assert_model_exists("meeting_user/2", {"meeting_id": 1, "group_ids": [1]})
        self.assert_model_exists("meeting_user/3", {"meeting_id": 4, "group_ids": [4]})

    def test_create_permission_group_A_cml_manage_user(self) -> None:
        """May create group A fields on cml scope"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_models(
            {
                f"user/{self.user_id}": {"committee_ids": [60]},
                "meeting/4": {"committee_id": 60, "is_active_in_organization_id": 1},
                "committee/60": {
                    "name": "minish council",
                    "meeting_ids": [1, 4],
                    "manager_ids": [self.user_id],
                },
            }
        )

        response = self.request_json(
            [
                {
                    "action": "user.create",
                    "data": [
                        {
                            "username": "usersname",
                            "meeting_id": 1,
                            "group_ids": [1],
                        }
                    ],
                },
                {
                    "action": "user.update",
                    "data": [
                        {
                            "id": 3,
                            "meeting_id": 4,
                            "group_ids": [4],
                        }
                    ],
                },
            ],
            atomic=False,
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/3",
            {
                "username": "usersname",
                "meeting_ids": [1, 4],
                "committee_ids": [60],
                "meeting_user_ids": [2, 3],
            },
        )
        self.assert_model_exists("meeting_user/2", {"meeting_id": 1, "group_ids": [1]})
        self.assert_model_exists("meeting_user/3", {"meeting_id": 4, "group_ids": [4]})

    def test_create_permission_group_A_user_can_manage(self) -> None:
        """May create group A fields on meeting scope"""
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 1,
                "group_ids": [1],
            },
            user_groups=[2],  # Admin group of meeting/1
            fail=False,
        )
        self.assert_model_exists(
            "user/3",
            {
                "username": "usersname",
                "meeting_user_ids": [2],
                "meeting_ids": [1],
                "committee_ids": [60],
            },
        )
        self.assert_model_exists("meeting_user/2", {"meeting_id": 1, "group_ids": [1]})

    def test_create_permission_group_A_both_committee_permissions(self) -> None:
        """May not create group A fields on organsisation scope, although having both committee permissions"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_models(
            {
                f"user/{self.user_id}": {
                    "committee_ids": [60, 63],
                },
                "committee/60": {"manager_ids": [self.user_id]},
                "committee/63": {"manager_ids": [self.user_id]},
            }
        )

        response = self.request(
            "user.create",
            {
                "username": "new_username",
                "committee_management_ids": [60],
                "meeting_id": 4,
                "group_ids": [4],
            },
        )
        self.assert_status_code(response, 200)

    def test_create_permission_group_B_user_can_manage(self) -> None:
        """create group B fields with simple user.can_manage permissions"""
        self.create_meeting()
        self.set_organization_management_level(None)
        self.set_user_groups(1, [2])  # Admin groups of meeting/1

        self.set_models(
            {
                "user/5": {"username": "user5"},
                "user/6": {"username": "user6"},
                "structure_level/31": {"name": "user 4 alone", "meeting_id": 1},
            }
        )
        self.set_user_groups(5, [1])
        self.set_user_groups(6, [1])

        response = self.request(
            "user.create",
            {
                "username": "username7",
                "meeting_id": 1,
                "number": "number1",
                "structure_level_ids": [31],
                "vote_weight": "12.002345",
                "about_me": "about me 1",
                "comment": "comment for meeting/1",
                "vote_delegations_from_ids": [2, 3],
                "group_ids": [1],
                "is_present_in_meeting_ids": [1],
                "locked_out": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/7",
            {
                "username": "username7",
                "meeting_ids": [1],
                "meeting_user_ids": [4],
                "is_present_in_meeting_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/4",
            {
                "meeting_id": 1,
                "user_id": 7,
                "number": "number1",
                "structure_level_ids": [31],
                "vote_weight": Decimal("12.002345"),
                "about_me": "about me 1",
                "comment": "comment for meeting/1",
                "vote_delegations_from_ids": [2, 3],
                "group_ids": [1],
                "locked_out": True,
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "meeting_id": 1,
                "user_id": 5,
                "vote_delegated_to_id": 4,
            },
        )
        self.assert_model_exists(
            "meeting_user/3",
            {
                "meeting_id": 1,
                "user_id": 6,
                "vote_delegated_to_id": 4,
            },
        )

    def test_create_permission_group_B_user_can_manage_no_permission(self) -> None:
        """Group B fields needs explicit user.can_manage permission for meeting"""
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 1,
                "group_ids": [1],
                "is_present_in_meeting_ids": [1],
                "number": "number1",
            },
            OrganizationManagementLevel.CAN_MANAGE_USERS,
            custom_error_message="You are not allowed to perform action user.create. Missing permission: Permission user.can_manage in meeting 1",
        )

    def test_create_permission_group_B_locked_meeting(self) -> None:
        """Group B fields needs explicit user.can_manage permission for meeting"""
        self.create_meeting(4)
        self.set_models({"meeting/4": {"locked_from_inside": True}})
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 4,
                "group_ids": [4],
                "is_present_in_meeting_ids": [4],
                "number": "number1",
            },
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            custom_error_message="The user needs Permission user.can_manage for meeting 4",
        )

    def test_create_permission_group_B_locked_meeting_with_perm(self) -> None:
        """Group B fields needs explicit user.can_manage permission for meeting"""
        self.create_meeting(4, meeting_data={"locked_from_inside": True})

        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 4,
                "group_ids": [4],
                "is_present_in_meeting_ids": [4],
                "number": "number1",
            },
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            user_groups=[5],
        )

    def test_create_permission_group_C_oml_manager(self) -> None:
        """May create group C group_ids by OML permission"""
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 1,
                "group_ids": [1],
            },
            OrganizationManagementLevel.CAN_MANAGE_USERS,
        )
        self.assert_model_exists("user/3", {"meeting_user_ids": [2]})
        self.assert_model_exists("meeting_user/2", {"group_ids": [1]})

    def test_create_permission_group_C_locked_meeting(self) -> None:
        """May not create group C group_ids by OML permission with a locked meeting"""
        self.create_meeting(4)
        self.set_models({"meeting/4": {"locked_from_inside": True}})

        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 4,
                "group_ids": [4],
            },
            OrganizationManagementLevel.SUPERADMIN,
            custom_error_message="The user needs Permission user.can_manage for meeting 4",
        )

    def test_create_permission_group_C_committee_manager(self) -> None:
        """May create group C group_ids by committee permission"""
        self.base_permission_test(
            {"committee/60": {"manager_ids": [2]}},
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 1,
                "group_ids": [1],
            },
            fail=False,
        )
        self.assert_model_exists(
            "user/3",
            {
                "username": "usersname",
                "meeting_user_ids": [2],
                "meeting_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "group_ids": [1],
                "meeting_id": 1,
            },
        )

    def test_create_permission_group_C_user_can_manage(self) -> None:
        """May create group C group_ids by user.can_manage permission"""
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 1,
                "group_ids": [2],
            },
            user_groups=[2],  # Admin group of meeting/1
            fail=False,
        )

        self.assert_model_exists(
            "user/3",
            {
                "username": "usersname",
                "meeting_user_ids": [2],
                "meeting_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "group_ids": [2],
                "meeting_id": 1,
            },
        )

    def test_create_permission_group_C_no_permission(self) -> None:
        """May not create group C group_ids"""
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 1,
                "group_ids": [1],
            },
            custom_error_message="The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_manage for meeting 1",
        )

    def test_create_permission_group_C_cml_locked_meeting(self) -> None:
        """May not create group C group_ids in locked meetings as a committee manager"""
        self.permission_setup()
        self.create_meeting(4)
        self.set_committee_management_level([63], self.user_id)
        self.set_models({"meeting/4": {"locked_from_inside": True}})

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 4,
                "group_ids": [4],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs Permission user.can_manage for meeting 4",
            response.json["message"],
        )

    def test_create_permission_group_C_parent_cml_locked_meeting(self) -> None:
        """May not create group C group_ids in locked meetings as a committee manager of a parent committee"""
        self.permission_setup()
        self.create_meeting(4)
        self.create_committee()
        self.create_committee(63, parent_id=1)
        self.set_committee_management_level([1], self.user_id)
        self.set_models({"meeting/4": {"locked_from_inside": True}})

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 4,
                "group_ids": [4],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs Permission user.can_manage for meeting 4",
            response.json["message"],
        )

    def test_create_permission_group_D_permission_with_OML(self) -> None:
        """May create Group D committee fields with OML level permission for more than one committee"""
        self.create_meeting(base=4)

        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "usersname",
                "committee_management_ids": [60, 63],
                "organization_management_level": None,
            },
            OrganizationManagementLevel.CAN_MANAGE_USERS,
        )
        self.assert_model_exists(
            "user/3",
            {
                "committee_ids": [60, 63],
                "organization_management_level": None,
                "committee_management_ids": [60, 63],
                "username": "usersname",
            },
        )

    def test_create_permission_group_D_permission_with_CML(self) -> None:
        """
        May create Group D committee fields with CML permission for one committee only.
        Note: For 2 committees he can't set the username, which is required, but within 2 committees
        it would be organizational scope with organizational rights required.
        To do this he could create a user with 1 committee and later he could update the
        same user with second committee, if he has the permission for the committees.
        """
        self.base_permission_test(
            {"committee/60": {"manager_ids": [2]}},
            "user.create",
            {
                "username": "usersname",
                "committee_management_ids": [60],
            },
            fail=False,
        )
        self.assert_model_exists(
            "user/3",
            {
                "committee_ids": [60],
                "committee_management_ids": [60],
                "username": "usersname",
            },
        )

    def test_create_permission_group_D_no_permission(self) -> None:
        """May not create Group D committee fields, because of missing CML permission for one committee"""
        self.create_meeting(base=4)
        self.base_permission_test(
            {"committee/60": {"manager_ids": [2]}},
            "user.create",
            {
                "username": "usersname",
                "committee_management_ids": [60, 63],
            },
            custom_error_message="You are not allowed to perform action user.create. Missing permission: CommitteeManagementLevel can_manage in committee 63",
        )

    def test_create_permission_group_E_OML_high_enough(self) -> None:
        """OML level to set is sufficient"""
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "usersname",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
            OrganizationManagementLevel.CAN_MANAGE_USERS,
        )
        self.assert_model_exists(
            "user/3",
            {
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                "username": "usersname",
            },
        )

    def test_create_permission_group_E_OML_not_high_enough(self) -> None:
        """OML level to set is higher than level of request user"""
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "usersname",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            },
            OrganizationManagementLevel.CAN_MANAGE_USERS,
            custom_error_message="Your organization management level is not high enough to set a Level of can_manage_organization.",
        )

    def test_create_permission_group_H_internal_saml_id(self) -> None:
        self.create_meeting()
        self.set_organization_management_level(None)
        self.set_user_groups(1, [2])  # Admin-group

        response = self.request(
            "user.create",
            {
                "username": "username",
                "saml_id": "11111",
                "meeting_id": 1,
                "group_ids": [2],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The field 'saml_id' can only be used in internal action calls",
            response.json["message"],
        )

    def test_create_permission_group_H_oml_can_manage_user_saml_id(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )

        response = self.request(
            "user.create",
            {
                "saml_id": "11111",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "11111",
                "saml_id": "11111",
                "can_change_own_password": False,
                "default_password": None,
            },
        )

    def test_create_permission_group_F_demo_user_permission(self) -> None:
        """demo_user only editable by Superadmin"""
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "username3",
                "is_demo_user": True,
            },
            OrganizationManagementLevel.SUPERADMIN,
        )
        self.assert_model_exists(
            "user/3",
            {
                "username": "username3",
                "is_demo_user": True,
            },
        )

    def test_create_permission_group_F_demo_user_no_permission(self) -> None:
        """demo_user only editable by Superadmin"""
        self.base_permission_test(
            {},
            "user.create",
            {
                "username": "username3",
                "is_demo_user": True,
            },
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            custom_error_message="You are not allowed to perform action user.create. Missing OrganizationManagementLevel: superadmin",
        )

    def test_create_participant_as_orga_admin(self) -> None:
        self.base_permission_test(
            {},
            "user.create",
            {
                "first_name": "",
                "last_name": "",
                "is_active": True,
                "is_physical_person": True,
                "email": "",
                "username": "username3",
                "meeting_id": 1,
                "group_ids": [3],
                "vote_delegations_from_ids": [],
            },
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            user_groups=[],
        )

        user = self.assert_model_exists("user/3", {"username": "username3"})
        assert len(meeting_user_ids := user.get("meeting_user_ids", [])) == 1
        self.assert_model_exists(
            f"meeting_user/{meeting_user_ids[0]}", {"meeting_id": 1, "group_ids": [3]}
        )

    def test_create_forbidden_username(self) -> None:
        response = self.request(
            "user.create",
            {
                "username": "   ",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
        self.assert_status_code(response, 400)
        assert "Need username or first_name or last_name" in response.json["message"]

    def test_create_username_with_spaces(self) -> None:
        response = self.request(
            "user.create",
            {
                "username": "test name",
            },
        )
        self.assert_status_code(response, 400)
        assert "Username may not contain spaces" in response.json["message"]

    def test_create_gender(self) -> None:
        self.set_models({"organization/1": {"gender_ids": [1, 2]}})
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "gender_id": 5,
            },
        )
        self.assert_status_code(response, 400)
        assert "Model 'gender/5' does not exist." in response.json["message"]

    def test_exceed_limit_of_users(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"limit_of_users": 3},
                "user/2": {"username": "timtari", "is_active": True},
                "user/3": {"username": "timtari", "is_active": True},
            }
        )
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "is_active": True,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "The number of active users cannot exceed the limit of users."
            == response.json["message"]
        )

    def test_create_inactive_user(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"limit_of_users": 1},
            }
        )
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "is_active": False,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "test_Xcdfgee",
                "is_active": False,
            },
        )

    def test_create_negative_default_vote_weight(self) -> None:
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "default_vote_weight": "-1.500000",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "default_vote_weight must be bigger than or equal to 0.",
            response.json["message"],
        )

    def test_create_default_vote_weight_none(self) -> None:
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "default_vote_weight": None,
            },
        )
        self.assert_status_code(response, 200)
        user = self.get_model("user/2")
        assert "default_vote_weight" not in user

    def test_create_negative_vote_weight(self) -> None:
        self.create_meeting()
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "meeting_id": 1,
                "vote_weight": "-1.000000",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "vote_weight must be bigger than or equal to 0.",
            response.json["message"],
        )

    def test_create_variant(self) -> None:
        """
        The replacement on both sides user and committee is the committee_management_level,
        the ids are the user_ids and on user-side the committee_ids.
        """
        self.create_meeting()
        self.create_meeting(4)
        self.set_models(
            {
                "committee/60": {
                    "manager_ids": [222],
                },
                "committee/63": {
                    "manager_ids": [222],
                },
                "user/222": {
                    "username": "timtari",
                },
                "group/22": {"name": "deminish cap", "meeting_id": 4},
            }
        )
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "committee_management_ids": [60],
                "meeting_id": 4,
                "group_ids": [22],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/223",
            {
                "committee_management_ids": [60],
                "meeting_ids": [4],
                "committee_ids": [60, 63],
                "meeting_user_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": 4,
                "user_id": 223,
                "group_ids": [22],
            },
        )

        self.assert_model_exists(
            "committee/60", {"user_ids": [222, 223], "manager_ids": [222, 223]}
        )
        self.assert_model_exists(
            "committee/63", {"user_ids": [222, 223], "manager_ids": [222]}
        )
        self.assert_model_exists("group/22", {"meeting_user_ids": [1]})
        self.assert_model_exists("meeting/1", {"user_ids": None})
        self.assert_model_exists(
            "meeting/4", {"user_ids": [223], "meeting_user_ids": [1]}
        )

    def assert_lock_out_user(
        self,
        meeting_id: int,
        other_payload_data: dict[str, Any],
        errormsg: str | None = None,
    ) -> None:
        self.create_meeting()  # committee:60; groups: default:1, admin:2, can_manage:3
        self.create_meeting(4)  # committee:63; groups: default:4, admin:5, can_update:6
        self.add_group_permissions(3, [Permissions.User.CAN_MANAGE])
        self.add_group_permissions(6, [Permissions.User.CAN_UPDATE])
        response = self.request(
            "user.create",
            {
                "username": "test",
                "meeting_id": meeting_id,
                "locked_out": True,
                "group_ids": [1],
                **other_payload_data,
            },
        )
        if errormsg is not None:
            self.assert_status_code(response, 400)
            self.assertIn(
                errormsg,
                response.json["message"],
            )
        else:
            self.assert_status_code(response, 200)

    def test_create_locked_out_user_foreign_cml_allowed(self) -> None:
        self.assert_lock_out_user(1, {"committee_management_ids": [63]})

    def test_create_locked_out_user_child_cml_allowed(self) -> None:
        self.create_committee(60)
        self.create_committee(63, parent_id=60)
        self.assert_lock_out_user(1, {"committee_management_ids": [63]})

    def test_create_locked_out_user_home_committee_allowed(self) -> None:
        self.assert_lock_out_user(1, {"home_committee_id": 60})

    def test_create_locked_out_user_child_home_committee_allowed(self) -> None:
        self.create_committee(60)
        self.create_committee(63, parent_id=60)
        self.assert_lock_out_user(1, {"home_committee_id": 63})

    def test_create_locked_out_user_foreign_home_committee_allowed(self) -> None:
        self.assert_lock_out_user(1, {"home_committee_id": 63})

    def test_create_locked_out_user_superadmin_error(self) -> None:
        self.assert_lock_out_user(
            1,
            {"organization_management_level": "superadmin"},
            errormsg="Cannot lock user from meeting 1 as long as he has the OrganizationManagementLevel superadmin",
        )

    def test_create_locked_out_user_other_oml_error(self) -> None:
        self.assert_lock_out_user(
            1,
            {"organization_management_level": "can_manage_users"},
            errormsg="Cannot lock user from meeting 1 as long as he has the OrganizationManagementLevel can_manage_users",
        )

    def test_create_locked_out_user_cml_error(self) -> None:
        self.assert_lock_out_user(
            1,
            {"committee_management_ids": [60]},
            errormsg="Cannot lock user out of meeting 1 as he is manager of the meetings committee or one of its parents",
        )

    def test_create_locked_out_user_parent_cml_error(self) -> None:
        self.create_committee(59)
        self.create_committee(60, parent_id=59)
        self.assert_lock_out_user(
            1,
            {"committee_management_ids": [59]},
            errormsg="Cannot lock user out of meeting 1 as he is manager of the meetings committee or one of its parents",
        )

    def test_create_locked_out_user_meeting_admin_error(self) -> None:
        self.assert_lock_out_user(
            1,
            {"group_ids": [2]},
            errormsg="Group(s) 2 have user.can_manage permissions and may therefore not be used by users who are locked out",
        )

    def test_create_locked_out_user_can_manage_error(self) -> None:
        self.assert_lock_out_user(
            1,
            {"group_ids": [3]},
            errormsg="Group(s) 3 have user.can_manage permissions and may therefore not be used by users who are locked out",
        )

    def test_create_locked_out_user_can_update_allowed(self) -> None:
        self.assert_lock_out_user(
            4,
            {"group_ids": [6]},
        )

    def test_create_with_home_committee(self) -> None:
        self.create_committee(3)
        response = self.request(
            "user.create",
            {"username": "dracula", "home_committee_id": 3},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {"username": "dracula", "home_committee_id": 3, "committee_ids": [3]},
        )

    def test_create_with_all_committee_fields(self) -> None:
        self.create_committee(3)
        self.create_committee(4)
        self.create_committee(5)
        self.create_committee(6, parent_id=5)
        self.create_meeting()
        response = self.request(
            "user.create",
            {
                "username": "dracula",
                "home_committee_id": 3,
                "committee_management_ids": [4, 6],
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "dracula",
                "home_committee_id": 3,
                "committee_management_ids": [4, 6],
                "meeting_user_ids": [1],
                "committee_ids": [3, 4, 6, 60],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "user_id": 2,
                "meeting_id": 1,
                "group_ids": [1],
            },
        )

    def test_create_with_home_committee_cml(self) -> None:
        self.create_committee(3)
        self.set_committee_management_level([3])
        self.set_organization_management_level(None)
        response = self.request(
            "user.create",
            {"username": "mina", "home_committee_id": 3},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2", {"username": "mina", "home_committee_id": 3, "committee_ids": [3]}
        )

    def test_create_with_external_true(self) -> None:
        response = self.request(
            "user.create",
            {"username": "jonathan", "external": True},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "jonathan", "external": True})

    def test_create_with_external_false(self) -> None:
        response = self.request(
            "user.create",
            {"username": "jack", "external": False},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "jack", "external": False})

    def test_create_with_with_home_committee_and_external_true(self) -> None:
        self.create_committee(3)
        response = self.request(
            "user.create",
            {"username": "renfield", "home_committee_id": 3, "external": True},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot set external to true and set a home committee at the same time.",
            response.json["message"],
        )

    def test_create_with_home_committee_and_external_false(self) -> None:
        """Also tests for parent CML"""
        self.create_committee(2)
        self.create_committee(3, parent_id=2)
        self.set_committee_management_level([2])
        self.set_organization_management_level(None)
        response = self.request(
            "user.create",
            {"username": "vanHelsing", "home_committee_id": 3, "external": False},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "vanHelsing",
                "home_committee_id": 3,
                "external": False,
                "committee_ids": [3],
            },
        )

    def test_create_with_home_committee_wrong_CML(self) -> None:
        self.create_committee(2)
        self.create_committee(3)
        self.set_committee_management_level([2])
        self.set_organization_management_level(None)
        response = self.request(
            "user.create",
            {
                "username": "quincy",
                "home_committee_id": 3,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.create. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 3",
            response.json["message"],
        )

    def test_create_with_home_committee_no_perm(self) -> None:
        self.create_committee(3)
        self.set_organization_management_level(None)
        response = self.request(
            "user.create",
            {
                "username": "arthur",
                "home_committee_id": 3,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.create. Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or CommitteeManagementLevel can_manage in committee 3",
            response.json["message"],
        )


class UserCreateActionTestInternal(BaseInternalActionTest):
    def test_create_empty_saml_id_and_empty_values(self) -> None:
        response = self.internal_request(
            "user.create",
            {"saml_id": "  ", "username": "x"},
        )
        self.assert_status_code(response, 400)
        self.assertIn("This saml_id is forbidden.", response.json["message"])

    def test_create_saml_id_and_default_pasword(self) -> None:
        response = self.internal_request(
            "user.create",
            {
                "username": "username_test",
                "saml_id": "123saml",
                "default_password": "test",
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "user 123saml is a Single Sign On user and may not set the local default_passwort or the right to change it locally."
            in response.json["message"]
        )

    def test_create_saml_id_and_empty_values(self) -> None:
        response = self.internal_request(
            "user.create",
            {
                "saml_id": "123saml",
                "default_password": "",
                "can_change_own_password": False,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "123saml",
                "saml_id": "123saml",
                "default_password": "",
                "can_change_own_password": False,
                "password": None,
                "is_physical_person": True,
                "is_active": True,
            },
        )

    def test_create_saml_id_but_duplicate_error1(self) -> None:
        self.set_models({"user/2": {"username": "x", "saml_id": "123saml"}})
        response = self.internal_request(
            "user.create",
            {
                "saml_id": "123saml",
                "default_password": "",
                "can_change_own_password": False,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A user with the saml_id 123saml already exists.", response.json["message"]
        )

    def test_create_saml_id_but_duplicate_error2(self) -> None:
        self.set_models({"user/2": {"username": "123saml"}})
        response = self.internal_request(
            "user.create",
            {
                "saml_id": "123saml",
                "default_password": "",
                "can_change_own_password": False,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "A user with the username 123saml already exists.", response.json["message"]
        )

    def test_create_anonymous_group_id(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"group_ids": [1, 2, 3, 4], "anonymous_group_id": 4},
                "group/4": {"name": "anonymous", "meeting_id": 1},
            }
        )
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "meeting_id": 1,
                "group_ids": [4],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot add explicit users to a meetings anonymous group",
            response.json["message"],
        )

    def test_create_permission_as_locked_out(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        meeting_user_id = self.set_user_groups(self.user_id, [3])[0]
        self.set_models({f"meeting_user/{meeting_user_id}": {"locked_out": True}})
        self.set_group_permissions(3, [Permissions.User.CAN_MANAGE])
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "meeting_id": 1,
                "group_ids": [1],
                "number": "123456",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_manage for meeting 1",
            response.json["message"],
        )
