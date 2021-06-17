from typing import Any, Dict

from tests.system.action.base import BaseActionTestCase


class CommitteeCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: Dict[str, Dict[str, Any]] = {
            "organization/1": {"name": "test_organization1"},
            "user/20": {"username": "test_user20"},
            "user/21": {"username": "test_user21"},
            "user/22": {"username": "test_user22"},
            "organization_tag/12": {"organization_id": 1},
        }

    def test_create(self) -> None:
        self.set_models(self.test_models)
        self.set_models({"committee/1": {"organization_id": 1, "name": "c1"}})
        committee_name = "test_committee2"
        description = "<p>Test Committee</p>"

        response = self.request(
            "committee.create",
            {
                "name": committee_name,
                "organization_id": 1,
                "description": description,
                "user_ids": [20, 21],
                "organization_tag_ids": [12],
                "forward_to_committee_ids": [1],
                "receive_forwardings_from_committee_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("committee/2")
        assert model.get("name") == committee_name
        assert model.get("description") == description
        assert model.get("meeting_ids") is None
        assert model.get("user_ids") == [20, 21]
        assert model.get("organization_tag_ids") == [12]
        assert model.get("forward_to_committee_ids") == [1]
        assert model.get("receive_forwardings_from_committee_ids") == [1]
        self.assert_model_exists(
            "committee/1",
            {
                "forward_to_committee_ids": [2],
                "receive_forwardings_from_committee_ids": [2],
            },
        )

    def test_create_only_required(self) -> None:
        self.create_model("organization/1", {"name": "test_organization1"})
        committee_name = "test_committee1"

        response = self.request(
            "committee.create", {"name": committee_name, "organization_id": 1}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("committee/1")
        assert model.get("name") == committee_name

    def test_create_wrong_field(self) -> None:
        self.create_model("organization/1", {"name": "test_organization1"})

        response = self.request(
            "committee.create",
            {
                "name": "test_committee_name",
                "organization_id": 1,
                "wrong_field": "test",
            },
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )
        self.assert_model_not_exists("committee/1")

    def test_create_empty_data(self) -> None:
        response = self.request("committee.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['organization_id', 'name'] properties",
            response.json["message"],
        )
        self.assert_model_not_exists("committee/1")

    def test_create_empty_data_list(self) -> None:
        response = self.request_multi("committee.create", [])
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("committee/1")

    def test_not_existing_organization(self) -> None:
        response = self.request(
            "committee.create", {"organization_id": 1, "name": "test_name"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model 'organization/1' does not exist.",
            response.json["message"],
        )
        self.assert_model_not_exists("committee/1")

    def test_not_existing_user(self) -> None:
        self.create_model("organization/1", {"name": "test_organization1"})
        committee_name = "test_committee1"

        response = self.request(
            "committee.create",
            {
                "name": committee_name,
                "organization_id": 1,
                "user_ids": [20, 21],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn("does not exist", response.json["message"])
        self.assert_model_not_exists("committee/1")

    def test_create_both_forwarded_and_received_self_involved(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "name": "test_organization1",
                },
            }
        )
        response = self.request(
            "committee.create",
            {
                "name": "committee 1",
                "organization_id": 1,
                "forward_to_committee_ids": [1],
                "receive_forwardings_from_committee_ids": [],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Forwarding or receiving from own committee is not possible!",
            response.json["message"],
        )

    def test_no_permission(self) -> None:
        self.test_models["user/1"] = {
            "organization_management_level": "can_manage_users"
        }
        self.set_models(self.test_models)

        response = self.request(
            "committee.create",
            {
                "name": "test_committee",
                "organization_id": 1,
                "user_ids": [20, 21],
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "Missing OrganizationManagementLevel: can_manage_organization"
            in response.json["message"]
        )

    def test_permission(self) -> None:
        self.test_models["user/1"] = {
            "organization_management_level": "can_manage_organization"
        }
        self.set_models(self.test_models)

        response = self.request(
            "committee.create",
            {
                "name": "test_committee",
                "organization_id": 1,
                "user_ids": [20, 21],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("committee/1")
