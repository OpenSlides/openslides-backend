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
                "username": "username_Xcdfgee",
                "default_vote_weight": "1.700000",
                "organization_management_level": "can_manage_users",
                "committee_ids": [78],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/111")
        assert model.get("username") == "username_Xcdfgee"
        assert model.get("default_vote_weight") == "1.700000"
        assert model.get("committee_ids") == [78]
        assert model.get("organization_management_level") == "can_manage_users"

    def test_update_template_fields(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "C1", "meeting_ids": [1]},
                "committee/2": {"name": "C2", "meeting_ids": [2]},
                "meeting/1": {"committee_id": 1},
                "meeting/2": {"committee_id": 2},
                "user/222": {"meeting_ids": [1]},
                "user/223": {
                    "committee_ids": [1],
                    "committee_$_management_level": ["1"],
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
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
                    1: None,
                    2: CommitteeManagementLevel.CAN_MANAGE,
                },
                "committee_ids": [2],
            },
        )
        self.assert_status_code(response, 200)
        user = self.get_model("user/223")
        assert user.get("committee_$1_management_level") is None
        assert (
            CommitteeManagementLevel(user.get("committee_$1_management_level"))
            == CommitteeManagementLevel.NO_RIGHT
        )
        assert (
            CommitteeManagementLevel(user.get("committee_$2_management_level"))
            == CommitteeManagementLevel.CAN_MANAGE
        )
        assert user.get("committee_ids") == [2]
        assert user.get("group_$1_ids") == [11]
        assert user.get("group_$2_ids") == [22]
        assert set(user.get("group_$_ids", [])) == {"1", "2"}
        assert user.get("vote_delegations_$1_from_ids") == [222]
        assert user.get("vote_delegations_$_from_ids") == ["1"]
        assert user.get("comment_$1") == "comment&lt;iframe&gt;&lt;/iframe&gt;"
        assert user.get("comment_$") == ["1"]
        assert user.get("number_$2") == "number"
        assert user.get("number_$") == ["2"]
        assert user.get("structure_level_$1") == "level_1"
        assert user.get("structure_level_$2") == "level_2"
        assert set(user.get("structure_level_$", [])) == {"1", "2"}
        assert user.get("about_me_$1") == "<p>about</p>&lt;iframe&gt;&lt;/iframe&gt;"
        assert user.get("about_me_$") == ["1"]
        assert user.get("vote_weight_$1") == "1.000000"
        assert user.get("vote_weight_$2") == "2.333333"
        assert set(user.get("vote_weight_$", [])) == {"1", "2"}
        assert user.get("meeting_ids") == [1, 2]
        user = self.get_model("user/222")
        assert user.get("vote_delegated_$1_to_id") == 223
        assert user.get("vote_delegated_$_to_id") == ["1"]
        group1 = self.get_model("group/11")
        assert group1.get("user_ids") == [223]
        group2 = self.get_model("group/22")
        assert group2.get("user_ids") == [223]
        meeting = self.get_model("meeting/1")
        assert meeting.get("user_ids") == [223]
        meeting = self.get_model("meeting/2")
        assert meeting.get("user_ids") == [223]

    def test_update_committee_manager_without_committee_ids(self) -> None:
        """ Giving committee management level requires committee_ids """
        self.set_models(
            {
                "user/111": {"username": "username_srtgb123"},
                "committee/60": {"name": "c60"},
                "committee/61": {"name": "c61"},
            }
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "username": "usersname",
                "committee_$_management_level": {
                    "60": CommitteeManagementLevel.CAN_MANAGE,
                    "61": CommitteeManagementLevel.CAN_MANAGE,
                },
                "committee_ids": [61],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "You must add the user to the committee(s) '60', because you want to give him committee management level permissions.",
            response.json["message"],
        )

    def test_update_group_switch_change_meeting_ids(self) -> None:
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

    def test_update_remove_group_from_user(self) -> None:
        """ May update group A fields on meeting scope. User belongs to 1 meeting without being part of a committee """
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

    def test_update_wrong_id(self) -> None:
        self.create_model(
            "user/111",
            {"username": "username_srtgb123"},
        )
        response = self.request(
            "user.update", {"id": 112, "username": "username_Xcdfgee"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Datastore service sends HTTP 400. Model 'user/112' does not exist.",
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

    def test_update_same_username(self) -> None:
        response = self.request("user.update", {"id": 1, "username": "admin"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"username": "admin"})

    def test_update_permission_nothing(self) -> None:
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

    def test_update_permission_auth_error(self) -> None:
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

    def test_update_permission_superadmin(self) -> None:
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

    def test_update_permission_group_A_oml_manage_user(self) -> None:
        """ May update group A fields on organsisation scope, because belongs to 2 meetings in 2 committees, requiring OML level permission"""
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
            },
        )

    def test_update_permission_group_A_cml_manage_user(self) -> None:
        """ May update group A fields on committee scope. User belongs to 1 meeting in 1 committee """
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

    def test_update_permission_group_A_meeting_manage_user(self) -> None:
        """ May update group A fields on meeting scope. User belongs to 1 meeting without being part of a committee """
        self.permission_setup()
        self.set_user_groups(self.user_id, [2])
        self.set_user_groups(111, [1])

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
                "committee_ids": None,
            },
        )

    def test_update_permission_group_A_no_permission(self) -> None:
        """ May not update group A fields on organsisation scope, although having both committee permissions"""
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

    def test_update_permission_group_B_user_can_manage(self) -> None:
        """ update group B fields for 2 meetings with simple user.can_manage permissions """
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
                "meeting_ids": [1, 4],
            },
        )

    def test_update_permission_group_B_user_can_manage_no_permission(self) -> None:
        """ Group B fields needs explicit user.can_manage permission for meeting """
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

    def test_update_permission_group_C_oml_manager(self) -> None:
        """ May update group C group_$_ids by OML permission """
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

    def test_update_permission_group_C_committee_manager(self) -> None:
        """ May update group C group_$_ids by committee permission """
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

    def test_update_permission_group_C_user_can_manage(self) -> None:
        """ May update group C group_$_ids by user.can_manage permission with admin group of all related meetings """
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
        self.assert_model_exists(
            "user/111",
            {
                "group_$_ids": ["1", "4"],
                "group_$1_ids": [2],
                "group_$4_ids": [5],
                "meeting_ids": [1, 4],
            },
        )

    def test_update_permission_group_C_no_permission(self) -> None:
        """ May not update group C group_$_ids """
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

    def test_update_permission_group_C_special_1(self) -> None:
        """ group C group_$_ids adding meeting in same committee with committee permission """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60], self.user_id)
        self.set_models(
            {
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

    def test_update_permission_group_C_special_2_no_permission(self) -> None:
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
            "You need OrganizationManagementLevel.can_manage_users, because you try to add or remove meetings in Organization-scope!",
            response.json["message"],
        )

    def test_update_permission_group_C_special_3_no_permission(self) -> None:
        """group C group_$_ids adding meeting in same committee
        with meeting permission for both. Error 403, because touching
        2 meetings requires Committee permission
        """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_user_groups(self.user_id, [2, 5])  # Admin groups meeting/1 and 4
        self.set_models(
            {
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
        self.assert_status_code(response, 403)
        self.assertIn(
            "You need CommitteeManagementLevel.can_manage permission for committee 60, because you try to add or remove meetings in Committee-scope!",
            response.json["message"],
        )

    def test_update_permission_group_D_permission_with_OML(self) -> None:
        """ May update Group D committee fields with OML level permission """
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_$_management_level": {
                    "60": CommitteeManagementLevel.CAN_MANAGE
                },
                "committee_ids": [60],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "committee_$60_management_level": CommitteeManagementLevel.CAN_MANAGE,
                "committee_ids": [60],
            },
        )

    def test_update_permission_group_D_permission_with_CML(self) -> None:
        """ May update Group D committee fields with CML permission for all committees """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60, 63], self.user_id)

        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_$_management_level": {
                    "60": CommitteeManagementLevel.CAN_MANAGE,
                    "63": CommitteeManagementLevel.CAN_MANAGE,
                },
                "committee_ids": [60, 63],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "committee_$60_management_level": CommitteeManagementLevel.CAN_MANAGE,
                "committee_$63_management_level": CommitteeManagementLevel.CAN_MANAGE,
            },
        )
        self.assertCountEqual(
            self.get_model("user/111").get("committee_ids", []), [60, 63]
        )

    def test_update_permission_group_D_no_permission(self) -> None:
        """ May not update Group D committee fields, because of missing CML permission for one committee """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_committee_management_level([60], self.user_id)
        self.set_committee_management_level([60], 111)

        response = self.request(
            "user.update",
            {
                "id": 111,
                "committee_$_management_level": {
                    "63": CommitteeManagementLevel.CAN_MANAGE,
                },
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee 63",
            response.json["message"],
        )

    def test_update_permission_group_D_permission_with_CML_and_untouched_committee(
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
                    "60": CommitteeManagementLevel.CAN_MANAGE,
                },
                "committee_ids": [60, 63],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/111",
            {
                "committee_$60_management_level": CommitteeManagementLevel.CAN_MANAGE,
                "committee_$63_management_level": CommitteeManagementLevel.CAN_MANAGE,
            },
        )
        self.assertCountEqual(
            [60, 63], self.get_model("user/111").get("committee_ids", [])
        )

    def test_update_permission_group_D_permission_with_CML_missing_permission(
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
                    "60": CommitteeManagementLevel.CAN_MANAGE,
                },
                "committee_ids": [60],
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.update. Missing permission: CommitteeManagementLevel can_manage in committee 63",
            response.json["message"],
        )

    def test_update_permission_group_E_OML_high_enough(self) -> None:
        """ OML level to set is sufficient """
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

    def test_update_permission_group_E_OML_not_high_enough(self) -> None:
        """ OML level to set is higher than level of request user """
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.update",
            {
                "id": 111,
                "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANISATION,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Your organization management level is not high enough to set a Level of can_manage_organization!",
            response.json["message"],
        )

    def test_update_permission_group_F_demo_user_permission(self) -> None:
        """ demo_user only editable by Superadmin """
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

    def test_update_permission_group_F_demo_user_no_permission(self) -> None:
        """ demo_user only editable by Superadmin """
        self.permission_setup()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANISATION, self.user_id
        )
        self.update_model(
            f"user/{self.user_id}",
            {
                "committee_$60_management_level": "can_manage",
                "committee_$_management_level": ["60"],
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
