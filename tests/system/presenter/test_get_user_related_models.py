from typing import Any, cast

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions

from .base import BasePresenterTestCase


class TestGetUserRelatedModels(BasePresenterTestCase):
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
                "committee/1": {"name": "test"},
                "user/1": {
                    "username": "na",
                    "committee_ids": [1],
                    "committee_management_ids": [1],
                },
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

    def test_get_user_related_models_committee_more_user(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "test", "user_ids": [1, 2, 3]},
                "user/1": {
                    "username": "na",
                    "committee_ids": [1],
                    "committee_management_ids": [1],
                },
                "user/2": {
                    "username": "na",
                    "committee_ids": [1],
                    "committee_management_ids": [1],
                },
                "user/3": {
                    "username": "na",
                    "committee_ids": [1],
                },
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
                "committee/1": {"name": "test", "user_ids": [1]},
                "committee/2": {"name": "test2", "user_ids": [1]},
                "committee/3": {"name": "test3", "user_ids": [1]},
                "user/1": {
                    "username": "na",
                    "committee_ids": [1, 2, 3],
                    "committee_management_ids": [1, 2],
                },
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
        self.set_models(
            {
                "user/1": {
                    "username": "na",
                    "meeting_ids": [1],
                    "meeting_user_ids": [1],
                },
                "committee/1": {"name": "ha", "meeting_ids": [1]},
                "meeting/1": {
                    "name": "test",
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [1],
                    "committee_id": 1,
                    "group_ids": [1],
                },
                "motion_submitter/2": {"meeting_user_id": 1, "meeting_id": 1},
                "assignment_candidate/3": {"meeting_user_id": 1, "meeting_id": 1},
                "speaker/4": {"meeting_user_id": 1, "meeting_id": 1},
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "speaker_ids": [4],
                    "motion_submitter_ids": [2],
                    "assignment_candidate_ids": [3],
                    "group_ids": [1],
                    "locked_out": True,
                },
                "group/1": {"meeting_user_ids": [1], "meeting_id": 1},
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "meetings": [
                    {
                        "id": 1,
                        "name": "test",
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

    def test_get_user_related_models_meetings_more_users(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "na",
                    "meeting_ids": [1],
                    "meeting_user_ids": [1],
                },
                "user/2": {
                    "username": "na",
                    "meeting_ids": [1],
                    "meeting_user_ids": [2],
                },
                "committee/1": {"name": "ha", "meeting_ids": [1]},
                "meeting/1": {
                    "name": "test",
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                    "group_ids": [1],
                },
                "motion_submitter/2": {"meeting_user_id": 1, "meeting_id": 1},
                "motion_submitter/3": {"meeting_user_id": 2, "meeting_id": 1},
                "assignment_candidate/3": {"meeting_user_id": 1, "meeting_id": 1},
                "assignment_candidate/4": {"meeting_user_id": 2, "meeting_id": 1},
                "speaker/4": {"meeting_user_id": 1, "meeting_id": 1},
                "speaker/5": {"meeting_user_id": 2, "meeting_id": 1},
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "speaker_ids": [4],
                    "motion_submitter_ids": [2],
                    "assignment_candidate_ids": [3],
                    "group_ids": [1],
                },
                "meeting_user/2": {
                    "meeting_id": 1,
                    "user_id": 2,
                    "speaker_ids": [5],
                    "motion_submitter_ids": [3],
                    "assignment_candidate_ids": [4],
                    "group_ids": [1],
                },
                "group/1": {"meeting_id": 1, "meeting_user_ids": [1, 2]},
            }
        )
        status_code, data = self.request(
            "get_user_related_models", {"user_ids": [1, 2]}
        )
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "meetings": [
                    {
                        "id": 1,
                        "name": "test",
                        "is_active_in_organization_id": 1,
                        "is_locked": False,
                        "motion_submitter_ids": [2],
                        "assignment_candidate_ids": [3],
                        "speaker_ids": [4],
                    }
                ],
            },
            "2": {
                "meetings": [
                    {
                        "id": 1,
                        "name": "test",
                        "is_active_in_organization_id": 1,
                        "is_locked": False,
                        "motion_submitter_ids": [3],
                        "assignment_candidate_ids": [4],
                        "speaker_ids": [5],
                    }
                ]
            },
        }

    def test_get_user_related_models_meetings_more_users_ignore_one_meeting_user(
        self,
    ) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "na",
                    "meeting_ids": [1],
                    "meeting_user_ids": [1],
                },
                "user/2": {
                    "username": "na",
                    "meeting_ids": [1],
                    "meeting_user_ids": [2],
                },
                "committee/1": {"name": "ha", "meeting_ids": [1]},
                "meeting/1": {
                    "name": "test",
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                    "group_ids": [1],
                },
                "motion_submitter/2": {"meeting_user_id": 1, "meeting_id": 1},
                "motion_submitter/3": {"meeting_user_id": 2, "meeting_id": 1},
                "assignment_candidate/3": {"meeting_user_id": 1, "meeting_id": 1},
                "assignment_candidate/4": {"meeting_user_id": 2, "meeting_id": 1},
                "speaker/4": {"meeting_user_id": 1, "meeting_id": 1},
                "speaker/5": {"meeting_user_id": 2, "meeting_id": 1},
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "speaker_ids": [4],
                    "motion_submitter_ids": [2],
                    "assignment_candidate_ids": [3],
                    "group_ids": [1],
                },
                "meeting_user/2": {
                    "meeting_id": 1,
                    "user_id": 2,
                    "speaker_ids": [5],
                    "motion_submitter_ids": [3],
                    "assignment_candidate_ids": [4],
                },
                "group/1": {"meeting_id": 1, "meeting_user_ids": [1]},
            }
        )
        status_code, data = self.request(
            "get_user_related_models", {"user_ids": [1, 2]}
        )
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "meetings": [
                    {
                        "id": 1,
                        "name": "test",
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
        self.set_models(
            {
                "user/1": {
                    "username": "na",
                    "organization_management_level": None,
                    "meeting_ids": [1],
                },
                "committee/1": {"name": "ha", "meeting_ids": [1]},
                "meeting/1": {
                    "name": "test",
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "motion_submitter/2": {"meeting_user_id": 1, "meeting_id": 1},
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "motion_submitter_ids": [2],
                },
            }
        )
        status_code, _ = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 403)

    def test_get_user_related_models_empty_meeting(
        self,
    ) -> None:
        self.set_models(
            {
                "user/2": {"username": "na", "meeting_user_ids": [1]},
                "committee/1": {"name": "ha", "meeting_ids": [1]},
                "meeting/1": {
                    "name": "test",
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                    "meeting_user_ids": [1],
                    "group_ids": [1],
                },
                "meeting_user/1": {"meeting_id": 1, "user_id": 2, "group_ids": [1]},
                "group/1": {"meeting_user_ids": [1], "meeting_id": 1},
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [2]})
        self.assertEqual(status_code, 200)
        assert data == {
            "2": {
                "meetings": [
                    {
                        "id": 1,
                        "name": "test",
                        "is_active_in_organization_id": 1,
                        "is_locked": False,
                    }
                ]
            },
        }

    def test_get_user_related_models_meeting_but_no_groups(
        self,
    ) -> None:
        self.set_models(
            {
                "user/2": {"username": "na", "meeting_user_ids": [1]},
                "committee/1": {"name": "ha", "meeting_ids": [1]},
                "meeting/1": {
                    "name": "test",
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                    "meeting_user_ids": [1],
                },
                "meeting_user/1": {"meeting_id": 1, "user_id": 2, "group_ids": []},
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
        self.set_models(
            {
                "user/2": {"username": "na", "meeting_user_ids": [1]},
                "committee/1": {"name": "ha", "meeting_ids": [1]},
                "meeting/1": {
                    "name": "test",
                    "is_archived_in_organization_id": 1,
                    "committee_id": 1,
                    "meeting_user_ids": [1],
                    "group_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 2,
                    "group_ids": [1],
                },
                "group/1": {"meeting_id": 1, "meeting_user_ids": [1]},
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [2]})
        self.assertEqual(status_code, 200)
        assert data == {
            "2": {
                "meetings": [
                    {
                        "id": 1,
                        "name": "test",
                        "is_active_in_organization_id": None,
                        "is_locked": False,
                    }
                ]
            },
        }

    def test_get_user_related_models_permissions_user_can_manage(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "na",
                    "organization_management_level": None,
                    "meeting_ids": [1],
                    "meeting_user_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [3],
                },
                "committee/1": {"name": "ha", "meeting_ids": [1]},
                "meeting/1": {
                    "name": "test",
                    "default_group_id": 3,
                    "group_ids": [3],
                    "is_active_in_organization_id": 1,
                    "committee_id": 1,
                },
                "group/3": {
                    "meeting_id": 1,
                    "default_group_for_meeting_id": 1,
                    "permissions": [Permissions.User.CAN_MANAGE],
                },
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)

    def test_get_user_related_models_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "na",
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                }
            }
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
                    "committee_ids": [1],
                    "committee_management_ids": [],
                },
            }
        )
        status_code, _ = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 403)

    def test_get_user_related_models_missing_committee(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "test", "user_ids": [1]},
                "committee/2": {"name": "test2", "user_ids": [1]},
                "committee/3": {"name": "test3", "user_ids": [1]},
                "user/1": {
                    "username": "na",
                    "committee_ids": [1],
                    "committee_management_ids": [1, 2],
                },
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 400)
        assert (
            data["message"]
            == "Data error: user has rights for committee 2, but faultily is no member of committee."
        )

    def test_get_user_related_models_no_permissions_higher_oml(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "username": "na",
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
        self.set_models(
            {
                "user/1": {"username": "na", "meeting_ids": [2]},
                "user/2": {
                    "username": "na",
                    "meeting_ids": [1, 2, 3],
                    "meeting_user_ids": [1, 2, 3],
                },
                "committee/1": {"name": "ha", "meeting_ids": [1, 2, 3]},
                **{
                    key: cast(dict[str, Any], value)
                    for id_ in [1, 2, 3]
                    for key, value in {
                        f"meeting/{id_}": {
                            "name": f"test{id_}",
                            "is_active_in_organization_id": 1,
                            "committee_id": id_,
                            "group_ids": [id_],
                            "locked_from_inside": id_ != 1,
                        },
                        f"motion_submitter/{id_}": {
                            "meeting_user_id": id_,
                            "meeting_id": id_,
                        },
                        f"assignment_candidate/{id_}": {
                            "meeting_user_id": id_,
                            "meeting_id": id_,
                        },
                        f"speaker/{id_}": {"meeting_user_id": id_, "meeting_id": id_},
                        f"meeting_user/{id_}": {
                            "meeting_id": id_,
                            "user_id": 2,
                            "speaker_ids": [id_],
                            "motion_submitter_ids": [id_],
                            "assignment_candidate_ids": [id_],
                            "group_ids": [id_],
                            "locked_out": id_ == 3,
                        },
                        f"group/{id_}": {"meeting_id": id_, "meeting_user_ids": [id_]},
                    }.items()
                },
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [2]})
        self.assertEqual(status_code, 200)
        assert data == {
            "2": {
                "meetings": [
                    {
                        "id": 1,
                        "name": "test1",
                        "is_active_in_organization_id": 1,
                        "is_locked": False,
                        "motion_submitter_ids": [1],
                        "assignment_candidate_ids": [1],
                        "speaker_ids": [1],
                    },
                    {
                        "id": 2,
                        "name": "test2",
                        "is_active_in_organization_id": 1,
                        "is_locked": True,
                        "motion_submitter_ids": [2],
                        "assignment_candidate_ids": [2],
                        "speaker_ids": [2],
                    },
                    {
                        "id": 3,
                        "name": "test3",
                        "is_active_in_organization_id": 1,
                        "is_locked": True,
                    },
                ]
            },
        }
