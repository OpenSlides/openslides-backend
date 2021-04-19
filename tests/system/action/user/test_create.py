from openslides_backend.permissions.permissions import OrganisationManagementLevel
from tests.system.action.base import BaseActionTestCase


class UserCreateActionTest(BaseActionTestCase):
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

    def test_create_no_permission(self) -> None:
        self.update_model("user/1", {"organisation_management_level": None})
        response = self.request("user.create", {"username": "test_Xcdfgee"})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.create. Missing permission: can_manage_users",
            response.json["message"],
        )

    def test_create_permission(self) -> None:
        self.update_model(
            "user/1",
            {
                "organisation_management_level": OrganisationManagementLevel.CAN_MANAGE_USERS
            },
        )
        response = self.request("user.create", {"username": "test_Xcdfgee"})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"username": "test_Xcdfgee"})
