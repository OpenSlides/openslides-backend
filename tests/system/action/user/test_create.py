from openslides_backend.permissions.permissions import (
    OrganisationManagementLevel,
    Permissions,
)
from tests.system.action.base import BaseActionTestCase


class UserCreateActionTest(BaseActionTestCase):
    def permission_setup(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("test", group_ids=[1])
        self.login(self.user_id)

    def test_create(self) -> None:
        """
        Also checks if a default_password is generated and the correct hashed password stored
        """
        response = self.request("user.create", {"username": "test_Xcdfgee"})
        self.assert_status_code(response, 200)
        model = self.get_model("user/2")
        assert model.get("username") == "test_Xcdfgee"
        assert model.get("default_password") is not None
        assert self.auth.is_equals(
            model.get("default_password", ""), model.get("password", "")
        )

    def test_create_some_more_fields(self) -> None:
        """
        Also checks if the correct password is stored from the given default_password
        """
        self.set_models(
            {
                "meeting/110": {"name": "name_DsJFXoot"},
                "meeting/111": {"name": "name_xXRGTLAJ"},
                "committee/78": {"name": "name_TSXpBGdt"},
                "committee/79": {"name": "name_hOldWvVF"},
            }
        )
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "default_vote_weight": "1.500000",
                "organisation_management_level": "can_manage_users",
                "guest_meeting_ids": [110, 111],
                "committee_as_member_ids": [78],
                "committee_as_manager_ids": [79],
                "default_password": "password",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("user/2")
        assert model.get("username") == "test_Xcdfgee"
        assert model.get("default_vote_weight") == "1.500000"
        assert model.get("guest_meeting_ids") == [110, 111]
        assert model.get("committee_as_member_ids") == [78]
        assert model.get("committee_as_manager_ids") == [79]
        assert model.get("organisation_management_level") == "can_manage_users"
        assert model.get("default_password") == "password"
        assert self.auth.is_equals(
            model.get("default_password", ""), model.get("password", "")
        )
        # check meeting.user_ids
        meeting = self.get_model("meeting/110")
        assert meeting.get("user_ids") == [2]
        meeting = self.get_model("meeting/111")
        assert meeting.get("user_ids") == [2]

    def test_create_template_fields(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "meeting/2": {},
                "user/222": {"meeting_id": 1},
                "group/11": {"meeting_id": 1},
                "group/22": {"meeting_id": 2},
            }
        )
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "group_$_ids": {1: [11], 2: [22]},
                "vote_delegations_$_from_ids": {1: [222]},
                "comment_$": {1: "comment<iframe></iframe>"},
                "number_$": {2: "number"},
                "structure_level_$": {1: "level_1", 2: "level_2"},
                "about_me_$": {1: "<p>about</p><iframe></iframe>"},
                "vote_weight_$": {1: "1.000000", 2: "2.333333"},
            },
        )
        self.assert_status_code(response, 200)
        user = self.get_model("user/223")
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

    def test_invalid_template_field_replacement_invalid_meeting(self) -> None:
        self.create_model("meeting/1")
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "comment_$": {2: "comment"},
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "'meeting/2' does not exist",
            response.json["message"],
        )

    def test_invalid_template_field_replacement_str(self) -> None:
        self.create_model("meeting/1")
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "comment_$": {"str": "comment"},
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.comment_$ must not contain {'str'} properties",
            response.json["message"],
        )

    def test_create_invalid_group_id(self) -> None:
        self.set_models(
            {
                "meeting/1": {},
                "meeting/2": {},
                "group/11": {"meeting_id": 1},
            }
        )
        response = self.request(
            "user.create",
            {
                "username": "test_Xcdfgee",
                "group_$_ids": {2: [11]},
            },
        )
        self.assert_status_code(response, 400)

    def test_create_empty_data(self) -> None:
        response = self.request("user.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['username'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        response = self.request(
            "user.create", {"wrong_field": "text_AefohteiF8", "username": "test1"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_username_already_given(self) -> None:
        response = self.request("user.create", {"username": "admin"})
        self.assert_status_code(response, 400)
        assert (
            response.json["message"] == "A user with the username admin already exists."
        )

    def test_user_create_with_empty_vote_delegation_from_ids(self) -> None:
        response = self.request(
            "user.create", {"username": "testname", "vote_delegations_$_from_ids": {}}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2", {"username": "testname", "vote_delegations_$_from_ids": []}
        )

    def test_create_empty_username(self) -> None:
        response = self.request("user.create", {"username": ""})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.username must be longer than or equal to 1 characters",
            response.json["message"],
        )

    def test_create_permission_nothing(self) -> None:
        self.permission_setup()
        response = self.request(
            "user.create",
            {
                "username": "username",
                "vote_weight_$": {1: "1.000000"},
                "group_$_ids": {1: [1]},
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "or alternative {'CommitteeManagementLevel.MANAGER for meetings {1}'}.",
            response.json["message"],
        )

    def test_create_permission_auth_error(self) -> None:
        self.permission_setup()
        response = self.request(
            "user.create",
            {
                "username": "username_Neu",
                "vote_weight_$": {1: "1.000000"},
                "group_$_ids": {1: [1]},
            },
            anonymous=True,
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Anonymous user is not allowed to change user data.",
            response.json["message"],
        )

    def test_create_permission_superadmin(self) -> None:
        """
        SUPERADMIN may set fields of all groups and may set an other user as SUPERADMIN, too.
        The SUPERADMIN don't need to belong to a meeting in any way to change data!
        """
        self.permission_setup()
        self.set_management_level(OrganisationManagementLevel.SUPERADMIN, self.user_id)

        response = self.request(
            "user.create",
            {
                "username": "username_new",
                "organisation_management_level": OrganisationManagementLevel.SUPERADMIN,
                "vote_weight_$": {1: "1.000000"},
                "group_$_ids": {1: [1]},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/3",
            {
                "username": "username_new",
                "organisation_management_level": OrganisationManagementLevel.SUPERADMIN,
                "vote_weight_$": ["1"],
                "vote_weight_$1": "1.000000",
                "group_$_ids": ["1"],
                "group_$1_ids": [1],
            },
        )

    def test_create_permission_committee_manager(self) -> None:
        """ May create group A and C fields """
        self.permission_setup()
        self.create_meeting(base=4)
        self.update_model(
            f"user/{self.user_id}",
            {
                "committee_as_manager_ids": [60, 63],
                "organisation_management_level": OrganisationManagementLevel.CAN_MANAGE_USERS,
            },
        )

        response = self.request(
            "user.create",
            {
                "username": "username",
                "group_$_ids": {1: [1], 4: [5]},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/3",
            {
                "group_$_ids": ["1", "4"],
                "group_$1_ids": [1],
                "group_$4_ids": [5],
                "username": "username",
            },
        )

    def test_create_permission_committee_manager_no_permission(self) -> None:
        """ vote_weight_$ is in group B and may only work with meeting-Permission  """
        self.permission_setup()
        self.update_model(
            f"user/{self.user_id}",
            {
                "committee_as_manager_ids": [60],
                "organisation_management_level": OrganisationManagementLevel.CAN_MANAGE_USERS,
                "group_$_ids": ["1", "4"],
                "group_$1_ids": [2],  # admin group of meeting/1
                "group_$4_ids": [4],  # default group of meeting/4
            },
        )
        response = self.request(
            "user.create",
            {
                "username": "username",
                "group_$_ids": {1: [1], 4: [5]},
                "vote_weight_$": {1: "1.000000"},
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.create. Missing permissions {'user.can_manage for meeting 4'} or alternative {'CommitteeManagementLevel.MANAGER for meetings {4}'}.",
            response.json["message"],
        )

    def test_create_permission_manage_user(self) -> None:
        """ May create group A fields only """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_management_level(
            OrganisationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.create",
            {
                "username": "username",
                "title": "title",
                "first_name": "first_name",
                "last_name": "last_name",
                "is_active": True,
                "is_physical_person": True,
                "default_password": "new default_password",
                "gender": "female",
                "email": "info@openslides.com ",
                "default_number": "new default_number",
                "default_structure_level": "new default_structure_level",
                "default_vote_weight": "1.234000",
                "organisation_management_level": OrganisationManagementLevel.CAN_MANAGE_USERS,
                "committee_as_member_ids": [60],
                "committee_as_manager_ids": [63],
                "guest_meeting_ids": [1, 4],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/3",
            {
                "username": "username",
                "title": "title",
                "first_name": "first_name",
                "last_name": "last_name",
                "is_active": True,
                "is_physical_person": True,
                "default_password": "new default_password",
                "gender": "female",
                "email": "info@openslides.com ",
                "default_number": "new default_number",
                "default_structure_level": "new default_structure_level",
                "default_vote_weight": "1.234000",
                "organisation_management_level": OrganisationManagementLevel.CAN_MANAGE_USERS,
                "committee_as_member_ids": [60],
                "committee_as_manager_ids": [63],
                "guest_meeting_ids": [1, 4],
            },
        )

    def test_create_permission_user_can_manage(self) -> None:
        """ May create all group-fields """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_management_level(
            OrganisationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )
        self.set_user_groups(
            self.user_id, [2, 6]
        )  # admin-group of meeting/1 and group of meeting/4
        self.set_group_permissions(6, [Permissions.User.CAN_MANAGE])
        self.create_user("user3", [4])
        self.create_user("user4", [4])

        response = self.request(
            "user.create",
            {
                "username": "username",
                "number_$": {"1": "number1", "4": "number1 in 4"},
                "structure_level_$": {"1": "structure_level 1"},
                "vote_weight_$": {"1": "12.002345"},
                "about_me_$": {"1": "about me 1"},
                "comment_$": {"1": "comment zu meeting/1"},
                "vote_delegated_$_to_id": {"1": self.user_id},
                "vote_delegations_$_from_ids": {"4": [3, 4]},
                "group_$_ids": {"1": [2, 3], "4": [5]},
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/5",
            {
                "username": "username",
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
                "vote_delegations_$4_from_ids": [3, 4],
                "group_$1_ids": [2, 3],
                "group_$4_ids": [5],
            },
        )

    def test_create_permission_user_can_manage_no_permission(self) -> None:
        """ May create group A, B and C fields """
        self.permission_setup()
        self.create_meeting(base=4)
        self.set_management_level(
            OrganisationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )
        self.set_user_groups(self.user_id, [3, 6])
        self.set_group_permissions(3, [Permissions.User.CAN_MANAGE])

        response = self.request(
            "user.create",
            {
                "username": "username",
                "number_$": {"1": "number1", "4": "number1 in 4"},
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.create. Missing permissions {'user.can_manage for meeting 4'}",
            response.json["message"],
        )

    def test_create_permission_OML_not_high_enough(self) -> None:
        """ May create group A fields only """
        self.permission_setup()
        self.set_management_level(
            OrganisationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )

        response = self.request(
            "user.create",
            {
                "username": "username",
                "organisation_management_level": OrganisationManagementLevel.CAN_MANAGE_ORGANISATION,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "Your Organisation Management Level is not high enough to set a Level of can_manage_organisation!",
            response.json["message"],
        )

    def test_create_permission_set_1(self) -> None:
        """ Rights for all field groups, but missing rights for meeting/4 """
        self.create_meeting()
        self.create_meeting(base=4)
        self.user_id = self.create_user(
            "test", group_ids=[2]
        )  # admin-group of meeting/1
        self.login(self.user_id)
        self.set_management_level(
            OrganisationManagementLevel.CAN_MANAGE_USERS, self.user_id
        )
        response = self.request(
            "user.create",
            {
                # Group A
                "username": "username",
                "default_vote_weight": "1.700000",
                "organisation_management_level": "can_manage_users",
                "guest_meeting_ids": [1, 4],
                "committee_as_member_ids": [78],
                "committee_as_manager_ids": [78],
                # Group B
                "vote_delegations_$_from_ids": {1: [222]},
                "comment_$": {1: "comment<iframe></iframe>"},
                "number_$": {4: "number"},
                "structure_level_$": {1: "level_1", 4: "level_2"},
                "about_me_$": {1: "<p>about</p><iframe></iframe>"},
                "vote_weight_$": {1: "1.000000", 4: "2.333333"},
                # Group C
                "group_$_ids": {1: [1]},
            },
        )

        self.assert_status_code(response, 403)
        self.assertIn("You do not belong to meeting 4", response.json["message"])
