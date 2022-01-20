from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from openslides_backend.permissions.permissions import Permissions

from .base import BasePresenterTestCase


class TestGetUserRelatedModels(BasePresenterTestCase):
    def test_get_user_related_models_simple(self) -> None:
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)
        assert data == {"1": {}}

    def test_get_user_related_models_committee(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "test"},
                "user/1": {
                    "committee_ids": [1],
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                    "committee_$can_manage_management_level": [1],
                },
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {"committees": [{"id": 1, "cml": "can_manage", "name": "test"}]}
        }

    def test_get_user_related_models_committee_more_user(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "test", "user_ids": [1, 2, 3]},
                "user/1": {
                    "committee_ids": [1],
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                    "committee_$can_manage_management_level": [1],
                },
                "user/2": {
                    "committee_ids": [1],
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                    "committee_$can_manage_management_level": [1],
                },
                "user/3": {
                    "committee_ids": [1],
                },
            }
        )
        status_code, data = self.request(
            "get_user_related_models", {"user_ids": [1, 2, 3]}
        )
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {"committees": [{"id": 1, "name": "test", "cml": "can_manage"}]},
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
                    "committee_ids": [1, 2, 3],
                    "committee_$_management_level": [
                        CommitteeManagementLevel.CAN_MANAGE
                    ],
                    "committee_$can_manage_management_level": [1, 2],
                },
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "committees": [
                    {"id": 1, "cml": "can_manage", "name": "test"},
                    {"id": 2, "cml": "can_manage", "name": "test2"},
                    {"id": 3, "cml": "", "name": "test3"},
                ]
            }
        }

    def test_get_user_related_models_meeting(self) -> None:
        self.set_models(
            {
                "user/1": {"meeting_ids": [1]},
                "meeting/1": {"name": "test", "is_active_in_organization_id": 1},
                "motion_submitter/2": {"user_id": 1, "meeting_id": 1},
                "assignment_candidate/3": {"user_id": 1, "meeting_id": 1},
                "speaker/4": {"user_id": 1, "meeting_id": 1},
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "meetings": [
                    {
                        "id": 1,
                        "name": "test",
                        "is_active_in_organization_id": 1,
                        "submitter_ids": [2],
                        "candidate_ids": [3],
                        "speaker_ids": [4],
                    }
                ]
            }
        }

    def test_get_user_related_models_meetings_more_user(self) -> None:
        self.set_models(
            {
                "user/1": {"meeting_ids": [1]},
                "user/2": {"meeting_ids": [1]},
                "meeting/1": {"name": "test", "is_active_in_organization_id": 1},
                "motion_submitter/2": {"user_id": 1, "meeting_id": 1},
                "motion_submitter/3": {"user_id": 2, "meeting_id": 1},
                "assignment_candidate/3": {"user_id": 1, "meeting_id": 1},
                "assignment_candidate/4": {"user_id": 2, "meeting_id": 1},
                "speaker/4": {"user_id": 1, "meeting_id": 1},
                "speaker/5": {"user_id": 2, "meeting_id": 1},
            }
        )
        status_code, data = self.request(
            "get_user_related_models", {"user_ids": [1, 2]}
        )
        self.assertEqual(status_code, 200)
        assert data == {
            "1": {
                "meetings": [
                    {
                        "id": 1,
                        "name": "test",
                        "is_active_in_organization_id": 1,
                        "submitter_ids": [2],
                        "candidate_ids": [3],
                        "speaker_ids": [4],
                    }
                ]
            },
            "2": {
                "meetings": [
                    {
                        "id": 1,
                        "name": "test",
                        "is_active_in_organization_id": 1,
                        "submitter_ids": [3],
                        "candidate_ids": [4],
                        "speaker_ids": [5],
                    }
                ]
            },
        }

    def test_get_user_related_models_missing_payload(self) -> None:
        status_code, data = self.request("get_user_related_models", {})
        self.assertEqual(status_code, 400)
        assert "data must contain ['user_ids'] properties" in data["message"]

    def test_get_user_related_models_no_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": None, "meeting_ids": [1]},
                "meeting/1": {"name": "test"},
                "motion_submitter/2": {"user_id": 1, "meeting_id": 1},
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 403)

    def test_get_user_related_models_permission_because_no_meeting_included(
        self,
    ) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": None, "meeting_ids": [1]},
                "meeting/1": {"name": "test"},
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)

    def test_get_user_related_models_permissions_user_can_manage(self) -> None:
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": None,
                    "meeting_ids": [1],
                    "group_$1_ids": [3],
                },
                "meeting/1": {"name": "test", "default_group_id": 3, "group_ids": [3]},
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
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                }
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 200)

    def test_get_user_related_models_no_committee_permissions(self) -> None:
        self.set_models(
            {
                "committee/1": {"name": "test"},
                "user/1": {
                    "organization_management_level": None,
                    "committee_ids": [1],
                    "committee_$_management_level": ["1"],
                    "committee_$1_management_level": None,
                },
            }
        )
        status_code, data = self.request("get_user_related_models", {"user_ids": [1]})
        self.assertEqual(status_code, 403)
