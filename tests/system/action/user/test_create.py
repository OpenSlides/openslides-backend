from openslides_backend.action.util.crypto import PASSWORD_CHARS
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
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
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_DsJFXoot",
                    "committee_id": 78,
                    "is_active_in_organization_id": 1,
                },
                "meeting/111": {
                    "name": "name_xXRGTLAJ",
                    "committee_id": 79,
                    "group_ids": [111],
                    "is_active_in_organization_id": 1,
                },
                "group/111": {"meeting_id": 111},
                "committee/78": {"name": "name_TSXpBGdt", "meeting_ids": [110]},
                "committee/79": {"name": "name_hOldWvVF", "meeting_ids": [111]},
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
                "meeting_id": 111,
                "group_ids": [111],
            },
        )
        self.assert_status_code(response, 200)
        user2 = self.assert_model_exists(
            "user/2",
            {
                "pronoun": "Test",
                "username": "test_Xcdfgee",
                "default_vote_weight": "1.500000",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                "default_password": "password",
                "committee_management_ids": [78],
                "meeting_user_ids": [1],
            },
        )
        self.assertCountEqual(user2.get("committee_ids", []), [78, 79])
        assert self.auth.is_equal(
            user2.get("default_password", ""), user2.get("password", "")
        )
        result = response.json["results"][0][0]
        assert result == {"id": 2, "meeting_user_id": 1}
        self.assert_model_exists(
            "meeting_user/1", {"meeting_id": 111, "user_id": 2, "group_ids": [111]}
        )
        self.assert_model_exists(
            "committee/78", {"meeting_ids": [110], "user_ids": [2]}
        )
        self.assert_model_exists(
            "committee/79", {"meeting_ids": [111], "user_ids": [2]}
        )
        self.assert_history_information(
            "user/2",
            ["Account created", "Participant added to meeting {}", "meeting/111"],
        )

    def test_create_comment(self) -> None:
        self.set_models(
            {"meeting/1": {"name": "test meeting 1", "is_active_in_organization_id": 1}}
        )
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "comment": "blablabla",
                "meeting_id": 1,
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
        self.set_models(
            {
                "meeting/11": {
                    "name": "meeting11",
                    "committee_id": 79,
                    "group_ids": [111],
                    "is_active_in_organization_id": 1,
                },
                "group/111": {"meeting_id": 11},
            }
        )

        response = self.request(
            "user.create",
            {"username": "test_Xcdfgee", "group_ids": [111]},
        )
        self.assert_status_code(response, 400)
        assert (
            "Missing meeting_id in instance, because meeting related fields used"
            in response.json["message"]
        )

    def test_create_with_meeting_user_fields(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "C1", "meeting_ids": [1]},
                "committee/2": {"name": "C2"},
                "meeting/1": {
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                    "structure_level_ids": [31],
                },
                "user/222": {"meeting_ids": [1], "meeting_user_ids": [1]},
                "meeting_user/1": {"meeting_id": 1, "user_id": 222},
                "group/11": {"meeting_id": 1},
                "structure_level/31": {"meeting_id": 1},
            }
        )
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "meeting_id": 1,
                "group_ids": [11],
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
                "committee_ids": [1, 2],
                "meeting_user_ids": [2],
                "meeting_ids": [1],
            },
        )
        result = response.json["results"][0][0]
        assert result == {"id": 223, "meeting_user_id": 2}
        self.assert_model_exists(
            "meeting_user/2",
            {
                "group_ids": [11],
                "vote_delegations_from_ids": [1],
                "comment": "comment&lt;iframe&gt;&lt;/iframe&gt;",
                "number": "number1",
                "structure_level_ids": [31],
                "about_me": "<p>about</p>&lt;iframe&gt;&lt;/iframe&gt;",
                "vote_weight": "1.000000",
            },
        )
        self.assert_model_exists("user/222", {"meeting_user_ids": [1]})
        self.assert_model_exists("meeting_user/1", {"vote_delegated_to_id": 2})
        self.assert_model_exists("group/11", {"meeting_user_ids": [2]})
        self.assert_model_exists("meeting/1", {"user_ids": [223]})

    def test_invalid_committee_management_ids(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "C1", "meeting_ids": [1]},
                "meeting/1": {"committee_id": 1},
                "user/222": {"meeting_ids": [1]},
            }
        )
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
        self.create_model("meeting/1")
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
        self.set_models(
            {
                "committee/1": {"meeting_ids": [1, 2]},
                "meeting/1": {"committee_id": 1},
                "meeting/2": {
                    "is_active_in_organization_id": ONE_ORGANIZATION_ID,
                    "committee_id": 1,
                },
                "group/11": {"meeting_id": 1},
            }
        )
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "meeting_id": 2,
                "group_ids": [11],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 2: ['group/11']",
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

    def test_user_create_with_empty_vote_delegation_from_ids(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
            }
        )
        response = self.request(
            "user.create",
            {
                "username": "testname",
                "meeting_id": 1,
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
            {"meeting_id": 1, "user_id": 2, "vote_delegations_from_ids": []},
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
        user = self.get_model("user/2")
        self.assertCountEqual((60, 63), user["committee_ids"])
        self.assertCountEqual((60, 63), user["committee_management_ids"])
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
        self.permission_setup()
        response = self.request(
            "user.create",
            {
                "username": "username",
                "meeting_id": 1,
                "vote_weight": "1.000000",
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_manage for meeting 1",
            response.json["message"],
        )

    def test_create_permission_auth_error(self) -> None:
        self.permission_setup()
        response = self.request(
            "user.create",
            {
                "username": "username_Neu",
                "meeting_id": 1,
                "vote_weight": "1.000000",
                "group_ids": [1],
            },
            anonymous=True,
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Anonymous is not allowed to execute user.create",
            response.json["message"],
        )

    def test_create_permission_superadmin(self) -> None:
        """
        SUPERADMIN may set fields of all groups and may set an other user as SUPERADMIN, too.
        The SUPERADMIN don't need to belong to a meeting in any way to change data!
        """
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )

        response = self.request(
            "user.create",
            {
                "username": "username_new",
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "meeting_id": 1,
                "vote_weight": "1.000000",
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
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
                "vote_weight": "1.000000",
                "group_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/2",
            {
                "user_id": 3,
                "meeting_id": 1,
                "vote_weight": "1.000000",
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
            {"organization/1": {"genders": ["male", "female", "diverse", "non-binary"]}}
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
                            "gender": "female",
                            "email": "info@openslides.com",
                            "default_number": "new default_number",
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
                "gender": "female",
                "email": "info@openslides.com",
                "default_number": "new default_number",
                "default_vote_weight": "1.234000",
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
                f"user/{self.user_id}": {
                    "committee_management_ids": [60],
                    "committee_ids": [60],
                },
                "meeting/4": {"committee_id": 60, "is_active_in_organization_id": 1},
                "committee/60": {"meeting_ids": [1, 4]},
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
        self.permission_setup()
        self.set_user_groups(self.user_id, [2])
        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
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

    def test_create_permission_group_A_no_permission(self) -> None:
        """May not create group A fields on organsisation scope, although having both committee permissions"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.update_model(
            f"user/{self.user_id}",
            {
                "committee_management_ids": [60, 63],
                "committee_ids": [60, 63],
            },
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
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.create. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
            response.json["message"],
        )

    def test_create_permission_group_B_user_can_manage(self) -> None:
        """create group B fields with simple user.can_manage permissions"""
        self.permission_setup()
        self.set_organization_management_level(None, self.user_id)
        self.set_user_groups(self.user_id, [2])  # Admin groups of meeting/1

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
                "vote_weight": "12.002345",
                "about_me": "about me 1",
                "comment": "comment for meeting/1",
                "vote_delegations_from_ids": [2, 3],
                "group_ids": [1],
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
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )
        self.set_user_groups(self.user_id, [3])  # Empty group of meeting/1

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 1,
                "group_ids": [1],
                "is_present_in_meeting_ids": [1],
                "number": "number1",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.create. Missing permission: Permission user.can_manage in meeting 1",
            response.json["message"],
        )

    def test_create_permission_group_C_oml_manager(self) -> None:
        """May create group C group_ids by OML permission"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/3", {"meeting_user_ids": [2]})
        self.assert_model_exists("meeting_user/2", {"group_ids": [1]})

    def test_create_permission_group_C_committee_manager(self) -> None:
        """May create group C group_ids by committee permission"""
        self.permission_setup()
        self.set_committee_management_level([60], self.user_id)

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
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
        self.permission_setup()
        self.set_user_groups(self.user_id, [2])  # Admin-group

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 1,
                "group_ids": [2],
            },
        )

        self.assert_status_code(response, 200)
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
        self.permission_setup()

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "meeting_id": 1,
                "group_ids": [1],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committee of following meeting or Permission user.can_manage for meeting 1",
            response.json["message"],
        )

    def test_create_permission_group_D_permission_with_OML(self) -> None:
        """May create Group D committee fields with OML level permission for more than one committee"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "committee_management_ids": [60, 63],
                "organization_management_level": None,
            },
        )
        self.assert_status_code(response, 200)
        user3 = self.assert_model_exists(
            "user/3",
            {
                "committee_ids": [60, 63],
                "organization_management_level": None,
                "committee_management_ids": [60, 63],
                "username": "usersname",
            },
        )
        self.assertCountEqual(user3.get("committee_management_ids", []), [60, 63])

    def test_create_permission_group_D_permission_with_CML(self) -> None:
        """
        May create Group D committee fields with CML permission for one committee only.
        Note: For 2 committees he can't set the username, which is required, but within 2 committees
        it would be organizational scope with organizational rights required.
        To do this he could create a user with 1 committee and later he could update the
        same user with second committee, if he has the permission for the committees.
        """
        self.permission_setup()
        self.set_committee_management_level([60], self.user_id)

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "committee_management_ids": [60],
            },
        )
        self.assert_status_code(response, 200)
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
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60], self.user_id)

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "committee_management_ids": [60, 63],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.create. Missing permission: CommitteeManagementLevel can_manage in committee 63",
            response.json["message"],
        )

    def test_create_permission_group_E_OML_high_enough(self) -> None:
        """OML level to set is sufficient"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/3",
            {
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                "username": "usersname",
            },
        )

    def test_create_permission_group_E_OML_not_high_enough(self) -> None:
        """OML level to set is higher than level of request user"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.create",
            {
                "username": "usersname",
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Your organization management level is not high enough to set a Level of can_manage_organization.",
            response.json["message"],
        )

    def test_create_permission_group_H_internal_saml_id(self) -> None:
        self.permission_setup()
        self.set_user_groups(self.user_id, [2])  # Admin-group

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
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, self.user_id
        )

        response = self.request(
            "user.create",
            {
                "username": "username3",
                "is_demo_user": True,
            },
        )

        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/3",
            {
                "username": "username3",
                "is_demo_user": True,
            },
        )

    def test_create_permission_group_F_demo_user_no_permission(self) -> None:
        """demo_user only editable by Superadmin"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, self.user_id
        )
        response = self.request(
            "user.create",
            {
                "username": "username3",
                "is_demo_user": True,
            },
        )

        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.create. Missing OrganizationManagementLevel: superadmin",
            response.json["message"],
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
        self.set_models({"organization/1": {"genders": ["male", "female"]}})
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "gender": "test",
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Gender 'test' is not in the allowed gender list."
            in response.json["message"]
        )

    def test_exceed_limit_of_users(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"limit_of_users": 3},
                "user/2": {"is_active": True},
                "user/3": {"is_active": True},
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

    def test_create_forwarding_committee_ids_not_allowed(self) -> None:
        self.set_models({"meeting/1": {"is_active_in_organization_id": 1}})
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "forwarding_committee_ids": [],
            },
        )
        self.assert_status_code(response, 403)
        assert "forwarding_committee_ids is not allowed." in response.json["message"]

    def test_create_negative_vote_weight(self) -> None:
        self.set_models(
            {
                "meeting/1": {"is_active_in_organization_id": 1},
                "meeting/2": {"is_active_in_organization_id": 1},
            }
        )
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
        The replacement on both sides user and committe is the committee_management_level,
        the ids are the user_ids and on user-side the committee_ids.
        """
        self.set_models(
            {
                "committee/1": {
                    "name": "C1",
                    "meeting_ids": [1],
                    "user_ids": [222],
                    "manager_ids": [222],
                },
                "committee/2": {
                    "name": "C2",
                    "meeting_ids": [2],
                    "user_ids": [222],
                    "manager_ids": [222],
                },
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "meeting/2": {"committee_id": 2, "is_active_in_organization_id": 1},
                "user/222": {
                    "committee_management_ids": [1, 2],
                },
                "group/22": {"meeting_id": 2},
            }
        )
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "committee_management_ids": [1],
                "meeting_id": 2,
                "group_ids": [22],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/223",
            {
                "committee_management_ids": [1],
                "meeting_ids": [2],
                "committee_ids": [1, 2],
                "meeting_user_ids": [1],
            },
        )
        self.assert_model_exists(
            "meeting_user/1",
            {
                "meeting_id": 2,
                "user_id": 223,
                "group_ids": [22],
            },
        )

        self.assert_model_exists(
            "committee/1", {"user_ids": [222, 223], "manager_ids": [222, 223]}
        )
        self.assert_model_exists(
            "committee/2", {"user_ids": [222, 223], "manager_ids": [222]}
        )
        self.assert_model_exists("group/22", {"meeting_user_ids": [1]})
        self.assert_model_exists("meeting/1", {"user_ids": None})
        self.assert_model_exists(
            "meeting/2", {"user_ids": [223], "meeting_user_ids": [1]}
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
                "is_active": None,  # optional field and not set
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
