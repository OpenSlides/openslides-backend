from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class UserUpdateActionTest(BaseActionTestCase):
    def permission_setup(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("test", group_ids=[1])
        self.login(self.user_id)
        self.set_models(
            {
                "user/111": {"username": "User 111"},
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
                "organization_management_level": "can_manage_users",
                "committee_$_management_level": {
                    CommitteeManagementLevel.CAN_MANAGE: [78],
                },
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
                "committee_$_management_level": ["can_manage"],
                "committee_$can_manage_management_level": [78],
                "organization_management_level": "can_manage_users",
            },
        )

    def test_update_template_fields(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "C1", "meeting_ids": [1]},
                "committee/2": {"name": "C2", "meeting_ids": [2]},
                "meeting/1": {"committee_id": 1, "is_active_in_organization_id": 1},
                "meeting/2": {"committee_id": 2, "is_active_in_organization_id": 1},
                "user/222": {"meeting_ids": [1]},
                "user/223": {
                    "committee_ids": [1],
                    "committee_$can_manage_management_level": [1],
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                },
                "group/11": {"meeting_id": 1},
                "group/22": {"meeting_id": 2},
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 223,
                "group_$_ids": {1: [11], 2: [22]},
                "vote_delegations_$_from_ids": {1: [222]},
                "comment_$": {1: "comment<iframe></iframe>"},
                "number_$": {2: "number"},
                "structure_level_$": {1: "level_1", 2: "level_2"},
                "about_me_$": {1: "<p>about</p><iframe></iframe>"},
                "vote_weight_$": {1: "1.000000", 2: "2.333333"},
                "committee_$_management_level": {
                    CommitteeManagementLevel.CAN_MANAGE: [2],
                },
            },
        )
        self.assert_status_code(response, 200)
        user = self.assert_model_exists(
            "user/223",
            {
                "committee_$can_manage_management_level": [2],
                "committee_$_management_level": [CommitteeManagementLevel.CAN_MANAGE],
                "group_$1_ids": [11],
                "group_$2_ids": [22],
                "vote_delegations_$1_from_ids": [222],
                "vote_delegations_$_from_ids": ["1"],
                "comment_$1": "comment&lt;iframe&gt;&lt;/iframe&gt;",
                "comment_$": ["1"],
                "number_$2": "number",
                "number_$": ["2"],
                "structure_level_$1": "level_1",
                "structure_level_$2": "level_2",
                "about_me_$1": "<p>about</p>&lt;iframe&gt;&lt;/iframe&gt;",
                "about_me_$": ["1"],
                "vote_weight_$1": "1.000000",
                "vote_weight_$2": "2.333333",
            },
        )
        self.assertCountEqual(user.get("committee_ids", []), [1, 2])
        self.assertCountEqual(user.get("group_$_ids", []), ["1", "2"])
        self.assertCountEqual(user.get("structure_level_$", []), ["1", "2"])
        self.assertCountEqual(user.get("vote_weight_$", []), ["1", "2"])
        self.assertCountEqual(user.get("meeting_ids", []), [1, 2])

        user = self.assert_model_exists(
            "user/222",
            {
                "vote_delegated_$1_to_id": 223,
                "vote_delegated_$_to_id": ["1"],
            },
        )
        group1 = self.get_model("group/11")
        self.assertCountEqual(group1.get("user_ids"), [223])
        group2 = self.get_model("group/22")
        self.assertCountEqual(group2.get("user_ids"), [223])
        meeting = self.get_model("meeting/1")
        self.assertCountEqual(meeting.get("user_ids"), [223])
        meeting = self.get_model("meeting/2")
        self.assertCountEqual(meeting.get("user_ids"), [223])

    def test_committee_manager_without_committee_ids(self) -> None:
        """Giving committee management level requires committee_ids"""
        self.set_models(
            {
                "user/111": {
                    "username": "username_srtgb123",
                    "group_$_ids": ["600"],
                    "group_$600_ids": [600],
                    "meeting_ids": [600],
                },
                "committee/60": {
                    "name": "c60",
                    "meeting_ids": [600],
                    "user_ids": [111],
                },
                "committee/61": {"name": "c61"},
                "meeting/600": {
                    "user_ids": [111],
                    "group_ids": [600],
                    "committee_id": 60,
                    "is_active_in_organization_id": 1,
                },
                "group/600": {"user_ids": [111], "meeting_id": 600},
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "usersname",
                "committee_$_management_level": {
                    CommitteeManagementLevel.CAN_MANAGE: [60, 61],
                },
                "group_$_ids": {"600": []},
            },
        )
        self.assert_status_code(response, 200)
        user = self.assert_model_exists(
            "user/111",
            {
                "committee_$_management_level": [CommitteeManagementLevel.CAN_MANAGE],
            },
        )
        self.assertCountEqual(user["committee_ids"], [60, 61])
        self.assertCountEqual(user["committee_$can_manage_management_level"], [60, 61])

    def test_committee_manager_remove_committee_ids(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "C1", "user_ids": [111]},
                "user/111": {
                    "committee_ids": [1],
                    "committee_$can_manage_management_level": [1],
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_$_management_level": {"can_manage": []},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111", {"committee_$_management_level": [], "committee_ids": []}
        )
        self.assert_model_exists("committee/1", {"user_ids": []})

    def test_committee_manager_add_and_remove_both(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "name": "remove user",
                    "user_ids": [111],
                    "meeting_ids": [11],
                },
                "committee/2": {
                    "name": "remove cml from_user",
                    "user_ids": [111],
                    "meeting_ids": [22],
                },
                "committee/3": {"name": "add user", "meeting_ids": [33]},
                "committee/4": {"name": "add user with cml"},
                "meeting/11": {
                    "user_ids": [111],
                    "group_ids": [111],
                    "committee_id": 1,
                    "is_active_in_organization_id": 1,
                },
                "meeting/22": {
                    "user_ids": [111],
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
                "group/111": {"user_ids": [111], "meeting_id": 11},
                "group/222": {"user_ids": [111], "meeting_id": 22},
                "group/333": {"user_ids": [], "meeting_id": 33},
                "user/111": {
                    "meeting_ids": [11, 22],
                    "committee_ids": [1, 2],
                    "committee_$can_manage_management_level": [1, 2],
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                    "group_$_ids": ["11", "22"],
                    "group_$11_ids": [111],
                    "group_$22_ids": [222],
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_$_management_level": {
                    CommitteeManagementLevel.CAN_MANAGE: [4],
                },
                "group_$_ids": {"11": [], "33": [333]},
            },
        )
        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        self.assertCountEqual(user["committee_$can_manage_management_level"], [4])
        self.assertCountEqual(user["committee_ids"], [2, 3, 4])
        self.assertCountEqual(user["meeting_ids"], [22, 33])
        self.assert_model_exists("committee/1", {"user_ids": []})
        self.assert_model_exists("committee/2", {"user_ids": [111]})
        self.assert_model_exists("committee/3", {"user_ids": [111]})
        self.assert_model_exists("committee/4", {"user_ids": [111]})
        self.assert_model_exists("meeting/11", {"user_ids": []})
        self.assert_model_exists("meeting/22", {"user_ids": [111]})
        self.assert_model_exists("meeting/33", {"user_ids": [111]})

    def test_group_switch_change_meeting_ids(self) -> None:
        """Set a group and a meeting_ids to a user. Then change the group."""
        self.create_meeting()
        self.create_meeting(base=4)
        self.set_user_groups(222, [1])
        self.assert_model_exists("user/222", {"meeting_ids": [1]})
        response = self.request(
            "user.update",
            {
                "id": 222,
                "group_$_ids": {1: [], 4: [4]},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/222", {"meeting_ids": [4]})

    def test_remove_group_from_user(self) -> None:
        """May update group A fields on meeting scope. User belongs to 1 meeting without being part of a committee"""
        self.permission_setup()
        self.set_user_groups(self.user_id, [2])
        self.set_user_groups(111, [1])

        response = self.request(
            "user.update",
            {
                "id": 111,
                "group_$_ids": {"1": []},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "group_$_ids": [],
                "group_$1_ids": None,
            },
        )

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

    def test_same_username(self) -> None:
        response = self.request("user.update", {"id": 1, "username": "admin"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"username": "admin"})

    def test_perm_nothing(self) -> None:
        self.permission_setup()
        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "username_Neu",
                "vote_weight_$": {1: "1.000000"},
                "group_$_ids": {1: [1]},
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committees of following meetings or Permission user.can_manage for meetings {1}",
            response.json["message"],
        )

    def test_perm_auth_error(self) -> None:
        self.permission_setup()
        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "username_Neu",
                "vote_weight_$": {1: "1.000000"},
                "group_$_ids": {1: [1]},
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
            {"user/111": {"username": "User 111"}},
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "username_new",
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "vote_weight_$": {1: "1.000000"},
                "group_$_ids": {1: [1]},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "username_new",
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "vote_weight_$": ["1"],
                "vote_weight_$1": "1.000000",
                "group_$_ids": ["1"],
                "group_$1_ids": [1],
            },
        )

    def test_perm_group_A_oml_manage_user(self) -> None:
        """May update group A fields on organsisation scope, because belongs to 2 meetings in 2 committees, requiring OML level permission"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )
        self.set_user_groups(111, [1, 6])

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new username",
                "title": "new title",
                "first_name": "new first_name",
                "last_name": "new last_name",
                "is_active": True,
                "is_physical_person": True,
                "default_password": "new default_password",
                "gender": "female",
                "email": "info@openslides.com ",
                "default_number": "new default_number",
                "default_structure_level": "new default_structure_level",
                "default_vote_weight": "1.234000",
                "can_change_own_password": False,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "new username",
                "title": "new title",
                "first_name": "new first_name",
                "last_name": "new last_name",
                "is_active": True,
                "is_physical_person": True,
                "default_password": "new default_password",
                "gender": "female",
                "email": "info@openslides.com ",
                "default_number": "new default_number",
                "default_structure_level": "new default_structure_level",
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
                "username": "new username",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "new username",
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
                "username": "new username",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "new username",
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
                "username": "new username",
                "pronoun": "pronoun",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "new username",
                "pronoun": "pronoun",
                "meeting_ids": [1],
                "committee_ids": None,
            },
        )

    def test_perm_group_A_meeting_manage_user_archived_meeting(self) -> None:
        """
        May update group A fields on meeting scope. User belongs to 1 meeting without being part of a committee
        User is member of an archived meeting in an other committee, but this doesn't may affect the result.
        """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_user_groups(self.user_id, [2])
        self.set_user_groups(111, [1, 4])
        self.set_models({"meeting/4": {"is_active_in_organization_id": None}})
        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new username",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "new username",
                "committee_ids": None,
            },
        )
        user111 = self.get_model("user/111")
        self.assertCountEqual(user111["meeting_ids"], [1, 4])

    def test_perm_group_A_no_permission(self) -> None:
        """May not update group A fields on organsisation scope, although having both committee permissions"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60, 63], self.user_id)
        self.set_user_groups(111, [1, 6])

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "new username",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: OrganizationManagementLevel can_manage_users in organization 1",
            response.json["message"],
        )

    def test_perm_group_B_user_can_manage(self) -> None:
        """update group B fields for 2 meetings with simple user.can_manage permissions"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_organization_management_level(None, self.user_id)
        self.set_user_groups(
            self.user_id, [2, 5]
        )  # Admin groups of meeting/1 and meeting/4
        self.set_user_groups(111, [1, 6])

        self.set_models(
            {
                "user/5": {"username": "user5", "meeting_ids": [4]},
                "user/6": {"username": "user6", "meeting_ids": [4]},
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "number_$": {"1": "number1", "4": "number1 in 4"},
                "structure_level_$": {"1": "structure_level 1"},
                "vote_weight_$": {"1": "12.002345"},
                "about_me_$": {"1": "about me 1"},
                "comment_$": {"1": "comment zu meeting/1"},
                "vote_delegated_$_to_id": {"1": self.user_id},
                "vote_delegations_$_from_ids": {"4": [5, 6]},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "username": "User 111",
                "number_$": ["1", "4"],
                "number_$1": "number1",
                "number_$4": "number1 in 4",
                "structure_level_$": ["1"],
                "structure_level_$1": "structure_level 1",
                "vote_weight_$": ["1"],
                "vote_weight_$1": "12.002345",
                "about_me_$": ["1"],
                "about_me_$1": "about me 1",
                "comment_$": ["1"],
                "comment_$1": "comment zu meeting/1",
                "vote_delegated_$_to_id": ["1"],
                "vote_delegated_$1_to_id": self.user_id,
                "vote_delegations_$_from_ids": ["4"],
                "vote_delegations_$4_from_ids": [5, 6],
            },
        )
        user = self.get_model("user/111")
        self.assertCountEqual(user["meeting_ids"], [1, 4])

    def test_perm_group_B_user_can_manage_no_permission(self) -> None:
        """Group B fields needs explicit user.can_manage permission for meeting"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_organization_management_level(None, self.user_id)
        self.set_user_groups(
            self.user_id, [3, 6]
        )  # Empty groups of meeting/1 and meeting/4
        self.set_user_groups(111, [1, 4])  # Default groups of meeting/1 and meeting/4
        self.set_group_permissions(3, [Permissions.User.CAN_MANAGE])

        response = self.request(
            "user.update",
            {
                "id": 111,
                "number_$": {"1": "number1", "4": "number1 in 4"},
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: Permission user.can_manage in meeting 4",
            response.json["message"],
        )

    def test_perm_group_C_oml_manager(self) -> None:
        """May update group C group_$_ids by OML permission"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "group_$_ids": {1: [1]},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {"group_$_ids": ["1"], "group_$1_ids": [1]},
        )

    def test_perm_group_C_committee_manager(self) -> None:
        """May update group C group_$_ids by committee permission"""
        self.permission_setup()
        self.set_committee_management_level([60], self.user_id)

        response = self.request(
            "user.update",
            {
                "id": 111,
                "group_$_ids": {1: [1]},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {"group_$_ids": ["1"], "group_$1_ids": [1]},
        )

    def test_perm_group_C_user_can_manage(self) -> None:
        """May update group C group_$_ids by user.can_manage permission with admin group of all related meetings"""
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
                "group_$_ids": {1: [2], 4: [5]},
            },
        )

        self.assert_status_code(response, 200)
        user = self.get_model("user/111")
        self.assertCountEqual(user["group_$_ids"], ["1", "4"])
        self.assertCountEqual(user["meeting_ids"], [1, 4])
        self.assertEqual(user["group_$1_ids"], [2])
        self.assertEqual(user["group_$4_ids"], [5])

    def test_perm_group_C_no_permission(self) -> None:
        """May not update group C group_$_ids"""
        self.permission_setup()

        response = self.request(
            "user.update",
            {
                "id": 111,
                "group_$_ids": {1: [1]},
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committees of following meetings or Permission user.can_manage for meetings {1}",
            response.json["message"],
        )

    def test_perm_group_C_special_1(self) -> None:
        """group C group_$_ids adding meeting in same committee with committee permission"""
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60], self.user_id)
        self.set_models(
            {
                "committee/60": {"meeting_ids": [1, 4]},
                "meeting/4": {"committee_id": 60},
                "user/111": {"group_$_ids": ["1"], "group_$1_ids": [1]},
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "group_$_ids": {1: [2], 4: [5]},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {"group_$_ids": ["1", "4"], "group_$1_ids": [2], "group_$4_ids": [5]},
        )

    def test_perm_group_C_special_2_no_permission(self) -> None:
        """group C group_$_ids adding meeting in other committee
        with committee permission for both. Error 403, because touching
        2 committees requires OML permission
        """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60], self.user_id)
        self.set_models(
            {
                "user/111": {"group_$_ids": ["1"], "group_$1_ids": [1]},
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "group_$_ids": {1: [2], 4: [5]},
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "The user needs OrganizationManagementLevel.can_manage_users or CommitteeManagementLevel.can_manage for committees of following meetings or Permission user.can_manage for meetings {4}",
            response.json["message"],
        )

    def test_perm_group_C_special_3_both_permissions(self) -> None:
        """group C group_$_ids adding meeting in same committee
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
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "meeting_ids": [1],
                },
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "group_$_ids": {1: [2], 4: [5]},
            },
        )
        self.assert_status_code(response, 200)
        user = self.assert_model_exists(
            "user/111",
            {"group_$1_ids": [2], "group_$4_ids": [5]},
        )
        self.assertCountEqual(user["group_$_ids"], ["1", "4"])
        self.assertCountEqual(user["meeting_ids"], [1, 4])

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
                "committee_$_management_level": {
                    CommitteeManagementLevel.CAN_MANAGE: [60],
                },
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "committee_$can_manage_management_level": [60],
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
                "committee_$_management_level": {
                    CommitteeManagementLevel.CAN_MANAGE: [60, 63],
                },
            },
        )
        self.assert_status_code(response, 200)
        user111 = self.assert_model_exists(
            "user/111",
            {
                "committee_$_management_level": [CommitteeManagementLevel.CAN_MANAGE],
            },
        )
        self.assertCountEqual(
            user111.get("committee_$can_manage_management_level", []), [60, 63]
        )
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
                "committee_$_management_level": {
                    CommitteeManagementLevel.CAN_MANAGE: [63],
                },
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee 63",
            response.json["message"],
        )

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
                "committee_$_management_level": {
                    CommitteeManagementLevel.CAN_MANAGE: [60, 63],
                },
            },
        )
        self.assert_status_code(response, 200)
        user111 = self.assert_model_exists(
            "user/111",
            {
                "committee_$_management_level": [CommitteeManagementLevel.CAN_MANAGE],
            },
        )
        self.assertCountEqual(user111.get("committee_ids", []), [60, 63])
        self.assertCountEqual(
            user111.get("committee_$can_manage_management_level", []), [60, 63]
        )

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
                "committee_$_management_level": {
                    CommitteeManagementLevel.CAN_MANAGE: [60],
                },
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
            "Your organization management level is not high enough to set a Level of can_manage_organization!",
            response.json["message"],
        )

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

    def test_perm_group_F_demo_user_no_permission(self) -> None:
        """demo_user only editable by Superadmin"""
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION, self.user_id
        )
        self.update_model(
            f"user/{self.user_id}",
            {
                "committee_$_management_level": [CommitteeManagementLevel.CAN_MANAGE],
                "committee_$can_manage_management_level": [60],
            },
        )
        self.set_user_groups(self.user_id, [1, 2, 3])  # All including admin group

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

    def test_update_gender(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
        )
        response = self.request("user.update", {"id": 111, "gender": "test"})
        self.assert_status_code(response, 400)
        assert (
            "data.gender must be one of ['male', 'female', 'diverse', None]"
            in response.json["message"]
        )

        response = self.request("user.update", {"id": 111, "gender": "diverse"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/111", {"gender": "diverse"})

    def test_update_not_in_update_is_present_in_meeting_ids(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username111"},
        )
        response = self.request(
            "user.update", {"id": 111, "is_present_in_meting_ids": [1]}
        )
        self.assert_status_code(response, 400)
        assert (
            "data must not contain {'is_present_in_meting_ids'} properties"
            in response.json["message"]
        )

    def test_update_change_group(self) -> None:
        self.create_meeting()
        user_id = self.create_user_for_meeting(1)
        # assert user is already in meeting
        self.assert_model_exists("meeting/1", {"user_ids": [user_id]})
        self.set_user_groups(user_id, [2])
        # change user group from 2 to 1 in meeting 1
        response = self.request("user.update", {"id": user_id, "group_$_ids": {1: [1]}})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            f"user/{user_id}", {"group_$_ids": ["1"], "group_$1_ids": [1]}
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

    def test_update_hit_user_limit(self) -> None:
        self.set_models(
            {
                "organization/1": {"limit_of_users": 3},
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
                "organization/1": {"limit_of_users": 4},
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
                "vote_weight_$": {"110": "-6.000000"},
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "vote_weight_$ must be bigger than or equal to 0.",
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
                    "user_ids": [222, 223],
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
                },
                "meeting/2": {
                    "committee_id": 2,
                    "is_active_in_organization_id": 1,
                    "user_ids": [222, 223],
                },
                "meeting/3": {
                    "committee_id": 3,
                    "is_active_in_organization_id": 1,
                    "user_ids": [222, 223],
                },
                "group/11": {"meeting_id": 1, "user_ids": [222, 223]},
                "group/22": {"meeting_id": 2, "user_ids": [222, 223]},
                "group/33": {"meeting_id": 3, "user_ids": [222, 223]},
                "user/222": {
                    "meeting_ids": [1, 2, 3],
                    "committee_ids": [1, 2, 3],
                    "group_$_ids": ["1", "2", "3"],
                    "group_$1_ids": [11],
                    "group_$2_ids": [22],
                    "group_$3_ids": [33],
                },
                "user/223": {
                    "meeting_ids": [1, 3],
                    "committee_ids": [1, 3],
                    "committee_$can_manage_management_level": [1, 3],
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                    "group_$_ids": ["1", "3"],
                    "group_$1_ids": [11],
                    "group_$3_ids": [33],
                },
            }
        )
        response = self.request(
            "user.update",
            {
                "id": 223,
                "group_$_ids": {1: [], 2: [22]},
                "committee_$_management_level": {
                    CommitteeManagementLevel.CAN_MANAGE: [2, 3],
                },
            },
        )
        self.assert_status_code(response, 200)
        user = self.assert_model_exists(
            "user/223",
            {
                "committee_$_management_level": [CommitteeManagementLevel.CAN_MANAGE],
                "group_$1_ids": None,
                "group_$2_ids": [22],
                "group_$3_ids": [33],
            },
        )
        self.assertCountEqual(user.get("committee_ids", []), [2, 3])
        self.assertCountEqual(
            user.get("committee_$can_manage_management_level", []), [2, 3]
        )
        self.assertCountEqual(user.get("group_$_ids", []), ["2", "3"])
        self.assertCountEqual(user.get("meeting_ids", []), [2, 3])

        group = self.get_model("group/11")
        self.assertCountEqual(group.get("user_ids"), [222])
        group = self.get_model("group/22")
        self.assertCountEqual(group.get("user_ids"), [222, 223])
        group = self.get_model("group/33")
        self.assertCountEqual(group.get("user_ids"), [222, 223])
        meeting = self.get_model("meeting/1")
        self.assertCountEqual(meeting.get("user_ids"), [222])
        meeting = self.get_model("meeting/2")
        self.assertCountEqual(meeting.get("user_ids"), [222, 223])
        meeting = self.get_model("meeting/3")
        self.assertCountEqual(meeting.get("user_ids"), [222, 223])
        committee = self.get_model("committee/1")
        self.assertCountEqual(committee.get("user_ids"), [222])
        committee = self.get_model("committee/2")
        self.assertCountEqual(committee.get("user_ids"), [222, 223])
        committee = self.get_model("committee/3")
        self.assertCountEqual(committee.get("user_ids"), [222, 223])
