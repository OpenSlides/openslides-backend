from tests.system.action.base import BaseActionTestCase


class UserAssignMeetings(BaseActionTestCase):
    def test_assign_meetings_correct(self) -> None:
        self.set_models(
            {
                "group/11": {
                    "name": "to_find",
                    "meeting_id": 1,
                    "meeting_user_ids": [1],
                },
                "group/22": {
                    "name": "nothing",
                    "meeting_id": 2,
                    "meeting_user_ids": [2],
                },
                "group/31": {"name": "to_find", "meeting_id": 3},
                "group/43": {"name": "standard", "meeting_id": 4},
                "group/51": {"name": "to_find", "meeting_id": 5},
                "group/52": {
                    "name": "nothing",
                    "meeting_id": 5,
                    "meeting_user_ids": [5],
                },
                "meeting/1": {
                    "name": "success(existing)",
                    "group_ids": [11],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                    "meeting_user_ids": [1],
                },
                "meeting/2": {
                    "name": "nothing",
                    "group_ids": [22],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                    "meeting_user_ids": [2],
                },
                "meeting/3": {
                    "name": "success(added)",
                    "group_ids": [31],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                },
                "meeting/4": {
                    "name": "standard",
                    "group_ids": [43],
                    "is_active_in_organization_id": 1,
                    "default_group_id": 43,
                    "committee_id": 2,
                },
                "meeting/5": {
                    "name": "success(added)",
                    "group_ids": [51, 52],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                    "meeting_user_ids": [5],
                },
                "user/1": {
                    "meeting_user_ids": [1, 2, 5],
                    "meeting_ids": [1, 2, 5],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [11],
                },
                "meeting_user/2": {
                    "meeting_id": 2,
                    "user_id": 1,
                    "group_ids": [22],
                },
                "meeting_user/5": {
                    "meeting_id": 5,
                    "user_id": 1,
                    "group_ids": [52],
                },
                "committee/2": {"meeting_ids": [1, 2, 3, 4, 5]},
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1, 2, 3, 4, 5],
                "group_name": "to_find",
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["succeeded"] == [1, 3, 5]
        assert response.json["results"][0][0]["standard_group"] == [4]
        assert response.json["results"][0][0]["nothing"] == [2]
        self.assert_model_exists(
            "meeting_user/1", {"meeting_id": 1, "user_id": 1, "group_ids": [11]}
        )
        self.assert_model_exists(
            "meeting_user/2", {"meeting_id": 2, "user_id": 1, "group_ids": [22]}
        )
        self.assert_model_exists(
            "meeting_user/5", {"meeting_id": 5, "user_id": 1, "group_ids": [51, 52]}
        )
        self.assert_model_exists(
            "meeting_user/6", {"meeting_id": 3, "user_id": 1, "group_ids": [31]}
        )
        self.assert_model_exists(
            "meeting_user/7", {"meeting_id": 4, "user_id": 1, "group_ids": [43]}
        )

    def test_assign_meetings_ignore_meetings_anonymous_group(self) -> None:
        """
        ...and don't ignore groups that are just named "Anonymous"
        """
        self.set_models(
            {
                "group/11": {
                    "name": "Anonymous",
                    "meeting_id": 1,
                    "meeting_user_ids": [1],
                },
                "group/22": {
                    "name": "nothing",
                    "meeting_id": 2,
                    "meeting_user_ids": [2],
                },
                "group/31": {
                    "name": "Anonymous",
                    "meeting_id": 3,
                    "anonymous_group_for_meeting_id": 3,
                },
                "group/32": {
                    "name": "standard",
                    "meeting_id": 3,
                    "default_group_for_meeting_id": 3,
                },
                "group/43": {"name": "standard", "meeting_id": 4},
                "group/51": {"name": "Anonymous", "meeting_id": 5},
                "group/52": {
                    "name": "Anonymous",
                    "meeting_id": 5,
                    "anonymous_group_for_meeting_id": 5,
                },
                "meeting/1": {
                    "name": "success(existing)",
                    "group_ids": [11],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                    "meeting_user_ids": [1],
                },
                "meeting/2": {
                    "name": "nothing",
                    "group_ids": [22],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                    "meeting_user_ids": [2],
                },
                "meeting/3": {
                    "name": "success(added)",
                    "group_ids": [30, 31],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                    "default_group_id": 32,
                },
                "meeting/4": {
                    "name": "standard",
                    "group_ids": [43],
                    "is_active_in_organization_id": 1,
                    "default_group_id": 43,
                    "committee_id": 2,
                },
                "meeting/5": {
                    "name": "success(added)",
                    "group_ids": [51, 52],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                },
                "user/1": {
                    "meeting_user_ids": [1, 2, 5],
                    "meeting_ids": [1, 2, 5],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [11],
                },
                "meeting_user/2": {
                    "meeting_id": 2,
                    "user_id": 1,
                    "group_ids": [22],
                },
                "committee/2": {"meeting_ids": [1, 2, 3, 4, 5]},
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1, 2, 3, 4, 5],
                "group_name": "Anonymous",
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["succeeded"] == [1, 5]
        assert response.json["results"][0][0]["standard_group"] == [3, 4]
        assert response.json["results"][0][0]["nothing"] == [2]
        self.assert_model_exists(
            "meeting_user/1", {"meeting_id": 1, "user_id": 1, "group_ids": [11]}
        )
        self.assert_model_exists(
            "meeting_user/2", {"meeting_id": 2, "user_id": 1, "group_ids": [22]}
        )
        self.assert_model_exists(
            "meeting_user/3", {"meeting_id": 5, "user_id": 1, "group_ids": [51]}
        )
        self.assert_model_exists(
            "meeting_user/4", {"meeting_id": 3, "user_id": 1, "group_ids": [32]}
        )
        self.assert_model_exists(
            "meeting_user/5", {"meeting_id": 4, "user_id": 1, "group_ids": [43]}
        )

    def test_assign_meetings_multiple_committees(self) -> None:
        self.set_models(
            {
                "group/11": {
                    "name": "to_find",
                    "meeting_id": 1,
                },
                "group/22": {
                    "name": "to_find",
                    "meeting_id": 2,
                },
                "meeting/1": {
                    "name": "m1",
                    "group_ids": [11],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                },
                "meeting/2": {
                    "name": "m2",
                    "group_ids": [22],
                    "is_active_in_organization_id": 1,
                    "committee_id": 3,
                },
                "committee/2": {"meeting_ids": [1]},
                "committee/3": {"meeting_ids": [2]},
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1, 2],
                "group_name": "to_find",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"committee_ids": [2, 3]})

    def test_assign_meetings_with_existing_user_in_group(self) -> None:
        self.set_models(
            {
                "group/1": {"name": "Test", "meeting_id": 1, "meeting_user_ids": [2]},
                "meeting/1": {
                    "name": "Find Test",
                    "group_ids": [1],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                },
                "user/2": {
                    "meeting_user_ids": [2],
                    "meeting_ids": [1],
                },
                "committee/2": {"meeting_ids": [1]},
                "meeting_user/2": {"meeting_id": 1, "user_id": 2, "group_ids": [1]},
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1],
                "group_name": "Test",
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["succeeded"] == [1]
        assert response.json["results"][0][0]["standard_group"] == []
        assert response.json["results"][0][0]["nothing"] == []
        self.assert_model_exists(
            "user/1",
        )
        self.assert_model_exists(
            "user/2",
            {
                "meeting_ids": [1],
            },
        )

        group1 = self.assert_model_exists("group/1")
        assert sorted(group1.get("meeting_user_ids", [])) == [2, 3]

    def test_assign_meetings_group_not_found(self) -> None:
        self.set_models(
            {
                "group/1": {"name": "Test", "meeting_id": 1},
                "meeting/1": {
                    "name": "Find Test",
                    "group_ids": [1],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                    "default_group_id": 1,
                },
                "user/2": {},
                "committee/2": {"meeting_ids": [1]},
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 2,
                "meeting_ids": [1],
                "group_name": "Broken",
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["succeeded"] == []
        assert response.json["results"][0][0]["standard_group"] == [1]
        assert response.json["results"][0][0]["nothing"] == []
        self.assert_model_exists(
            "user/2",
            {"meeting_ids": [1], "meeting_user_ids": [1]},
        )
        self.assert_model_exists("group/1", {"meeting_user_ids": [1]})

    def test_assign_meetings_group_not_found_2(self) -> None:
        self.set_models(
            {
                "group/1": {"name": "Test", "meeting_id": 1, "meeting_user_ids": [2]},
                "meeting/1": {
                    "name": "Find Test",
                    "group_ids": [1],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                    "default_group_id": 1,
                },
                "user/2": {
                    "meeting_user_ids": [2],
                    "meeting_ids": [1],
                },
                "meeting_user/2": {"meeting_id": 1, "user_id": 2, "group_ids": [1]},
                "committee/2": {"meeting_ids": [1]},
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 2,
                "meeting_ids": [1],
                "group_name": "Broken",
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["succeeded"] == []
        assert response.json["results"][0][0]["standard_group"] == []
        assert response.json["results"][0][0]["nothing"] == [1]

    def test_assign_meetings_no_permissions(self) -> None:
        self.set_models(
            {
                "group/1": {"name": "Test", "meeting_id": 1},
                "group/2": {"name": "Default Group", "meeting_id": 2},
                "group/3": {"name": "In Meeting", "meeting_id": 3},
                "meeting/1": {
                    "name": "Find Test",
                    "group_ids": [1],
                    "is_active_in_organization_id": 1,
                },
                "meeting/2": {
                    "name": "No Test and Not in Meeting",
                    "group_ids": [2],
                    "is_active_in_organization_id": 1,
                },
                "meeting/3": {
                    "name": "No Test and in Meeting",
                    "group_ids": [3],
                    "is_active_in_organization_id": 1,
                },
                "user/1": {
                    "organization_management_level": None,
                },
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1, 2, 3],
                "group_name": "Test",
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "Missing OrganizationManagementLevel: can_manage_users"
            in response.json["message"]
        )

    def test_assign_meetings_archived_meetings(self) -> None:
        self.set_models(
            {
                "group/1": {"name": "Test", "meeting_id": 1},
                "group/2": {"name": "Default Group", "meeting_id": 2},
                "group/3": {"name": "In Meeting", "meeting_id": 3},
                "meeting/1": {
                    "name": "Archived",
                    "group_ids": [1],
                },
                "meeting/2": {
                    "name": "No Test and Not in Meeting",
                    "group_ids": [2],
                    "is_active_in_organization_id": 1,
                },
                "meeting/3": {
                    "name": "No Test and in Meeting",
                    "group_ids": [3],
                    "is_active_in_organization_id": 1,
                },
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1, 2, 3],
                "group_name": "Test",
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Meeting Archived/1 cannot be changed, because it is archived."
            in response.json["message"]
        )

    def test_assign_meetings_with_locked_meetings(self) -> None:
        self.set_models(
            {
                "group/11": {
                    "name": "to_find",
                    "meeting_id": 1,
                    "meeting_user_ids": [1],
                },
                "group/22": {
                    "name": "nothing",
                    "meeting_id": 2,
                    "meeting_user_ids": [2],
                },
                "group/31": {"name": "to_find", "meeting_id": 3},
                "group/43": {"name": "standard", "meeting_id": 4},
                "group/51": {"name": "to_find", "meeting_id": 5},
                "group/52": {
                    "name": "nothing",
                    "meeting_id": 5,
                    "meeting_user_ids": [5],
                },
                "meeting/1": {
                    "name": "success(existing)",
                    "group_ids": [11],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                    "meeting_user_ids": [1],
                },
                "meeting/2": {
                    "name": "nothing",
                    "group_ids": [22],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                    "meeting_user_ids": [2],
                    "locked_from_inside": True,
                },
                "meeting/3": {
                    "name": "success(added)",
                    "group_ids": [31],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                    "locked_from_inside": False,
                },
                "meeting/4": {
                    "name": "standard",
                    "group_ids": [43],
                    "is_active_in_organization_id": 1,
                    "default_group_id": 43,
                    "committee_id": 2,
                    "locked_from_inside": True,
                },
                "meeting/5": {
                    "name": "success(added)",
                    "group_ids": [51, 52],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                    "meeting_user_ids": [5],
                },
                "user/1": {
                    "meeting_user_ids": [1, 2, 5],
                    "meeting_ids": [1, 2, 5],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [11],
                },
                "meeting_user/2": {
                    "meeting_id": 2,
                    "user_id": 1,
                    "group_ids": [22],
                },
                "meeting_user/5": {
                    "meeting_id": 5,
                    "user_id": 1,
                    "group_ids": [52],
                },
                "committee/2": {"meeting_ids": [1, 2, 3, 4, 5]},
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1, 2, 3, 4, 5],
                "group_name": "to_find",
            },
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Cannot assign meetings because some selected meetings are locked: 2, 4."
        )
