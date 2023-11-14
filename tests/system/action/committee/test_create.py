from typing import Any, Dict

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class CommitteeCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: Dict[str, Dict[str, Any]] = {
            ONE_ORGANIZATION_FQID: {"name": "test_organization1"},
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
        external_id = "external"

        response = self.request(
            "committee.create",
            {
                "name": committee_name,
                "organization_id": 1,
                "description": description,
                "organization_tag_ids": [12],
                "forward_to_committee_ids": [1],
                "receive_forwardings_from_committee_ids": [1],
                "external_id": external_id,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("committee/2")
        assert model.get("name") == committee_name
        assert model.get("description") == description
        assert model.get("meeting_ids") is None
        assert model.get("external_id") == external_id
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
        committee_name = "test_committee1"

        response = self.request(
            "committee.create", {"name": committee_name, "organization_id": 1}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("committee/1")
        assert model.get("name") == committee_name

    def test_create_user_management_level(self) -> None:
        self.create_model("user/13", {"username": "test"})
        committee_name = "test_committee1"

        response = self.request(
            "committee.create",
            {
                "name": committee_name,
                "organization_id": 1,
                "manager_ids": [13],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/1",
            {
                "name": committee_name,
                "user_ids": [13],
                "manager_ids": [13],
            },
        )
        self.assert_model_exists(
            "user/13",
            {
                "committee_management_ids": [1],
                "committee_ids": [1],
            },
        )

    def test_create_user_management_level_ids_with_existing_committee(self) -> None:
        self.create_model(
            "user/13",
            {
                "username": "test",
                "committee_ids": [3],
                "committee_management_ids": [3],
            },
        )
        self.create_model("committee/3", {"name": "test_committee2", "user_ids": [13]})
        committee_name = "test_committee4"

        response = self.request(
            "committee.create",
            {
                "name": committee_name,
                "organization_id": 1,
                "manager_ids": [13],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/4",
            {"name": committee_name, "user_ids": [13]},
        )
        self.assert_model_exists(
            "user/13",
            {
                "committee_management_ids": [3, 4],
                "committee_ids": [3, 4],
            },
        )

    def test_create_wrong_field(self) -> None:
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
            "data must contain ['name', 'organization_id'] properties",
            response.json["message"],
        )
        self.assert_model_not_exists("committee/1")

    def test_create_empty_data_list(self) -> None:
        response = self.request_multi("committee.create", [])
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("committee/1")

    def test_not_existing_user(self) -> None:
        response = self.request(
            "committee.create",
            {
                "name": "test_committee1",
                "organization_id": 1,
                "manager_ids": [20, 21],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn("does not exist", response.json["message"])
        self.assert_model_not_exists("committee/1")

    def test_create_self_forwarded_and_received_ok_self_self(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
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
                "receive_forwardings_from_committee_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/1",
            {
                "forward_to_committee_ids": [1],
                "receive_forwardings_from_committee_ids": [1],
            },
        )

    def test_create_self_forwarded_and_received_ok_self_None(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
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
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/1",
            {
                "forward_to_committee_ids": [1],
                "receive_forwardings_from_committee_ids": [1],
            },
        )

    def test_create_self_forwarded_and_received_asyn1(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
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
            "Forwarding or receiving to/from own must be configured in both directions!",
            response.json["message"],
        )

    def test_create_self_forwarded_and_received_asyn2(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "name": "test_organization1",
                },
            }
        )
        response = self.request(
            "committee.create",
            {
                "name": "committee 1",
                "organization_id": 1,
                "forward_to_committee_ids": [],
                "receive_forwardings_from_committee_ids": [1],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Forwarding or receiving to/from own must be configured in both directions!",
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
                "manager_ids": [20, 21],
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
                "manager_ids": [20, 21],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("committee/1")

    def test_create_after_deleting_default_committee(self) -> None:
        # details see Backend Issue1071
        self.set_models(self.test_models)
        self.set_models(
            {
                "committee/1": {
                    "organization_tag_ids": [12],
                    "forward_to_committee_ids": [2],
                    "receive_forwardings_from_committee_ids": [3],
                    "user_ids": [1],
                    "organization_id": 1,
                    "manager_ids": [1],
                },
                "user/1": {
                    "committee_management_ids": [1],
                    "committee_ids": [1],
                },
                ONE_ORGANIZATION_FQID: {"committee_ids": [1]},
            }
        )
        response = self.request("committee.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("committee/1", {"user_ids": [1], "manager_ids": [1]})

        response = self.request(
            "committee.create",
            {
                "name": "committee2",
                "organization_id": 1,
                "manager_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_deleted("committee/1", {"user_ids": [1], "manager_ids": [1]})
        self.assert_model_exists(
            "committee/2",
            {
                "name": "committee2",
                "user_ids": [1],
                "manager_ids": [1],
            },
        )
        self.assert_model_exists(
            "user/1",
            {"committee_management_ids": [2], "committee_ids": [2]},
        )

    def test_create_external_id_not_unique(self) -> None:
        external_id = "external"
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"name": "test_organization1"},
                "committee/1": {
                    "organization_id": 1,
                    "name": "c1",
                    "external_id": external_id,
                },
            }
        )

        response = self.request(
            "committee.create",
            {
                "name": "committee_name",
                "organization_id": 1,
                "external_id": external_id,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The external_id of the committee is not unique.", response.json["message"]
        )

    def test_create_external_id_empty_special_case(self) -> None:
        external_id = ""
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"name": "test_organization1"},
                "committee/1": {
                    "organization_id": 1,
                    "name": "c1",
                    "external_id": external_id,
                },
            }
        )

        response = self.request(
            "committee.create",
            {
                "name": "committee_name",
                "organization_id": 1,
                "external_id": external_id,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/2",
            {
                "name": "committee_name",
                "organization_id": 1,
                "external_id": external_id,
            },
        )
