from typing import Any

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase
from tests.system.util import CountDatastoreCalls

DEFAULT_PASSWORD = "password"


class AssignmentCandidateCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: dict[str, dict[str, Any]] = {
            "user/110": {
                "username": "test_Xcdfgee",
                "is_active": True,
                "default_password": DEFAULT_PASSWORD,
                "password": self.auth.hash(DEFAULT_PASSWORD),
                "meeting_user_ids": [110],
            },
            "meeting_user/110": {
                "meeting_id": 1,
                "user_id": 110,
            },
            "assignment/111": {
                "title": "title_xTcEkItp",
                "meeting_id": 1,
                "phase": "voting",
            },
        }

    def test_create(self) -> None:
        self.set_models(
            {
                "meeting/1333": {
                    "name": "name_JhlFOAfK",
                    "is_active_in_organization_id": 1,
                },
                "user/110": {"username": "test_Xcdfgee"},
                "meeting_user/110": {
                    "meeting_id": 1133,
                    "user_id": 110,
                },
                "assignment/111": {"title": "title_xTcEkItp", "meeting_id": 1333},
            }
        )
        with CountDatastoreCalls() as counter:
            response = self.request(
                "assignment_candidate.create",
                {"assignment_id": 111, "meeting_user_id": 110},
            )
        self.assert_status_code(response, 200)
        assert counter.calls == 6
        model = self.get_model("assignment_candidate/1")
        assert model.get("meeting_user_id") == 110
        assert model.get("assignment_id") == 111
        assert model.get("weight") == 10000
        self.assert_history_information("assignment/111", ["Candidate added"])

    def test_create_empty_data(self) -> None:
        response = self.request("assignment_candidate.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['assignment_id', 'meeting_user_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.set_models(
            {
                "user/110": {"username": "test_Xcdfgee"},
                "assignment/111": {"title": "title_xTcEkItp"},
                "meeting_user/110": {
                    "meeting_id": 1133,
                    "user_id": 110,
                },
            }
        )
        response = self.request(
            "assignment_candidate.create",
            {
                "wrong_field": "text_AefohteiF8",
                "assignment_id": 111,
                "meeting_user_id": 110,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_finished(self) -> None:
        self.set_models(
            {
                "meeting/1333": {
                    "name": "name_JhlFOAfK",
                    "is_active_in_organization_id": 1,
                },
                "user/110": {"username": "test_Xcdfgee"},
                "meeting_user/110": {
                    "meeting_id": 1133,
                    "user_id": 110,
                },
                "assignment/111": {
                    "title": "title_xTcEkItp",
                    "meeting_id": 1333,
                    "phase": "finished",
                },
            }
        )
        response = self.request(
            "assignment_candidate.create",
            {"assignment_id": 111, "meeting_user_id": 110},
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "It is not permitted to add a candidate to a finished assignment!",
            response.json["message"],
        )

    def test_create_no_permission(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_models(self.permission_test_models)
        response = self.request(
            "assignment_candidate.create",
            {"assignment_id": 111, "meeting_user_id": 110},
        )
        self.assert_status_code(response, 403)
        assert "Missing Permission: assignment.can_manage" in response.json["message"]

    def test_create_both_permissions(self) -> None:
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
        response = self.request(
            "assignment_candidate.create",
            {"assignment_id": 111, "meeting_user_id": 110},
        )
        self.assert_status_code(response, 200)

    def test_create_both_permissions_self(self) -> None:
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
        response = self.request(
            "assignment_candidate.create",
            {"assignment_id": 111, "meeting_user_id": 110},
        )
        self.assert_status_code(response, 200)

    def test_create_no_permissions_self(self) -> None:
        self.create_meeting()
        self.user_id = 110
        self.set_models(self.permission_test_models)
        self.set_user_groups(self.user_id, [3])
        self.login(self.user_id)
        response = self.request(
            "assignment_candidate.create",
            {"assignment_id": 111, "meeting_user_id": 110},
        )
        self.assert_status_code(response, 403)
        assert "Missing Permission: assignment.can_manage" in response.json["message"]

    def test_create_permissions_no_voting_self(self) -> None:
        self.permission_test_models["assignment/111"]["phase"] = "search"
        self.create_meeting()
        self.user_id = 110
        self.set_models(self.permission_test_models)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(
            3,
            [
                Permissions.Assignment.CAN_NOMINATE_SELF,
            ],
        )
        self.login(self.user_id)
        response = self.request(
            "assignment_candidate.create",
            {"assignment_id": 111, "meeting_user_id": 110},
        )
        self.assert_status_code(response, 200)
