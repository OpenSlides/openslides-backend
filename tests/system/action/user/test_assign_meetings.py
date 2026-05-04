from typing import Any

from tests.system.action.base import BaseActionTestCase


class UserAssignMeetings(BaseActionTestCase):
    def test_assign_meetings_correct(self) -> None:
        meetings_data: dict[int, dict[str, Any]] = {
            1: {"name": "success(existing)"},
            4: {"name": "nothing"},
            7: {"name": "success(added)", "committee_id": 63},
            10: {"name": "standard", "committee_id": 63},
            13: {"name": "success(added)", "committee_id": 63},
        }
        for id_, meeting_data in meetings_data.items():
            self.create_meeting(id_, meeting_data=meeting_data)
        self.set_models(
            {
                "group/1": {"name": "to_find", "meeting_user_ids": [1]},
                "group/4": {"name": "nothing", "meeting_user_ids": [2]},
                "group/7": {"name": "to_find", "meeting_id": 7},
                "group/10": {"name": "standard", "meeting_id": 10},
                "group/13": {"name": "to_find", "meeting_id": 13},
                "group/14": {"name": "nothing", "meeting_user_ids": [5]},
                "meeting_user/1": {"meeting_id": 1, "user_id": 1},
                "meeting_user/2": {"meeting_id": 4, "user_id": 1},
                "meeting_user/5": {"meeting_id": 13, "user_id": 1},
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
            "meeting_user/1", {"meeting_id": 1, "user_id": 1, "group_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/2", {"meeting_id": 4, "user_id": 1, "group_ids": [4]}
        )
        self.assert_model_exists(
            "meeting_user/5", {"meeting_id": 13, "user_id": 1, "group_ids": [13, 14]}
        )
        self.assert_model_exists(
            "meeting_user/6", {"meeting_id": 7, "user_id": 1, "group_ids": [7]}
        )
        self.assert_model_exists(
            "meeting_user/7", {"meeting_id": 10, "user_id": 1, "group_ids": [10]}
        )

    def test_assign_meetings_ignore_meetings_anonymous_group(self) -> None:
        """
        ...and don't ignore groups that are just named "Anonymous"
        """
        meetings_data: dict[int, dict[str, Any]] = {
            1: {"name": "success(existing)"},
            4: {"name": "nothing", "committee_id": 60},
            7: {
                "name": "success(added)",
                "committee_id": 60,
                "anonymous_group_id": 7,
                "default_group_id": 8,
            },
            10: {"name": "standard", "committee_id": 60},
            13: {
                "name": "success(added)",
                "committee_id": 60,
                "anonymous_group_id": 14,
            },
        }
        for id_, meeting_data in meetings_data.items():
            self.create_meeting(id_, meeting_data=meeting_data)
        self.set_models(
            {
                "group/1": {"name": "Anonymous", "meeting_user_ids": [1]},
                "group/4": {"name": "nothing", "meeting_user_ids": [2]},
                "group/7": {"name": "Anonymous"},
                "group/8": {"name": "standard"},
                "group/10": {"name": "standard"},
                "group/13": {"name": "Anonymous"},
                "group/14": {"name": "Anonymous"},
                "meeting_user/1": {"meeting_id": 1, "user_id": 1},
                "meeting_user/2": {"meeting_id": 4, "user_id": 1},
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
            "meeting_user/1", {"meeting_id": 1, "user_id": 1, "group_ids": [1]}
        )
        self.assert_model_exists(
            "meeting_user/2", {"meeting_id": 4, "user_id": 1, "group_ids": [4]}
        )
        self.assert_model_exists(
            "meeting_user/3", {"meeting_id": 13, "user_id": 1, "group_ids": [13]}
        )
        self.assert_model_exists(
            "meeting_user/4", {"meeting_id": 10, "user_id": 1, "group_ids": [10]}
        )
        self.assert_model_exists(
            "meeting_user/5", {"meeting_id": 7, "user_id": 1, "group_ids": [8]}
        )

    def test_assign_meetings_multiple_committees(self) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.set_models(
            {
                "group/1": {"name": "to_find"},
                "group/4": {"name": "to_find"},
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
        self.assert_model_exists("user/1", {"committee_ids": [60, 63]})

    def test_assign_meetings_with_existing_user_in_group(self) -> None:
        self.create_meeting(1, meeting_data={"name": "Find Test"})
        self.set_models(
            {
                "group/3": {"name": "Test", "meeting_user_ids": [2]},
                "user/2": {"username": "winnie"},
                "meeting_user/2": {"meeting_id": 1, "user_id": 2},
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
        self.assert_model_exists("user/2", {"meeting_ids": [1]})
        self.assert_model_exists("group/3", {"meeting_user_ids": [2, 3]})

    def test_assign_meetings_group_not_found(self) -> None:
        self.create_meeting()
        self.set_models({"user/2": {"username": "winnie"}})
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
        self.create_meeting()
        self.set_models(
            {
                "group/3": {"meeting_user_ids": [2]},
                "user/2": {"username": "winnie"},
                "meeting_user/2": {"meeting_id": 1, "user_id": 2},
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
        self.create_meeting(1, meeting_data={"name": "Find Test"})
        self.create_meeting(
            4, meeting_data={"name": "No Test and Not in Meeting", "committee_id": 60}
        )
        self.create_meeting(7, meeting_data={"name": "No Test and in Meeting"})
        self.set_models(
            {
                "group/3": {"name": "Test"},
                "user/1": {"organization_management_level": None},
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
        self.create_meeting(1, meeting_data={"name": "Find Test"})
        self.create_meeting(
            4, meeting_data={"name": "No Test and Not in Meeting", "committee_id": 60}
        )
        self.create_meeting(7, meeting_data={"name": "No Test and in Meeting"})
        self.set_models(
            {
                "committee/60": {"manager_ids": [1]},
                "group/3": {"name": "Test"},
                "user/1": {"organization_management_level": None},
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
        self.create_meeting(1, meeting_data={"name": "Find Test"})
        self.create_meeting(
            4, meeting_data={"name": "No Test and Not in Meeting", "committee_id": 60}
        )
        self.create_meeting(7, meeting_data={"name": "No Test and in Meeting"})
        self.set_models(
            {
                "committee/60": {"manager_ids": [1]},
                "committee/66": {"manager_ids": [1]},
                "group/3": {"name": "Test"},
                "user/1": {"organization_management_level": None},
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
        self.create_meeting(1, meeting_data={"name": "Find Test"})
        self.create_meeting(
            4, meeting_data={"name": "No Test and Not in Meeting", "committee_id": 60}
        )
        self.create_meeting(7, meeting_data={"name": "No Test and in Meeting"})
        self.set_models(
            {
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
        self.create_meeting(
            1, meeting_data={"name": "Archived", "is_active_in_organization_id": None}
        )
        self.create_meeting(
            4, meeting_data={"name": "No Test and Not in Meeting", "committee_id": 60}
        )
        self.create_meeting(
            7, meeting_data={"name": "No Test and in Meeting", "committee_id": 60}
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
        meetings_data: dict[int, dict[str, Any]] = {
            1: {"name": "success(existing)"},
            4: {"name": "nothing", "committee_id": 60, "locked_from_inside": True},
            7: {"name": "success(added)", "committee_id": 60},
            10: {"name": "standard", "committee_id": 60, "locked_from_inside": True},
            13: {"name": "success(added)", "committee_id": 60},
        }
        for id_, meeting_data in meetings_data.items():
            self.create_meeting(id_, meeting_data=meeting_data)
        self.set_models(
            {
                "group/1": {"name": "to_find", "meeting_user_ids": [1]},
                "group/4": {"name": "nothing", "meeting_user_ids": [2]},
                "group/7": {"name": "to_find"},
                "group/10": {"name": "standard"},
                "group/13": {"name": "to_find", "meeting_id": 13},
                "group/14": {"name": "nothing", "meeting_user_ids": [5]},
                "meeting_user/1": {"meeting_id": 1, "user_id": 1},
                "meeting_user/2": {"meeting_id": 4, "user_id": 1},
                "meeting_user/5": {"meeting_id": 13, "user_id": 1},
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
