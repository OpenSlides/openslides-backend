from typing import cast

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions

from .base import BasePresenterTestCase


class TestGetUserRelatedModels(BasePresenterTestCase):
    def create_assignment(self, base: int, meeting_id: int) -> None:
        self.set_models(
            {
                f"assignment/{base}": {
                    "title": "just do it",
                    "meeting_id": meeting_id,
                },
                f"list_of_speakers/{base + 100}": {
                    "content_object_id": f"assignment/{base}",
                    "meeting_id": meeting_id,
                },
            }
        )

    def get_models_for_meeting_users(
        self, meeting_user_to_meetings_ids: dict[int, int]
    ) -> dict[str, dict[str, int]]:
        return {
            fqid: model_data
            for meeting_user_id, meeting_id in meeting_user_to_meetings_ids.items()
            for fqid, model_data in {
                f"motion_submitter/{meeting_user_id + 1}": {
                    "meeting_user_id": meeting_user_id,
                    "meeting_id": meeting_id,
                    "motion_id": meeting_id,
                },
                f"assignment_candidate/{meeting_user_id + 2}": {
                    "meeting_user_id": meeting_user_id,
                    "meeting_id": meeting_id,
                    "assignment_id": meeting_id,
                },
                f"speaker/{meeting_user_id + 3}": {
                    "meeting_user_id": meeting_user_id,
                    "meeting_id": meeting_id,
                    "list_of_speakers_id": meeting_id,
                },
            }.items()
        }

    def test_get_user_related_models_simple(self) -> None:
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
            }
        }

    def test_get_user_related_models_committee(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "test", "manager_ids": [1]},
                "user/1": {"username": "na"},
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "committees": [{"id": 1, "cml": "can_manage", "name": "test"}],
            }
        }

    def test_get_user_related_models_committee_more_users(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "committee/1": {"name": "test", "manager_ids": [1, 2]},
                "user/1": {"username": "na"},
                "user/2": {"username": "na"},
                "user/3": {"username": "na", "home_committee_id": 1},
            }
        )
        status_code, data = self.request(
            "get_user_related_models", {"user_ids": [1, 2, 3]}
        )
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "committees": [{"id": 1, "name": "test", "cml": "can_manage"}],
            },
            "2": {"committees": [{"id": 1, "name": "test", "cml": "can_manage"}]},
            "3": {"committees": [{"id": 1, "name": "test", "cml": ""}]},
        }

    def test_get_user_related_models_committee_more_committees(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "test", "manager_ids": [1]},
                "committee/2": {"name": "test2", "manager_ids": [1]},
                "committee/3": {"name": "test3"},
                "user/1": {"username": "na", "home_committee_id": 3},
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "committees": [
                    {"id": 1, "cml": "can_manage", "name": "test"},
                    {"id": 2, "cml": "can_manage", "name": "test2"},
                    {"id": 3, "cml": "", "name": "test3"},
                ],
            }
        }

    def test_get_user_related_models_meeting(self) -> None:
        self.create_meeting()
        self.create_motion(1, 1)
        self.create_assignment(1, 1)
        self.set_models(
            {
                "meeting_user/1": {"meeting_id": 1, "user_id": 1, "locked_out": True},
                "group/1": {"meeting_user_ids": [1]},
                **self.get_models_for_meeting_users({1: 1}),
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "committees": [
                    {
                        "cml": "",
                        "id": 60,
                        "name": "Committee60",
                    },
                ],
                "meetings": [
                    {
                        "id": 1,
                        "name": "OpenSlides",
                        "is_active_in_organization_id": 1,
                        "is_locked": False,
                        "motion_submitter_ids": [2],
                        "assignment_candidate_ids": [3],
                        "speaker_ids": [4],
                        "locked_out": True,
                    }
                ],
            }
        }

    def test_two_meetings(self) -> None:
        logged_in_user_id = 2
        regular_user_id = 111
        additional_admin_id = 777
        self.set_models(
            {
                f"user/{logged_in_user_id}": {
                    "username": "executor",
                    "default_password": "DEFAULT_PASSWORD",
                    "password": self.auth.hash("DEFAULT_PASSWORD"),
                    "is_active": True,
                },
                f"user/{regular_user_id}": {"username": "untouchable"},
            }
        )
        self.create_meeting_for_two_users(1, logged_in_user_id, regular_user_id)
        self.create_meeting_for_two_users(4, logged_in_user_id, regular_user_id)
        self.set_models(
            {
                f"user/{additional_admin_id}": {"username": "additional_admin"},
                "meeting_user/666": {"meeting_id": 1, "user_id": additional_admin_id},
            }
        )
        self.login(logged_in_user_id)
        # Admin groups of meeting/1 for requesting user meeting/2 as normal user
        # 111 into both meetings
        # 777 additional admin for meeting/2 doesn't affect outcome
        self.move_users_to_groups(
            {
                logged_in_user_id: [2, 4],
                regular_user_id: [1, 4],
                additional_admin_id: [5],
            }
        )
        status_code, data = self.request(
            "get_user_related_models",
            {"user_ids": [regular_user_id, additional_admin_id]},
        )
        self.assertEqual(status_code, 403)
        self.assertEqual(
            "Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 4",
            data["message"],
        )
        # Admin groups of meeting/1 for requesting user
        # 111 into both meetings
        self.move_users_to_groups({logged_in_user_id: [2]})
        status_code, data = self.request(
            "get_user_related_models", {"user_ids": [regular_user_id]}
        )
        self.assertEqual(status_code, 403)
        self.assertEqual(
            "Missing permissions: OrganizationManagementLevel can_manage_users in organization 1 or Permission user.can_update in meeting 4",
            data["message"],
        )
        # Admin groups of meeting/1 and meeting/4 for requesting user
        # 111 into both meetings
        self.move_users_to_groups({logged_in_user_id: [2, 5]})
        status_code, data = self.request(
            "get_user_related_models", {"user_ids": [regular_user_id]}
        )
        self.assertEqual(status_code, 200)
        assert data == {
            "111": {
                "committees": [
                    {
                        "cml": "",
                        "id": 60,
                        "name": "Committee60",
                    },
                    {
                        "cml": "",
                        "id": 63,
                        "name": "Committee63",
                    },
                ],
                "meetings": [
                    {
                        "id": 1,
                        "name": "OpenSlides",
                        "is_active_in_organization_id": 1,
                        "is_locked": False,
                    },
                    {
                        "id": 4,
                        "name": "OpenSlides",
                        "is_active_in_organization_id": 1,
                        "is_locked": False,
                    },
                ],
            },
        }

    def test_get_user_related_models_meetings_more_users(self) -> None:
        self.create_meeting()
        self.set_user_groups(1, [1])
        self.create_user_for_meeting(1)
        self.create_motion(1, 1)
        self.create_assignment(1, 1)
        self.set_models(self.get_models_for_meeting_users({1: 1, 2: 1}))
        status_code, data = self.request(
            "get_user_related_models", {"user_ids": [1, 2]}
        )
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "committees": [
                    {
                        "cml": "",
                        "id": 60,
                        "name": "Committee60",
                    },
                ],
                "meetings": [
                    {
                        "id": 1,
                        "name": "OpenSlides",
                        "is_active_in_organization_id": 1,
                        "is_locked": False,
                        "motion_submitter_ids": [2],
                        "assignment_candidate_ids": [3],
                        "speaker_ids": [4],
                    }
                ],
            },
            "2": {
                "committees": [
                    {
                        "cml": "",
                        "id": 60,
                        "name": "Committee60",
                    },
                ],
                "meetings": [
                    {
                        "id": 1,
                        "name": "OpenSlides",
                        "is_active_in_organization_id": 1,
                        "is_locked": False,
                        "motion_submitter_ids": [3],
                        "assignment_candidate_ids": [4],
                        "speaker_ids": [5],
                    }
                ],
            },
        }

    def test_get_user_related_models_meetings_more_users_ignore_one_meeting_user(
        self,
    ) -> None:
        self.create_meeting()
        self.set_user_groups(1, [1])
        self.create_user_for_meeting(1)
        self.create_motion(1, 1)
        self.create_assignment(1, 1)
        self.set_models(self.get_models_for_meeting_users({1: 1, 2: 1}))
        self.set_user_groups(2, [])
        status_code, data = self.request(
            "get_user_related_models", {"user_ids": [1, 2]}
        )
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "committees": [
                    {
                        "cml": "",
                        "id": 60,
                        "name": "Committee60",
                    },
                ],
                "meetings": [
                    {
                        "id": 1,
                        "name": "OpenSlides",
                        "is_active_in_organization_id": 1,
                        "is_locked": False,
                        "motion_submitter_ids": [2],
                        "assignment_candidate_ids": [3],
                        "speaker_ids": [4],
                    }
                ],
            },
            "2": {},
        }

    def test_get_user_related_models_missing_payload(self) -> None:
        status_code, data = self.request("get_user_related_models", {})
        self.assertEqual(status_code, 400)
        assert "data must contain ['user_ids'] properties" in data["message"]

    def test_get_user_related_models_no_permissions(self) -> None:
        self.create_meeting()
        self.create_motion(1, 1)
        self.set_organization_management_level(None)
        self.set_user_groups(1, [1])
        self.set_models(
            {
                "motion_submitter/2": {
                    "meeting_user_id": 1,
                    "meeting_id": 1,
                    "motion_id": 1,
                }
            }
        )
        status_code, _ = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 403)

    def test_get_user_related_models_empty_meeting(
        self,
    ) -> None:
        self.create_meeting()
        self.create_user_for_meeting(1)
        status_code, data = self.request("get_user_related_models", {"user_ids": [2]})
        self.assertEqual(status_code, 200)
        assert data == {
            "2": {
                "committees": [
                    {
                        "cml": "",
                        "id": 60,
                        "name": "Committee60",
                    },
                ],
                "meetings": [
                    {
                        "id": 1,
                        "name": "OpenSlides",
                        "is_active_in_organization_id": 1,
                        "is_locked": False,
                    }
                ],
            },
        }

    def test_get_user_related_models_meeting_but_no_groups(
        self,
    ) -> None:
        self.create_meeting()
        self.set_models(
            {
                "user/2": {"username": "na"},
                "meeting_user/1": {"meeting_id": 1, "user_id": 2},
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [2]})
        self.assertEqual(status_code, 200)
        assert data == {
            "2": {},
        }

    def test_get_user_related_models_archived_meeting(
        self,
    ) -> None:
        self.create_meeting(
            meeting_data={
                "is_active_in_organization_id": None,
                "is_archived_in_organization_id": 1,
            }
        )
        self.create_user_for_meeting(1)
        status_code, data = self.request("get_user_related_models", {"user_ids": [2]})
        self.assertEqual(status_code, 200)
        assert data == {
            "2": {
                "committees": [
                    {
                        "cml": "",
                        "id": 60,
                        "name": "Committee60",
                    },
                ],
                "meetings": [
                    {
                        "id": 1,
                        "name": "OpenSlides",
                        "is_active_in_organization_id": None,
                        "is_locked": False,
                    }
                ],
            },
        }

    def test_get_user_related_models_permissions_user_can_manage(self) -> None:
        self.create_meeting()
        self.set_organization_management_level(None)
        self.set_user_groups(1, [3])
        self.set_group_permissions(3, [Permissions.User.CAN_MANAGE])
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)

    def test_get_user_related_models_permissions(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)
        self.assertEqual(
            data,
            {
                "1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                }
            },
        )

    def test_get_user_related_models_no_committee_permissions(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "test"},
                "user/1": {
                    "username": "na",
                    "organization_management_level": None,
                    "home_committee_id": 1,
                },
            }
        )
        status_code, _ = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 403)

    def test_get_user_related_models_no_permissions_higher_oml(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                },
                "user/2": {
                    "username": "na",
                    "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                },
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [2]})
        self.assertEqual(status_code, 403)
        assert (
            data["message"]
            == "Missing permission: OrganizationManagementLevel superadmin in organization 1"
        )

    def test_get_user_related_models_with_locked_meetings(self) -> None:
        self.create_user("user2")
        models = cast(
            dict[str, dict[str, int | list[int]]],
            (self.get_models_for_meeting_users({12: 1, 42: 4})),
        )
        for meeting_id in range(1, 8, 3):
            self.create_meeting(
                meeting_id, meeting_data={"locked_from_inside": meeting_id != 1}
            )
            self.create_motion(meeting_id, meeting_id)
            self.create_assignment(meeting_id, meeting_id)
            mu_id = int(f"{meeting_id}2")
            models[f"meeting_user/{mu_id}"] = {"user_id": 2, "meeting_id": meeting_id}
            models[f"group/{meeting_id}"] = {"meeting_user_ids": [mu_id]}
        self.set_models(models)
        self.set_user_groups(1, [4])

        status_code, data = self.request("get_user_related_models", {"user_ids": [2]})
        self.assertEqual(status_code, 200)
        assert data == {
            "2": {
                "committees": [
                    {
                        "cml": "",
                        "id": 60,
                        "name": "Committee60",
                    },
                    {
                        "cml": "",
                        "id": 63,
                        "name": "Committee63",
                    },
                    {
                        "cml": "",
                        "id": 66,
                        "name": "Committee66",
                    },
                ],
                "meetings": [
                    {
                        "id": 1,
                        "name": "OpenSlides",
                        "is_active_in_organization_id": 1,
                        "is_locked": False,
                        "motion_submitter_ids": [13],
                        "assignment_candidate_ids": [14],
                        "speaker_ids": [15],
                    },
                    {
                        "id": 4,
                        "name": "OpenSlides",
                        "is_active_in_organization_id": 1,
                        "is_locked": True,
                        "motion_submitter_ids": [43],
                        "assignment_candidate_ids": [44],
                        "speaker_ids": [45],
                    },
                    {
                        "id": 7,
                        "name": "OpenSlides",
                        "is_active_in_organization_id": 1,
                        "is_locked": True,
                    },
                ],
            },
        }
