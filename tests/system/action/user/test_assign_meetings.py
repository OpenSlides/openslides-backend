from tests.system.action.base import BaseActionTestCase


class UserAssignMeetings(BaseActionTestCase):
    def test_assign_meetings_correct(self) -> None:
        self.set_models(
            {
                "group/11": {"name": "to_find", "meeting_id": 1, "user_ids": [1]},
                "group/22": {"name": "nothing", "meeting_id": 2, "user_ids": [1]},
                "group/31": {"name": "to_find", "meeting_id": 3},
                "group/43": {"name": "standard", "meeting_id": 4},
                "group/51": {"name": "to_find", "meeting_id": 5},
                "group/52": {"name": "nothing", "meeting_id": 5, "user_ids": [1]},
                "meeting/1": {
                    "name": "success(existing)",
                    "group_ids": [11],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                },
                "meeting/2": {
                    "name": "nothing",
                    "group_ids": [22],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
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
                },
                "user/1": {
                    "group_$_ids": ["1", "2", "5"],
                    "group_$1_ids": [11],
                    "group_$2_ids": [22],
                    "group_$5_ids": [52],
                    "meeting_ids": [1, 2, 5],
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
        user1 = self.assert_model_exists(
            "user/1",
            {
                "group_$1_ids": [11],
                "group_$2_ids": [22],
                "group_$3_ids": [31],
                "group_$4_ids": [43],
            },
        )
        assert sorted(user1.get("group_$_ids", [])) == ["1", "2", "3", "4", "5"]
        assert sorted(user1.get("group_$5_ids", [])) == [51, 52]
        assert sorted(user1.get("meeting_ids", [])) == [1, 2, 3, 4, 5]
        self.assert_model_exists("group/11", {"user_ids": [1]})
        self.assert_model_exists("group/22", {"user_ids": [1]})
        self.assert_model_exists("group/31", {"user_ids": [1]})
        self.assert_model_exists("group/43", {"user_ids": [1]})
        self.assert_model_exists("group/51", {"user_ids": [1]})
        self.assert_model_exists("group/52", {"user_ids": [1]})

    def test_assign_meetings_with_existing_user_in_group(self) -> None:
        self.set_models(
            {
                "group/1": {"name": "Test", "meeting_id": 1, "user_ids": [2]},
                "meeting/1": {
                    "name": "Find Test",
                    "group_ids": [1],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                },
                "user/2": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "meeting_ids": [1],
                },
                "committee/2": {"meeting_ids": [1]},
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
            {
                "group_$_ids": ["1"],
                "group_$1_ids": [1],
                "meeting_ids": [1],
            },
        )
        self.assert_model_exists(
            "user/2",
            {
                "group_$_ids": ["1"],
                "group_$1_ids": [1],
                "meeting_ids": [1],
            },
        )

        group1 = self.assert_model_exists("group/1")
        assert sorted(group1.get("user_ids", [])) == [1, 2]

    def test_assign_meetings_group_not_found(self) -> None:
        self.set_models(
            {
                "group/1": {"name": "Test", "meeting_id": 1, "user_ids": [2]},
                "meeting/1": {
                    "name": "Find Test",
                    "group_ids": [1],
                    "is_active_in_organization_id": 1,
                    "committee_id": 2,
                },
                "user/2": {
                    "group_$_ids": ["1"],
                    "group_$1_ids": [1],
                    "meeting_ids": [1],
                },
                "committee/2": {"meeting_ids": [1]},
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1],
                "group_name": "Broken",
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Didn't find a group with groupname Broken in any meeting."
            in response.json["message"]
        )

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
