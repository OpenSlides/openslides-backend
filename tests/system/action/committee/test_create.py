from typing import Any

from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class CommitteeCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.test_models: dict[str, dict[str, Any]] = {
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

    def test_create_with_parent(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "organization_id": 1,
                    "name": "Committee 1",
                },
                ONE_ORGANIZATION_FQID: {
                    "limit_of_meetings": 0,
                    "enable_electronic_voting": True,
                },
            }
        )

        response = self.request(
            "committee.create",
            {"name": "Committee 2", "organization_id": 1, "parent_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/2",
            {
                "name": "Committee 2",
                "organization_id": 1,
                "parent_id": 1,
                "all_parent_ids": [1],
            },
        )
        self.assert_model_exists(
            "committee/1", {"child_ids": [2], "all_child_ids": [2]}
        )

    def test_create_with_parent_as_committee_admin(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "organization_id": 1,
                    "name": "Committee 1",
                },
                ONE_ORGANIZATION_FQID: {
                    "limit_of_meetings": 0,
                    "enable_electronic_voting": True,
                },
            }
        )
        self.set_committee_management_level([1])
        self.set_organization_management_level(None)

        response = self.request(
            "committee.create",
            {"name": "Committee 2", "organization_id": 1, "parent_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/2",
            {
                "name": "Committee 2",
                "organization_id": 1,
                "parent_id": 1,
                "all_parent_ids": [1],
            },
        )

    def test_create_with_parent_as_grandparent_committee_admin(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "organization_id": 1,
                    "name": "Committee 1",
                    "child_ids": [2],
                    "all_child_ids": [2],
                },
                "committee/2": {
                    "organization_id": 1,
                    "name": "Committee 2",
                    "parent_id": 1,
                    "all_parent_ids": [1],
                },
                ONE_ORGANIZATION_FQID: {
                    "limit_of_meetings": 0,
                    "enable_electronic_voting": True,
                },
            }
        )
        self.set_committee_management_level([1])
        self.set_organization_management_level(None)

        response = self.request_multi(
            "committee.create",
            [
                {"name": "Committee 3", "organization_id": 1, "parent_id": 2},
                {"name": "Committee 4", "organization_id": 1, "parent_id": 2},
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/1",
            {
                "child_ids": [2],
                "all_child_ids": [2, 3, 4],
            },
        )
        self.assert_model_exists(
            "committee/2",
            {
                "parent_id": 1,
                "all_parent_ids": [1],
                "child_ids": [3, 4],
                "all_child_ids": [3, 4],
            },
        )
        self.assert_model_exists(
            "committee/3",
            {
                "name": "Committee 3",
                "organization_id": 1,
                "parent_id": 2,
                "all_parent_ids": [1, 2],
            },
        )
        self.assert_model_exists(
            "committee/4",
            {
                "name": "Committee 4",
                "organization_id": 1,
                "parent_id": 2,
                "all_parent_ids": [1, 2],
            },
        )

    def test_create_with_parent_wrong_committee_admin(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "organization_id": 1,
                    "name": "Committee 1",
                },
                "committee/2": {
                    "organization_id": 1,
                    "name": "Committee 2",
                },
                ONE_ORGANIZATION_FQID: {
                    "limit_of_meetings": 0,
                    "enable_electronic_voting": True,
                },
            }
        )
        self.set_committee_management_level([2])
        self.set_organization_management_level(None)

        response = self.request(
            "committee.create",
            {"name": "Committee 3", "organization_id": 1, "parent_id": 1},
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action committee.create. Missing permissions: OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_create_with_parent_not_committee_admin(self) -> None:
        self.set_models(
            {
                "committee/1": {
                    "organization_id": 1,
                    "name": "Committee 1",
                },
                ONE_ORGANIZATION_FQID: {
                    "limit_of_meetings": 0,
                    "enable_electronic_voting": True,
                },
            }
        )
        self.set_organization_management_level(None)
        response = self.request(
            "committee.create",
            {"name": "Committee 2", "organization_id": 1, "parent_id": 1},
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action committee.create. Missing permissions: OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_create_add_forwarding_relations(
        self,
        fail_forward_from: bool = False,
        fail_forward_to: bool = False,
        has_parent_id: bool = True,
    ) -> None:
        self.create_committee()
        self.create_committee(2)
        self.create_committee(3)
        self.create_committee(4)
        self.create_committee(5)
        self.create_committee(6, parent_id=5)
        self.set_models(
            {
                "committee/1": {
                    "forward_to_committee_ids": [2],
                    "receive_forwardings_from_committee_ids": [2],
                },
                "committee/2": {
                    "forward_to_committee_ids": [1],
                    "receive_forwardings_from_committee_ids": [1],
                },
            }
        )
        cmls = [1, 2]
        to_fail = {3, 4, 6}
        if not fail_forward_to:
            cmls.extend([3, 5])
            to_fail.remove(3)
            to_fail.remove(6)
        if not fail_forward_from:
            cmls.append(4)
            to_fail.remove(4)
        self.set_committee_management_level(cmls)
        self.set_organization_management_level(None)
        data = {
            "name": "It's in Arameic",
            "organization_id": 1,
            "forward_to_committee_ids": [3, 6],
            "receive_forwardings_from_committee_ids": [2, 4],
        }
        if has_parent_id:
            data["parent_id"] = 1
        response = self.request(
            "committee.create",
            data,
        )
        if not has_parent_id:
            self.assert_status_code(response, 403)
            assert (
                "You are not allowed to perform action committee.create. Missing OrganizationManagementLevel: can_manage_organization"
                == response.json["message"]
            )
        elif to_fail:
            self.assert_status_code(response, 403)
            msg: str = response.json["message"]
            self.assertIn(
                "You are not allowed to perform action committee.create. Missing permissions: OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committee",
                msg,
            )
            numbers = {
                int(numstr.strip())
                for numstr in msg.split("{")[1].split("}")[0].split(",")
            }
            assert len(numbers.intersection(to_fail)) == len(to_fail)
        else:
            self.assert_status_code(response, 200)
            self.assert_model_exists(
                "committee/7",
                {
                    "name": "It's in Arameic",
                    "organization_id": 1,
                    "forward_to_committee_ids": [3, 6],
                    "receive_forwardings_from_committee_ids": [2, 4],
                },
            )

    def test_create_add_forwarding_relations_fail_forward_to(self) -> None:
        self.test_create_add_forwarding_relations(fail_forward_to=True)

    def test_create_add_forwarding_relations_fail_forward_from(self) -> None:
        self.test_create_add_forwarding_relations(fail_forward_from=True)

    def test_create_add_forwarding_relations_fail_forward_to_and_from(self) -> None:
        self.test_create_add_forwarding_relations(
            fail_forward_to=True, fail_forward_from=True
        )

    def test_create_add_forwarding_relations_no_parent(self) -> None:
        self.test_create_add_forwarding_relations(
            fail_forward_to=True, has_parent_id=False
        )

    def test_create_add_forwarding_relations_no_parent_fail_forward_to(self) -> None:
        self.test_create_add_forwarding_relations(
            fail_forward_to=True, has_parent_id=False
        )

    def test_create_add_forwarding_relations_no_parent_fail_forward_from(self) -> None:
        self.test_create_add_forwarding_relations(
            fail_forward_from=True, has_parent_id=False
        )

    def test_create_add_forwarding_relations_no_parent_fail_forward_to_and_from(
        self,
    ) -> None:
        self.test_create_add_forwarding_relations(
            fail_forward_to=True, fail_forward_from=True, has_parent_id=False
        )
