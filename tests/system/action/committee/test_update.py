from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from tests.system.action.base import BaseActionTestCase


class CommitteeUpdateActionTest(BaseActionTestCase):
    COMMITTEE_ID = 1
    COMMITTEE_FQID = "committee/1"
    COMMITTEE_NAME = "committee_testname"
    COMMITTEE_ID_FORWARD = 2
    COMMITTEE_FQID_FORWARD = "committee/2"

    def create_data(self) -> None:
        self.set_models(
            {
                "organization/1": {"name": "test_organization1"},
                "user/20": {"username": "test_user20"},
                "user/21": {"username": "test_user21"},
            }
        )

        response = self.request(
            "committee.create",
            {
                "name": self.COMMITTEE_NAME,
                "organization_id": 1,
                "description": "<p>Test description</p>",
                "user_ids": [20, 21],
            },
        )
        self.assert_status_code(response, 200)

        response = self.request(
            "committee.create",
            {
                "name": "forwarded_committee",
                "organization_id": 1,
            },
        )
        self.assert_status_code(response, 200)

    def create_meetings(self) -> None:
        self.set_models(
            {
                "meeting/200": {"committee_id": self.COMMITTEE_ID},
                "meeting/201": {"committee_id": self.COMMITTEE_ID},
            }
        )

    def test_update_correct(self) -> None:
        self.create_data()
        new_name = "committee_testname_updated"
        response = self.request(
            "committee.update", {"id": self.COMMITTEE_ID, "name": new_name}
        )
        self.assert_status_code(response, 200)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertEqual(model.get("name"), new_name)

    def test_update_everything_correct(self) -> None:
        self.create_data()
        self.create_meetings()
        new_name = "committee_testname_updated"
        new_description = "<p>New Test description</p>"
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "name": new_name,
                "description": new_description,
                "user_ids": [20, 21],
                "forward_to_committee_ids": [self.COMMITTEE_ID_FORWARD],
                "template_meeting_id": 200,
                "default_meeting_id": 201,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertEqual(model.get("name"), new_name)
        self.assertEqual(model.get("description"), new_description)
        self.assertEqual(model.get("user_ids"), [20, 21])
        self.assertEqual(
            model.get("forward_to_committee_ids"), [self.COMMITTEE_ID_FORWARD]
        )
        self.assertEqual(model.get("template_meeting_id"), 200)
        self.assertEqual(model.get("default_meeting_id"), 201)

    def test_update_receive_forwardings(self) -> None:
        self.create_data()
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID_FORWARD,
                "receive_forwardings_from_committee_ids": [self.COMMITTEE_ID],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            self.COMMITTEE_FQID,
            {"forward_to_committee_ids": [self.COMMITTEE_ID_FORWARD]},
        )
        self.assert_model_exists(
            self.COMMITTEE_FQID_FORWARD,
            {"receive_forwardings_from_committee_ids": [self.COMMITTEE_ID]},
        )

    def test_update_both_forwarded_and_received(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "name": "test_organization1",
                    "committee_ids": [1, 2, 3],
                },
                "committee/1": {"name": "committee_1", "organization_id": 1},
                "committee/2": {"name": "committee_2", "organization_id": 1},
                "committee/3": {"name": "committee_3", "organization_id": 1},
            }
        )
        response = self.request(
            "committee.update",
            {
                "id": 1,
                "forward_to_committee_ids": [2],
                "receive_forwardings_from_committee_ids": [3],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/1",
            {
                "forward_to_committee_ids": [2],
                "receive_forwardings_from_committee_ids": [3],
            },
        )
        self.assert_model_exists(
            "committee/2", {"receive_forwardings_from_committee_ids": [1]}
        )
        self.assert_model_exists("committee/3", {"forward_to_committee_ids": [1]})

    def test_update_both_forwarded_and_received_async(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "name": "test_organization1",
                    "committee_ids": [1],
                },
                "committee/1": {
                    "name": "committee_1",
                    "organization_id": 1,
                    "forward_to_committee_ids": [2],
                    "receive_forwardings_from_committee_ids": [2],
                },
                "committee/2": {
                    "name": "committee_2",
                    "organization_id": 1,
                    "forward_to_committee_ids": [1],
                    "receive_forwardings_from_committee_ids": [
                        1,
                    ],
                },
            }
        )
        response = self.request(
            "committee.update",
            {
                "id": 1,
                "forward_to_committee_ids": [1],
                "receive_forwardings_from_committee_ids": [2],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Forwarding or receiving to/from own must be configured in both directions!",
            response.json["message"],
        )

    def test_update_complex_1(self) -> None:
        """A->C and B->C exist, test that the request for C with {B, D}->C works and sets the reverse relations on A and D correctly."""
        self.set_models(
            {
                "organization/1": {
                    "name": "test_organization1",
                    "committee_ids": [1, 2, 3, 4],
                },
                "committee/1": {
                    "name": "committee_A",
                    "organization_id": 1,
                    "forward_to_committee_ids": [3],
                },
                "committee/2": {
                    "name": "committee_B",
                    "organization_id": 1,
                    "forward_to_committee_ids": [3],
                },
                "committee/3": {
                    "name": "committee_C",
                    "organization_id": 1,
                    "receive_forwardings_from_committee_ids": [1, 2],
                },
                "committee/4": {"name": "committee_D", "organization_id": 1},
            }
        )
        response = self.request(
            "committee.update",
            {
                "id": 3,
                "receive_forwardings_from_committee_ids": [2, 4],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/1",
            {
                "forward_to_committee_ids": [],
            },
        )
        self.assert_model_exists("committee/2", {"forward_to_committee_ids": [3]})
        self.assert_model_exists(
            "committee/3", {"receive_forwardings_from_committee_ids": [2, 4]}
        )
        self.assert_model_exists("committee/4", {"forward_to_committee_ids": [3]})

    def test_update_complex_2(self) -> None:
        """C->A and C->B exists, test that the request for C with C->{B,D} works and sets the reverse relations on A and D correctly"""
        self.set_models(
            {
                "organization/1": {
                    "name": "test_organization1",
                    "committee_ids": [1, 2, 3, 4],
                },
                "committee/1": {
                    "name": "committee_A",
                    "organization_id": 1,
                    "receive_forwardings_from_committee_ids": [3],
                },
                "committee/2": {
                    "name": "committee_B",
                    "organization_id": 1,
                    "receive_forwardings_from_committee_ids": [3],
                },
                "committee/3": {
                    "name": "committee_C",
                    "organization_id": 1,
                    "forward_to_committee_ids": [1, 2],
                },
                "committee/4": {"name": "committee_D", "organization_id": 1},
            }
        )
        response = self.request(
            "committee.update",
            {
                "id": 3,
                "forward_to_committee_ids": [2, 4],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/1",
            {
                "receive_forwardings_from_committee_ids": [],
            },
        )
        self.assert_model_exists(
            "committee/2", {"receive_forwardings_from_committee_ids": [3]}
        )
        self.assert_model_exists("committee/3", {"forward_to_committee_ids": [2, 4]})
        self.assert_model_exists(
            "committee/4", {"receive_forwardings_from_committee_ids": [3]}
        )

    def test_update_complex_3(self) -> None:
        """C->A and C->B exists, test that the request for C with C->{} works and sets the reverse relations on A and B correctly"""
        self.set_models(
            {
                "organization/1": {
                    "name": "test_organization1",
                    "committee_ids": [1, 2, 3],
                },
                "committee/1": {
                    "name": "committee_A",
                    "organization_id": 1,
                    "receive_forwardings_from_committee_ids": [3],
                },
                "committee/2": {
                    "name": "committee_B",
                    "organization_id": 1,
                    "receive_forwardings_from_committee_ids": [3],
                },
                "committee/3": {
                    "name": "committee_C",
                    "organization_id": 1,
                    "forward_to_committee_ids": [1, 2],
                },
            }
        )
        response = self.request(
            "committee.update",
            {
                "id": 3,
                "forward_to_committee_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/1",
            {
                "receive_forwardings_from_committee_ids": [],
            },
        )
        self.assert_model_exists(
            "committee/2", {"receive_forwardings_from_committee_ids": []}
        )
        self.assert_model_exists("committee/3", {"forward_to_committee_ids": []})

    def test_update_complex_4(self) -> None:
        """A->A, Try A->{}"""
        self.set_models(
            {
                "organization/1": {
                    "name": "test_organization1",
                    "committee_ids": [1],
                },
                "committee/1": {
                    "name": "committee_A",
                    "organization_id": 1,
                    "forward_to_committee_ids": [1],
                    "receive_forwardings_from_committee_ids": [1],
                },
            }
        )
        response = self.request(
            "committee.update",
            {
                "id": 1,
                "forward_to_committee_ids": [],
                "receive_forwardings_from_committee_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/1",
            {
                "forward_to_committee_ids": [],
                "receive_forwardings_from_committee_ids": [],
            },
        )

    def test_update_complex_5(self) -> None:
        """A->B, B->{C,D}: Try request B, C->B and B->D"""
        self.set_models(
            {
                "organization/1": {
                    "name": "test_organization1",
                    "committee_ids": [1, 2, 3, 4],
                },
                "committee/1": {
                    "name": "committee_A",
                    "organization_id": 1,
                    "forward_to_committee_ids": [2],
                },
                "committee/2": {
                    "name": "committee_B",
                    "organization_id": 1,
                    "receive_forwardings_from_committee_ids": [1],
                    "forward_to_committee_ids": [3, 4],
                },
                "committee/3": {
                    "name": "committee_C",
                    "organization_id": 1,
                    "receive_forwardings_from_committee_ids": [2],
                },
                "committee/4": {
                    "name": "committee_D",
                    "organization_id": 1,
                    "receive_forwardings_from_committee_ids": [2],
                },
            }
        )
        response = self.request(
            "committee.update",
            {
                "id": 2,
                "forward_to_committee_ids": [4],
                "receive_forwardings_from_committee_ids": [3],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/1",
            {
                "forward_to_committee_ids": [],
            },
        )
        self.assert_model_exists(
            "committee/2",
            {
                "forward_to_committee_ids": [4],
                "receive_forwardings_from_committee_ids": [3],
            },
        )
        self.assert_model_exists(
            "committee/3",
            {
                "forward_to_committee_ids": [2],
                "receive_forwardings_from_committee_ids": [],
            },
        )
        self.assert_model_exists(
            "committee/4", {"receive_forwardings_from_committee_ids": [2]}
        )

    def test_update_wrong_user_ids(self) -> None:
        self.create_data()
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "user_ids": [30],
            },
        )
        self.assert_status_code(response, 400)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertEqual(model.get("user_ids"), [20, 21])
        self.assertIn(
            "Model 'user/30' does not exist.",
            response.json["message"],
        )

    def test_update_wrong_forward_committee(self) -> None:
        self.create_data()
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "forward_to_committee_ids": [101],
            },
        )
        self.assert_status_code(response, 400)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertIsNone(model.get("forward_to_committee_ids"))
        self.assertIn(
            "Model 'committee/101' does not exist.",
            response.json["message"],
        )

    def test_update_wrong_template_meeting(self) -> None:
        self.create_data()
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "template_meeting_id": 299,
            },
        )
        self.assert_status_code(response, 400)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertIsNone(model.get("template_meeting_id"))
        self.assertIn(
            "Model 'meeting/299' does not exist.",
            response.json["message"],
        )

    def test_update_template_meeting_wrong_committee(self) -> None:
        self.create_data()
        self.set_models({"meeting/299": {"committee_id": 2}})
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "template_meeting_id": 299,
            },
        )
        self.assert_status_code(response, 400)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertIsNone(model.get("template_meeting_id"))
        self.assertIn(
            f"Meeting 299 does not belong to committee {self.COMMITTEE_ID}",
            response.json["message"],
        )

    def test_update_wrong_default_meeting(self) -> None:
        self.create_data()
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "default_meeting_id": 299,
            },
        )
        self.assert_status_code(response, 400)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertIsNone(model.get("default_meeting_id"))
        self.assertIn(
            "Model 'meeting/299' does not exist.",
            response.json["message"],
        )

    def test_update_default_meeting_wrong_committee(self) -> None:
        self.create_data()
        self.set_models({"meeting/299": {"committee_id": 2}})
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "default_meeting_id": 299,
            },
        )
        self.assert_status_code(response, 400)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertIsNone(model.get("default_meeting_id"))
        self.assertIn(
            f"Meeting 299 does not belong to committee {self.COMMITTEE_ID}",
            response.json["message"],
        )

    def test_update_wrong_id(self) -> None:
        self.create_data()
        response = self.request("committee.update", {"id": 200, "name": "xxxxx"})
        self.assert_status_code(response, 400)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertEqual(model.get("name"), self.COMMITTEE_NAME)

    def test_update_correct_manager_ids(self) -> None:
        self.create_data()
        response = self.request(
            "committee.update",
            {"id": self.COMMITTEE_ID, "name": "test", "manager_ids": [20]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/20",
            {
                f"committee_${self.COMMITTEE_ID}_management_level": CommitteeManagementLevel.CAN_MANAGE
            },
        )

    def test_update_manager_ids_in_committee(self) -> None:
        self.create_data()
        response = self.request(
            "committee.update",
            {"id": self.COMMITTEE_ID, "manager_ids": [1]},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                f"committee_${self.COMMITTEE_ID}_management_level": CommitteeManagementLevel.CAN_MANAGE,
                "committee_ids": [self.COMMITTEE_ID],
            },
        )
        committee = self.get_model("committee/1")
        self.assertCountEqual((1, 20, 21), committee["user_ids"])

    def test_update_manager_ids_rm_manager(self) -> None:
        # prepare data
        self.create_data()
        response = self.request(
            "committee.update",
            {"id": self.COMMITTEE_ID, "name": "test", "manager_ids": [20]},
        )
        self.assert_status_code(response, 200)
        committee = self.get_model(f"committee/{self.COMMITTEE_ID}")
        self.assertCountEqual((20, 21), committee["user_ids"])
        # important request.
        response = self.request(
            "committee.update",
            {"id": self.COMMITTEE_ID, "name": "test", "manager_ids": [21]},
        )
        self.assert_status_code(response, 200)
        committee = self.get_model(f"committee/{self.COMMITTEE_ID}")
        self.assertCountEqual((20, 21), committee["user_ids"])
        self.assert_model_exists(
            "user/21",
            {"committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE},
        )
        self.assert_model_exists(
            "user/20",
            {
                "committee_$_management_level": [],
                "committee_$1_management_level": None,
            },
        )

    def test_update_group_a_no_permission(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS
                }
            }
        )
        response = self.request(
            "committee.update", {"id": 1, "name": "test", "description": "blablabla"}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action committee.update. Missing permissions: OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_update_group_a_permission_1(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
                },
                "committee/1": {"organization_id": 1},
            }
        )
        response = self.request(
            "committee.update", {"id": 1, "name": "test", "description": "blablabla"}
        )
        self.assert_status_code(response, 200)

    def test_update_group_a_permission_2(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/1": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                },
                "committee/1": {"organization_id": 1},
            }
        )
        response = self.request(
            "committee.update", {"id": 1, "name": "test", "description": "blablabla"}
        )
        self.assert_status_code(response, 200)

    def test_update_group_b_no_permission(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                },
                "committee/1": {"user_ids": [1]},
            }
        )
        response = self.request("committee.update", {"id": 1, "user_ids": [1, 20]})
        self.assert_status_code(response, 403)
        assert (
            "Missing OrganizationManagementLevel: can_manage_organization"
            in response.json["message"]
        )

    def test_update_group_b_permission(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/1": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
                },
                "committee/1": {"user_ids": [1]},
            }
        )
        response = self.request("committee.update", {"id": 1, "user_ids": [1, 20]})
        self.assert_status_code(response, 200)

    def test_add_manager_ids_to_user_ids(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "name": "test_organization1",
                    "committee_ids": [self.COMMITTEE_ID],
                },
                "committee/1": {
                    "name": self.COMMITTEE_NAME,
                    "organization_id": 1,
                    "description": "<p>Test description</p>",
                },
                "user/20": {"username": "test_user20"},
                "user/21": {"username": "test_user21"},
            }
        )
        response = self.request(
            "committee.update", {"id": 1, "user_ids": [1, 20], "manager_ids": [1, 21]}
        )
        self.assert_status_code(response, 200)
        committee = self.get_model("committee/1")
        self.assertCountEqual((1, 20, 21), committee["user_ids"])

    def test_remove_manager_from_user_ids(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/20": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_$_management_level": ["1"],
                },
                "user/21": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_$_management_level": ["1"],
                },
            }
        )
        response = self.request(
            "committee.update", {"id": self.COMMITTEE_ID, "user_ids": [20]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("committee/1", {"user_ids": [20]})
        self.assert_model_exists(
            "user/20",
            {
                "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                "committee_$_management_level": ["1"],
                "committee_ids": [1],
            },
        )
        self.assert_model_exists(
            "user/21",
            {
                "committee_$1_management_level": None,
                "committee_$_management_level": [],
                "committee_ids": [],
            },
        )

    def test_remove_cml_manager_from_user21_v1(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/20": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_$_management_level": ["1"],
                },
                "user/21": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_$_management_level": ["1"],
                },
            }
        )
        response = self.request(
            "committee.update", {"id": self.COMMITTEE_ID, "manager_ids": [20]}
        )
        self.assert_status_code(response, 200)
        committee = self.get_model("committee/1")
        self.assertCountEqual([20, 21], committee["user_ids"])
        self.assert_model_exists(
            "user/20",
            {
                "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                "committee_$_management_level": ["1"],
                "committee_ids": [1],
            },
        )
        self.assert_model_exists(
            "user/21",
            {
                "committee_$1_management_level": None,
                "committee_$_management_level": [],
                "committee_ids": [1],
            },
        )

    def test_remove_cml_manager_from_user21_v2(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/20": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_$_management_level": ["1"],
                },
                "user/21": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_$_management_level": ["1"],
                },
            }
        )
        response = self.request(
            "committee.update",
            {"id": self.COMMITTEE_ID, "user_ids": [21], "manager_ids": [20]},
        )
        self.assert_status_code(response, 200)
        committee = self.get_model("committee/1")
        self.assertCountEqual([20, 21], committee["user_ids"])
        self.assert_model_exists(
            "user/20",
            {
                "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                "committee_$_management_level": ["1"],
                "committee_ids": [1],
            },
        )
        self.assert_model_exists(
            "user/21",
            {
                "committee_$1_management_level": None,
                "committee_$_management_level": [],
                "committee_ids": [1],
            },
        )

    def test_several_additions_and_removements(self) -> None:
        """
        20 remove completely
        21 remove only manager permission
        22 add manager permission to existing member(and implicitly stay as user, not necessary)
        23 add as manager (and explicitly as user)
        24 add as user only
        """
        self.create_data()
        self.set_models(
            {
                "user/20": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_$_management_level": ["1"],
                },
                "user/21": {
                    "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                    "committee_$_management_level": ["1"],
                },
                "user/22": {"username": "test22", "committee_ids": [1]},
                "user/23": {"username": "test23"},
                "user/24": {"username": "test24"},
                "committee/1": {"user_ids": [20, 21, 22]},
            }
        )
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "user_ids": [21, 23, 24],
                "manager_ids": [22, 23],
            },
        )
        self.assert_status_code(response, 200)
        committee = self.get_model("committee/1")
        self.assertCountEqual([21, 22, 23, 24], committee["user_ids"])
        self.assert_model_exists(
            "user/20", {"committee_$1_management_level": None, "committee_ids": []}
        )
        self.assert_model_exists(
            "user/21", {"committee_$1_management_level": None, "committee_ids": [1]}
        )
        self.assert_model_exists(
            "user/22",
            {
                "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                "committee_$_management_level": ["1"],
                "committee_ids": [1],
            },
        )
        self.assert_model_exists(
            "user/23",
            {
                "committee_$1_management_level": CommitteeManagementLevel.CAN_MANAGE,
                "committee_$_management_level": ["1"],
                "committee_ids": [1],
            },
        )
        self.assert_model_exists(
            "user/24", {"committee_$1_management_level": None, "committee_ids": [1]}
        )
