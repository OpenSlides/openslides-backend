from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase

DEFAULT_PASSWORD = "password"


class AssignmentCandidateDeleteActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "name": "name_JhlFOAfK",
                "assignment_candidate_ids": [111],
                "is_active_in_organization_id": 1,
                "meeting_user_ids": [110],
            },
            "user/110": {
                "meeting_user_ids": [110],
                "is_active": True,
                "default_password": DEFAULT_PASSWORD,
                "password": self.auth.hash(DEFAULT_PASSWORD),
                "username": "user",
            },
            "assignment/111": {
                "title": "title_xTcEkItp",
                "meeting_id": 1,
                "candidate_ids": [111],
                "phase": "voting",
            },
            "assignment_candidate/111": {
                "meeting_user_id": 110,
                "assignment_id": 111,
                "meeting_id": 1,
            },
            "meeting_user/110": {
                "meeting_id": 1,
                "user_id": 110,
                "assignment_candidate_ids": [111],
            },
        }

    def test_delete_correct(self) -> None:
        self.set_models(
            {
                "meeting/1333": {
                    "name": "name_JhlFOAfK",
                    "assignment_candidate_ids": [111],
                    "is_active_in_organization_id": 1,
                },
                "user/110": {
                    "meeting_user_ids": [110],
                },
                "meeting_user/110": {
                    "meeting_id": 1333,
                    "user_id": 110,
                    "assignment_candidate_ids": [111],
                },
                "assignment/111": {
                    "title": "title_xTcEkItp",
                    "meeting_id": 1333,
                    "candidate_ids": [111],
                },
                "assignment_candidate/111": {
                    "meeting_user_id": 110,
                    "assignment_id": 111,
                    "meeting_id": 1333,
                },
            }
        )
        response = self.request("assignment_candidate.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("assignment_candidate/111")
        self.assert_history_information("assignment/111", ["Candidate removed"])

    def test_delete_correct_empty_user(self) -> None:
        self.set_models(
            {
                "meeting/1333": {
                    "name": "name_JhlFOAfK",
                    "assignment_candidate_ids": [111],
                    "is_active_in_organization_id": 1,
                },
                "assignment/111": {
                    "title": "title_xTcEkItp",
                    "meeting_id": 1333,
                    "candidate_ids": [111],
                },
                "assignment_candidate/111": {
                    "meeting_user_id": None,
                    "assignment_id": 111,
                    "meeting_id": 1333,
                },
            }
        )
        response = self.request("assignment_candidate.delete", {"id": 111})

        self.assert_status_code(response, 200)
        self.assert_model_deleted("assignment_candidate/111")

    def test_delete_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/1333": {
                    "name": "name_JhlFOAfK",
                    "assignment_candidate_ids": [112],
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [110],
                },
                "user/110": {
                    "meeting_user_ids": [110],
                },
                "meeting_user/110": {
                    "meeting_id": 1333,
                    "user_id": 110,
                    "assignment_candidate_ids": [112],
                },
                "assignment/111": {
                    "title": "title_xTcEkItp",
                    "meeting_id": 1333,
                    "candidate_ids": [111],
                },
                "assignment_candidate/112": {
                    "meeting_user_id": 110,
                    "assignment_id": 111,
                    "meeting_id": 1333,
                },
            }
        )

        response = self.request("assignment_candidate.delete", {"id": 111})
        self.assert_status_code(response, 400)
        assert "Model 'assignment_candidate/111' does not exist." in str(
            response.json["message"]
        )
        model = self.get_model("assignment_candidate/112")
        assert model.get("meeting_user_id") == 110
        assert model.get("assignment_id") == 111

    def test_delete_finished(self) -> None:
        self.set_models(
            {
                "meeting/1333": {
                    "name": "name_JhlFOAfK",
                    "assignment_candidate_ids": [111],
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [110],
                },
                "user/110": {
                    "meeting_user_ids": [110],
                },
                "meeting_user/110": {
                    "meeting_id": 1333,
                    "user_id": 110,
                    "assignment_candidate_ids": [111],
                },
                "assignment/111": {
                    "title": "title_xTcEkItp",
                    "meeting_id": 1333,
                    "candidate_ids": [111],
                    "phase": "finished",
                },
                "assignment_candidate/111": {
                    "meeting_user_id": 110,
                    "assignment_id": 111,
                    "meeting_id": 1333,
                },
            }
        )
        response = self.request("assignment_candidate.delete", {"id": 111})

        self.assert_status_code(response, 400)
        self.assert_model_exists("assignment_candidate/111")
        self.assertIn(
            "It is not permitted to remove a candidate from a finished assignment!",
            response.json["message"],
        )

    def test_delete_no_permission(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_models(self.permission_test_models)
        response = self.request("assignment_candidate.delete", {"id": 111})
        self.assert_status_code(response, 403)
        assert "Missing Permission: assignment.can_manage" in response.json["message"]

    def test_delete_both_permissions(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(
            3,
            [
                Permissions.Assignment.CAN_NOMINATE_OTHER,
                Permissions.Assignment.CAN_MANAGE,
            ],
        )
        self.set_models(self.permission_test_models)
        response = self.request("assignment_candidate.delete", {"id": 111})
        self.assert_status_code(response, 200)

    def test_delete_both_permissions_self(self) -> None:
        self.create_meeting()
        self.user_id = 110
        self.set_models(self.permission_test_models)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(
            3,
            [
                Permissions.Assignment.CAN_NOMINATE_SELF,
                Permissions.Assignment.CAN_MANAGE,
            ],
        )
        self.login(self.user_id)
        response = self.request("assignment_candidate.delete", {"id": 111})
        self.assert_status_code(response, 200)

    def test_delete_no_permissions_self(self) -> None:
        self.create_meeting()
        self.user_id = 110
        self.set_models(self.permission_test_models)
        self.set_user_groups(self.user_id, [3])
        self.login(self.user_id)
        response = self.request("assignment_candidate.delete", {"id": 111})
        self.assert_status_code(response, 403)
        assert "Missing Permission: assignment.can_manage" in response.json["message"]

    def test_delete_permission_no_voting(self) -> None:
        self.permission_test_models["assignment/111"]["phase"] = "search"
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(
            3,
            [
                Permissions.Assignment.CAN_NOMINATE_OTHER,
            ],
        )
        self.set_models(self.permission_test_models)
        response = self.request("assignment_candidate.delete", {"id": 111})
        self.assert_status_code(response, 200)
