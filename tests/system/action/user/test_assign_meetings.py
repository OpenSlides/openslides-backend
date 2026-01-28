from tests.system.action.base import BaseActionTestCase


class UserAssignMeetings(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        for i in range(1, 14, 3):
            self.create_meeting(i)

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
                    "meeting_id": 4,
                    "meeting_user_ids": [2],
                },
                "group/31": {"name": "to_find", "meeting_id": 7},
                "group/43": {"name": "standard", "meeting_id": 10},
                "group/51": {"name": "to_find", "meeting_id": 13},
                "group/52": {
                    "name": "nothing",
                    "meeting_id": 13,
                    "meeting_user_ids": [5],
                },
                "meeting/1": {
                    "name": "success(existing)",
                    "group_ids": [11],
                    "meeting_user_ids": [1],
                },
                "meeting/4": {
                    "name": "nothing",
                    "group_ids": [22],
                    "committee_id": 66,
                    "meeting_user_ids": [2],
                },
                "meeting/7": {
                    "name": "success(added)",
                    "group_ids": [31],
                    "committee_id": 66,
                },
                "meeting/10": {
                    "name": "standard",
                    "group_ids": [43],
                    "default_group_id": 43,
                    "committee_id": 66,
                },
                "meeting/13": {
                    "name": "success(added)",
                    "group_ids": [51, 52],
                    "committee_id": 66,
                    "meeting_user_ids": [5],
                },
                "user/1": {
                    "meeting_user_ids": [1, 2, 5],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [11],
                },
                "meeting_user/2": {
                    "meeting_id": 4,
                    "user_id": 1,
                    "group_ids": [22],
                },
                "meeting_user/5": {
                    "meeting_id": 13,
                    "user_id": 1,
                    "group_ids": [52],
                },
                "committee/66": {"meeting_ids": [1, 4, 7, 10, 13]},
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1, 4, 7, 10, 13],
                "group_name": "to_find",
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["succeeded"] == [1, 13, 7]
        assert response.json["results"][0][0]["standard_group"] == [10]
        assert response.json["results"][0][0]["nothing"] == [4]
        self.assert_model_exists(
            "meeting_user/1", {"meeting_id": 1, "user_id": 1, "group_ids": [11]}
        )
        self.assert_model_exists(
            "meeting_user/2", {"meeting_id": 4, "user_id": 1, "group_ids": [22]}
        )
        self.assert_model_exists(
            "meeting_user/5", {"meeting_id": 13, "user_id": 1, "group_ids": [51, 52]}
        )
        self.assert_model_exists(
            "meeting_user/6", {"meeting_id": 7, "user_id": 1, "group_ids": [31]}
        )
        self.assert_model_exists(
            "meeting_user/7", {"meeting_id": 10, "user_id": 1, "group_ids": [43]}
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
                    "meeting_id": 4,
                    "meeting_user_ids": [2],
                },
                "group/31": {
                    "name": "Anonymous",
                    "meeting_id": 7,
                },
                "group/32": {
                    "name": "standard",
                    "meeting_id": 7,
                },
                "group/43": {"name": "standard", "meeting_id": 10},
                "group/51": {"name": "Anonymous", "meeting_id": 13},
                "group/52": {
                    "name": "Anonymous",
                    "meeting_id": 13,
                },
                "meeting/1": {
                    "name": "success(existing)",
                    "group_ids": [11],
                    "committee_id": 66,
                    "meeting_user_ids": [1],
                },
                "meeting/4": {
                    "name": "nothing",
                    "group_ids": [22],
                    "committee_id": 66,
                    "meeting_user_ids": [2],
                },
                "meeting/7": {
                    "name": "success(added)",
                    "group_ids": [30, 31],
                    "anonymous_group_id": 31,
                    "committee_id": 66,
                    "default_group_id": 32,
                },
                "meeting/10": {
                    "name": "standard",
                    "group_ids": [43],
                    "default_group_id": 43,
                    "committee_id": 66,
                },
                "meeting/13": {
                    "name": "success(added)",
                    "group_ids": [51, 52],
                    "anonymous_group_id": 52,
                    "committee_id": 66,
                },
                "user/1": {
                    "meeting_user_ids": [1, 2],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [11],
                },
                "meeting_user/2": {
                    "meeting_id": 4,
                    "user_id": 1,
                    "group_ids": [22],
                },
                "committee/66": {"meeting_ids": [1, 4, 7, 10, 13]},
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1, 4, 7, 10, 13],
                "group_name": "Anonymous",
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["succeeded"] == [1, 13]
        assert response.json["results"][0][0]["standard_group"] == [10, 7]
        assert response.json["results"][0][0]["nothing"] == [4]
        self.assert_model_exists(
            "meeting_user/1", {"meeting_id": 1, "user_id": 1, "group_ids": [11]}
        )
        self.assert_model_exists(
            "meeting_user/2", {"meeting_id": 4, "user_id": 1, "group_ids": [22]}
        )
        self.assert_model_exists(
            "meeting_user/3", {"meeting_id": 13, "user_id": 1, "group_ids": [51]}
        )
        self.assert_model_exists(
            "meeting_user/4", {"meeting_id": 10, "user_id": 1, "group_ids": [43]}
        )
        self.assert_model_exists(
            "meeting_user/5", {"meeting_id": 7, "user_id": 1, "group_ids": [32]}
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
                    "meeting_id": 4,
                },
                "meeting/1": {
                    "name": "m1",
                    "group_ids": [11],
                    "committee_id": 66,
                },
                "meeting/4": {
                    "name": "m2",
                    "group_ids": [22],
                    "committee_id": 69,
                },
                "committee/66": {"meeting_ids": [1]},
                "committee/69": {"meeting_ids": [4]},
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1, 4],
                "group_name": "to_find",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"committee_ids": [66, 69]})

    def test_assign_meetings_with_existing_user_in_group(self) -> None:
        self.set_models(
            {
                "group/3": {"name": "Test", "meeting_user_ids": [2]},
                "meeting/1": {
                    "name": "Find Test",
                },
                "user/2": {"meeting_user_ids": [2], "username": "winnie"},
                "meeting_user/2": {"meeting_id": 1, "user_id": 2, "group_ids": [3]},
            }
        )
        self.set_user_groups(2, [3])
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
        self.assert_model_exists("group/3", {"meeting_user_ids": [2, 3]})

    def test_assign_meetings_group_not_found(self) -> None:
        self.set_models(
            {
                "user/2": {"username": "winnie"},
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
                "group/3": {"meeting_user_ids": [2]},
                "user/2": {"username": "winnie"},
                "meeting_user/2": {"meeting_id": 1, "user_id": 2, "group_ids": [1]},
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
                "committee/60": {"meeting_ids": [1, 4]},
                "committee/66": {"meeting_ids": [7]},
                "group/3": {"name": "Test", "meeting_id": 1},
                "meeting/1": {
                    "name": "Find Test",
                },
                "meeting/4": {
                    "name": "No Test and Not in Meeting",
                    "committee_id": 60,
                },
                "meeting/7": {
                    "name": "No Test and in Meeting",
                    "committee_id": 66,
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
                "meeting_ids": [1, 4, 7],
                "group_name": "Test",
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action user.assign_meetings. Missing permission: CommitteeManagementLevel can_manage in committees {66, 60}"
            in response.json["message"]
        )

    def test_assign_meetings_some_permissions(self) -> None:
        self.set_models(
            {
                "committee/60": {"manager_ids": [1]},
                "group/3": {"name": "Test"},
                "meeting/1": {
                    "name": "Find Test",
                    "committee_id": 60,
                },
                "meeting/4": {
                    "name": "No Test and Not in Meeting",
                    "committee_id": 60,
                },
                "meeting/7": {
                    "name": "No Test and in Meeting",
                    "committee_id": 66,
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
                "meeting_ids": [1, 4, 7],
                "group_name": "Test",
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action user.assign_meetings. Missing permission: CommitteeManagementLevel can_manage in committee {66}"
            in response.json["message"]
        )

    def test_assign_meetings_all_cml_permissions(self) -> None:
        self.set_models(
            {
                "committee/60": {"manager_ids": [1]},
                "committee/66": {"manager_ids": [1]},
                "meeting/1": {
                    "name": "Find Test",
                },
                "meeting/4": {
                    "name": "No Test and Not in Meeting",
                    "committee_id": 60,
                },
                "meeting/7": {
                    "name": "No Test and in Meeting",
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
                "meeting_ids": [1, 4, 7],
                "group_name": "Test",
            },
        )
        self.assert_status_code(response, 200)

    def test_assign_meetings_oml_permission(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "Find Test",
                },
                "meeting/4": {
                    "name": "No Test and Not in Meeting",
                    "committee_id": 60,
                },
                "meeting/7": {
                    "name": "No Test and in Meeting",
                },
                "user/1": {
                    "organization_management_level": "can_manage_users",
                },
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1, 4, 7],
                "group_name": "Test",
            },
        )
        self.assert_status_code(response, 200)

    def test_assign_meetings_archived_meetings(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "Archived",
                    "is_active_in_organization_id": None,
                },
                "meeting/4": {
                    "name": "No Test and Not in Meeting",
                    "committee_id": 60,
                },
                "meeting/7": {
                    "name": "No Test and in Meeting",
                    "committee_id": 60,
                },
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1, 4, 7],
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
                    "meeting_id": 4,
                    "meeting_user_ids": [2],
                },
                "group/31": {"name": "to_find", "meeting_id": 7},
                "group/43": {"name": "standard", "meeting_id": 10},
                "group/51": {"name": "to_find", "meeting_id": 13},
                "group/52": {
                    "name": "nothing",
                    "meeting_id": 13,
                    "meeting_user_ids": [5],
                },
                "meeting/1": {
                    "name": "success(existing)",
                    "group_ids": [11],
                    "committee_id": 66,
                    "meeting_user_ids": [1],
                },
                "meeting/4": {
                    "name": "nothing",
                    "group_ids": [22],
                    "committee_id": 66,
                    "meeting_user_ids": [2],
                    "locked_from_inside": True,
                },
                "meeting/7": {
                    "name": "success(added)",
                    "group_ids": [31],
                    "committee_id": 66,
                    "locked_from_inside": False,
                },
                "meeting/10": {
                    "name": "standard",
                    "group_ids": [43],
                    "default_group_id": 43,
                    "committee_id": 66,
                    "locked_from_inside": True,
                },
                "meeting/13": {
                    "name": "success(added)",
                    "group_ids": [51, 52],
                    "committee_id": 66,
                    "meeting_user_ids": [5],
                },
                "user/1": {
                    "meeting_user_ids": [1, 2, 5],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [11],
                },
                "meeting_user/2": {
                    "meeting_id": 4,
                    "user_id": 1,
                    "group_ids": [22],
                },
                "meeting_user/5": {
                    "meeting_id": 13,
                    "user_id": 1,
                    "group_ids": [52],
                },
                "committee/66": {"meeting_ids": [1, 4, 7, 10, 13]},
            }
        )
        response = self.request(
            "user.assign_meetings",
            {
                "id": 1,
                "meeting_ids": [1, 4, 7, 10, 13],
                "group_name": "to_find",
            },
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Cannot assign meetings because some selected meetings are locked: 4, 10."
        )
