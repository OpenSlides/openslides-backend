from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from tests.system.action.base import BaseActionTestCase


class CommitteeUpdateActionTest(BaseActionTestCase):
    COMMITTEE_ID = 1
    COMMITTEE_FQID = "committee/1"
    COMMITTEE_NAME = "committee_testname"
    COMMITTEE_ID_FORWARD = 2
    COMMITTEE_FQID_FORWARD = "committee/2"

    def create_data(self) -> None:
        self.create_committee(self.COMMITTEE_ID, name=self.COMMITTEE_NAME)
        self.create_committee(self.COMMITTEE_ID_FORWARD)
        self.set_models(
            {
                "user/20": {"username": "test_user20"},
                "user/21": {"username": "test_user21"},
            }
        )

    def create_meetings_with_users(self) -> None:
        self.create_meeting(200)
        self.create_meeting(203)
        self.set_models(
            {
                "meeting/200": {"committee_id": self.COMMITTEE_ID},
                "meeting/203": {"committee_id": self.COMMITTEE_ID},
                "group/2001": {
                    "name": "knitting grandpas",
                    "meeting_user_ids": [20, 21],
                    "meeting_id": 200,
                },
                "group/2031": {"name": "cycling thursdays", "meeting_id": 203},
                "meeting_user/20": {
                    "meeting_id": 200,
                    "user_id": 20,
                },
                "meeting_user/21": {
                    "meeting_id": 200,
                    "user_id": 21,
                },
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
        new_name = "committee_testname_updated"
        new_description = "<p>New Test description</p>"
        external_id = "external"

        self.create_data()
        self.update_model(self.COMMITTEE_FQID, {"external_id": external_id})
        self.create_meetings_with_users()

        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "name": new_name,
                "external_id": external_id,
                "description": new_description,
                "manager_ids": [20, 21],
                "forward_to_committee_ids": [self.COMMITTEE_ID_FORWARD],
                "default_meeting_id": 203,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            self.COMMITTEE_FQID,
            {
                "name": new_name,
                "external_id": external_id,
                "description": new_description,
                "user_ids": [20, 21],
                "manager_ids": [20, 21],
                "forward_to_committee_ids": [self.COMMITTEE_ID_FORWARD],
                "default_meeting_id": 203,
            },
        )

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
                "committee/1": {
                    "name": "committee_1",
                    "organization_id": 1,
                    "forward_to_committee_ids": [2],
                },
                "committee/2": {
                    "name": "committee_2",
                    "organization_id": 1,
                    "forward_to_committee_ids": [1],
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
        self.assert_model_exists("committee/1", {"forward_to_committee_ids": None})
        self.assert_model_exists("committee/2", {"forward_to_committee_ids": [3]})
        self.assert_model_exists(
            "committee/3", {"receive_forwardings_from_committee_ids": [2, 4]}
        )
        self.assert_model_exists("committee/4", {"forward_to_committee_ids": [3]})

    def test_update_complex_2(self) -> None:
        """C->A and C->B exists, test that the request for C with C->{B,D} works and sets the reverse relations on A and D correctly"""
        self.set_models(
            {
                "committee/1": {
                    "name": "committee_A",
                    "organization_id": 1,
                },
                "committee/2": {
                    "name": "committee_B",
                    "organization_id": 1,
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
            {"receive_forwardings_from_committee_ids": None},
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
                "committee/1": {
                    "name": "committee_A",
                    "organization_id": 1,
                },
                "committee/2": {
                    "name": "committee_B",
                    "organization_id": 1,
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
            "committee/1", {"receive_forwardings_from_committee_ids": None}
        )
        self.assert_model_exists(
            "committee/2", {"receive_forwardings_from_committee_ids": None}
        )
        self.assert_model_exists("committee/3", {"forward_to_committee_ids": None})

    def test_update_complex_4(self) -> None:
        """A->A, Try A->{}"""
        self.set_models(
            {
                "committee/1": {
                    "name": "committee_A",
                    "organization_id": 1,
                    "forward_to_committee_ids": [1],
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
                "forward_to_committee_ids": None,
                "receive_forwardings_from_committee_ids": None,
            },
        )

    def test_update_complex_5(self) -> None:
        """A->B, B->{C,D}: Try request B, C->B and B->D"""
        self.set_models(
            {
                "committee/1": {
                    "name": "committee_A",
                    "organization_id": 1,
                    "forward_to_committee_ids": [2],
                },
                "committee/2": {
                    "name": "committee_B",
                    "organization_id": 1,
                    "forward_to_committee_ids": [3, 4],
                },
                "committee/3": {
                    "name": "committee_C",
                    "organization_id": 1,
                },
                "committee/4": {
                    "name": "committee_D",
                    "organization_id": 1,
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
        self.assert_model_exists("committee/1", {"forward_to_committee_ids": None})
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
                "receive_forwardings_from_committee_ids": None,
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
                "manager_ids": [30],
            },
        )
        self.assert_status_code(response, 400)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertEqual(model.get("user_ids"), None)
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
        self.create_meeting(299)
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

    def test_update_correct_user_management_level(self) -> None:
        self.create_data()
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "name": "test",
                "manager_ids": [20],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/20",
            {"committee_management_ids": [self.COMMITTEE_ID]},
        )

    def test_update_user_management_level_in_committee(self) -> None:
        self.create_data()
        self.create_meetings_with_users()
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "manager_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {
                "committee_management_ids": [self.COMMITTEE_ID],
                "committee_ids": [self.COMMITTEE_ID],
            },
        )
        committee = self.get_model("committee/1")
        self.assertCountEqual(committee["user_ids"], [1, 20, 21])
        self.assertCountEqual(committee["manager_ids"], [1])

    def test_update_user_management_level_rm_manager(self) -> None:
        # prepare data
        self.create_data()
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "name": "test",
                "manager_ids": [20, 21],
            },
        )
        self.assert_status_code(response, 200)
        committee = self.get_model(self.COMMITTEE_FQID)
        self.assertCountEqual((20, 21), committee["user_ids"])
        # important request.
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "name": "test",
                "manager_ids": [21],
            },
        )
        self.assert_status_code(response, 200)
        committee = self.assert_model_exists(
            self.COMMITTEE_FQID,
            {"user_ids": [21], "manager_ids": [21]},
        )
        self.assert_model_exists(
            "user/21",
            {"committee_management_ids": [1], "committee_ids": [1]},
        )
        self.assert_model_exists("user/20", {"committee_management_ids": None})

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
            "committee.update",
            {
                "id": 1,
                "name": "test",
                "description": "blablabla",
                "external_id": "test",
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action committee.update. Missing permissions: OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committee 1",
            response.json["message"],
        )

    def test_update_group_a_permission_1(self) -> None:
        self.create_data()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request(
            "committee.update",
            {
                "id": 1,
                "name": "test",
                "description": "blablabla",
                "external_id": "test",
            },
        )
        self.assert_status_code(response, 200)

    def test_update_group_a_permission_2(self) -> None:
        self.create_data()
        self.set_committee_management_level([1])
        self.set_organization_management_level(None)
        response = self.request(
            "committee.update",
            {
                "id": 1,
                "name": "test",
                "description": "blablabla",
                "external_id": "test",
            },
        )
        self.assert_status_code(response, 200)

    def test_update_group_a_permission_parent_committee_admin(self) -> None:
        self.create_committee(3)
        self.create_committee(4, parent_id=3)
        self.set_committee_management_level([3])
        self.set_organization_management_level(None)
        response = self.request(
            "committee.update",
            {
                "id": 4,
                "name": "test",
                "description": "blablabla",
                "external_id": "test",
            },
        )
        self.assert_status_code(response, 200)

    def test_update_group_a_permission_grandparent_committee_admin(self) -> None:
        self.create_committee(2)
        self.create_committee(3, parent_id=2)
        self.create_committee(4, parent_id=3)
        self.set_committee_management_level([2])
        self.set_organization_management_level(None)
        response = self.request(
            "committee.update",
            {
                "id": 4,
                "name": "test",
                "description": "blablabla",
                "external_id": "test",
            },
        )
        self.assert_status_code(response, 200)

    def test_update_manager_ids_committee_permission(self) -> None:
        self.create_data()
        self.set_organization_management_level(None)
        self.set_committee_management_level([1])
        response = self.request(
            "committee.update",
            {
                "id": 1,
                "manager_ids": [1, 20],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("committee/1", {"manager_ids": [1, 20]})

    def test_update_group_b_no_permission(self) -> None:
        self.create_data()
        self.create_meetings_with_users()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_USERS
        )
        self.set_committee_management_level([1])
        response = self.request(
            "committee.update",
            {
                "id": 1,
                "forward_to_committee_ids": [2],
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "You are not allowed to perform action committee.update. Missing permissions: OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committee {2}"
            in response.json["message"]
        )

    def test_update_group_b_permission(self) -> None:
        self.create_data()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request(
            "committee.update",
            {
                "id": 1,
                "manager_ids": [1, 20],
            },
        )
        self.assert_status_code(response, 200)

    def test_add_user_management_level_to_user_ids(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                self.COMMITTEE_FQID: {
                    "name": self.COMMITTEE_NAME,
                    "description": "<p>Test description</p>",
                },
                "meeting/1": {"committee_id": self.COMMITTEE_ID},
                "user/20": {"username": "test_user20"},
                "user/21": {"username": "test_user21"},
            }
        )
        self.set_user_groups(20, [1])
        response = self.request(
            "committee.update",
            {
                "id": 1,
                "manager_ids": [1, 21],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("committee/1", {"user_ids": [1, 20, 21]})

    def test_remove_cml_manager_from_user21(self) -> None:
        self.create_data()
        self.create_meetings_with_users()
        self.set_models({"committee/1": {"manager_ids": [20, 21]}})
        response = self.request(
            "committee.update",
            {
                "id": self.COMMITTEE_ID,
                "manager_ids": [20],
            },
        )
        self.assert_status_code(response, 200)
        committee = self.get_model("committee/1")
        self.assertCountEqual([20, 21], committee["user_ids"])
        self.assert_model_exists(
            "user/20",
            {
                "committee_management_ids": [1],
                "committee_ids": [1],
            },
        )
        self.assert_model_exists(
            "user/21",
            {
                "committee_management_ids": None,
                "committee_ids": [1],
            },
        )

    def test_update_after_deleting_default_committee(self) -> None:
        # details see Backend Issue1071
        response = self.request(
            "committee.create",
            {
                "organization_id": 1,
                "name": "committee1",
                "manager_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.set_models({"committee/2": {"organization_id": 1, "name": "c2"}})

        response = self.request("committee.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", {"committee_management_ids": None})
        self.assert_model_not_exists("committee/1")

        response = self.request(
            "committee.update",
            {
                "id": 2,
                "name": "committee2",
                "manager_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
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
            {
                "committee_management_ids": [2],
            },
        )

    def test_update_external_id_not_unique(self) -> None:
        external_id = "external"
        self.set_models(
            {
                "committee/1": {"name": "c1", "external_id": external_id},
                "committee/2": {"name": "c2"},
            }
        )

        response = self.request(
            "committee.update",
            {
                "id": 2,
                "external_id": external_id,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The external_id of the committee is not unique.", response.json["message"]
        )

    def test_update_parent_id(self) -> None:
        self.create_committee(100)
        self.create_committee(200)
        response = self.request(
            "committee.update",
            {
                "id": 200,
                "parent_id": 100,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/100", {"child_ids": [200], "all_child_ids": [200]}
        )
        self.assert_model_exists(
            "committee/200", {"parent_id": 100, "all_parent_ids": [100]}
        )

    def test_update_multiple_parent_ids(self) -> None:
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )

        def create_children(
            parent_id: int = 1, next_id: int = 2, levels: int = 1
        ) -> int:
            for i in range(2):
                self.create_committee(next_id, parent_id)
                next_id += 1
                if levels > 1:
                    next_id = create_children(next_id - 1, next_id, levels - 1)
            return next_id

        self.create_committee()
        next_id = create_children(1, 2, 4)
        last_id = next_id - 1
        assert last_id == 1 + 2 + 4 + 8 + 16
        response = self.request_multi(
            "committee.update",
            [
                {"id": 2, "parent_id": None},
                {"id": 4, "parent_id": None},
                {"id": 14, "parent_id": 18},
                {"id": 15, "parent_id": 9},
                {"id": 24, "parent_id": 26},
                {"id": 31, "name": "Renamed committee"},
            ],
        )
        self.assert_status_code(response, 200)
        expected: dict[
            int, tuple[int | None, list[int] | None, list[int] | None, list[int] | None]
        ] = {
            1: (None, [17], None, [14, 16, *range(17, 32)]),
            2: (None, [3, 10], None, [3, 7, 8, 9, 10, 11, 12, 13, 15]),
            3: (2, [7], [2], [7, 8, 9, 15]),
            4: (None, [5, 6], None, [5, 6]),
            5: (4, None, [4], None),
            6: (4, None, [4], None),
            7: (3, [8, 9], [2, 3], [8, 9, 15]),
            8: (7, None, [2, 3, 7], None),
            9: (7, [15], [2, 3, 7], [15]),
            10: (2, [11], [2], [11, 12, 13]),
            11: (10, [12, 13], [2, 10], [12, 13]),
            12: (11, None, [2, 10, 11], None),
            13: (11, None, [2, 10, 11], None),
            14: (18, [16], [1, 17, 18], [16]),
            15: (9, None, [2, 3, 7, 9], None),
            16: (14, None, [1, 14, 17, 18], None),
            17: (
                1,
                [18, 25],
                [1],
                [14, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31],
            ),
            18: (17, [14, 19, 22], [1, 17], [14, 16, 19, 20, 21, 22, 23]),
            19: (18, [20, 21], [1, 17, 18], [20, 21]),
            20: (19, None, [1, 17, 18, 19], None),
            21: (19, None, [1, 17, 18, 19], None),
            22: (18, [23], [1, 17, 18], [23]),
            23: (22, None, [1, 17, 18, 22], None),
            24: (26, None, [1, 17, 25, 26], None),
            25: (17, [26, 29], [1, 17], [24, 26, 27, 28, 29, 30, 31]),
            26: (25, [24, 27, 28], [1, 17, 25], [24, 27, 28]),
            27: (26, None, [1, 17, 25, 26], None),
            28: (26, None, [1, 17, 25, 26], None),
            29: (25, [30, 31], [1, 17, 25], [30, 31]),
            30: (29, None, [1, 17, 25, 29], None),
        }
        for id_, (
            parent_id,
            child_ids,
            all_parent_ids,
            all_child_ids,
        ) in expected.items():
            self.assert_model_exists(
                f"committee/{id_}",
                {
                    "parent_id": parent_id,
                    "child_ids": child_ids,
                    "all_parent_ids": all_parent_ids,
                    "all_child_ids": all_child_ids,
                },
            )
        self.assert_model_exists(
            "committee/31",
            {
                "parent_id": 29,
                "child_ids": None,
                "all_parent_ids": [1, 17, 25, 29],
                "all_child_ids": None,
                "name": "Renamed committee",
            },
        )

    def test_update_parent_circle_error(self) -> None:
        self.create_committee()
        self.create_committee(2, parent_id=1)
        self.create_committee(3, parent_id=2)
        response = self.request(
            "committee.update",
            {
                "id": 1,
                "parent_id": 3,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot perform parent updates, as it would create circles for the following committees: {1, 2, 3}",
            response.json["message"],
        )

    def test_update_set_parent_with_child_perm(self) -> None:
        self.create_committee()
        self.create_committee(2, parent_id=1)
        self.create_committee(3, parent_id=1)
        self.set_organization_management_level(None)
        self.set_committee_management_level([3])
        response = self.request(
            "committee.update",
            {
                "id": 3,
                "parent_id": 2,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action committee.update. Missing permissions: OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committee {1}",
            response.json["message"],
        )

    def test_update_set_parent_committee_perm_not_of_shared_parents(self) -> None:
        self.create_committee()
        self.create_committee(4, parent_id=1)
        self.create_committee(2, parent_id=4)
        self.create_committee(3, parent_id=4)
        self.set_organization_management_level(None)
        self.set_committee_management_level([3])
        response = self.request(
            "committee.update",
            {
                "id": 3,
                "parent_id": 2,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action committee.update. Missing permissions: OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committees {1, 4}",
            response.json["message"],
        )

    def test_update_set_parent_committee_perm_in_shared_parent(self) -> None:
        self.create_committee()
        self.create_committee(2, parent_id=1)
        self.create_committee(3, parent_id=1)
        self.set_organization_management_level(None)
        self.set_committee_management_level([1, 2])
        response = self.request(
            "committee.update",
            {
                "id": 3,
                "parent_id": 2,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/3", {"parent_id": 2, "all_parent_ids": [1, 2]}
        )

    def test_update_set_parent_committee_perm_one_of_shared_parents(self) -> None:
        self.create_committee()
        self.create_committee(2, parent_id=1)
        self.create_committee(3, parent_id=2)
        self.create_committee(4, parent_id=3)
        self.create_committee(5, parent_id=4)
        self.create_committee(6, parent_id=4)
        self.create_committee(7, parent_id=6)
        self.set_organization_management_level(None)
        self.set_committee_management_level([2, 7])
        response = self.request(
            "committee.update",
            {
                "id": 7,
                "parent_id": 5,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/7", {"parent_id": 5, "all_parent_ids": [1, 2, 3, 4, 5]}
        )

    def test_update_set_parent_committee_perms_no_shared_parent(self) -> None:
        self.create_committee()
        self.create_committee(2, parent_id=1)
        self.create_committee(3)
        self.create_committee(4, parent_id=3)
        self.set_organization_management_level(None)
        self.set_committee_management_level([1, 3])
        response = self.request(
            "committee.update",
            {
                "id": 4,
                "parent_id": 2,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action committee.update. Missing OrganizationManagementLevel: can_manage_organization",
            response.json["message"],
        )

    def test_update_set_parent_orga_perm_no_shared_parent(self) -> None:
        self.create_committee()
        self.create_committee(2, parent_id=1)
        self.create_committee(3)
        self.create_committee(4, parent_id=3)
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request(
            "committee.update",
            {
                "id": 4,
                "parent_id": 2,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("committee/4", {"parent_id": 2})

    def test_update_unset_parent_with_committee_parent_perm(self) -> None:
        self.create_committee(3)
        self.create_committee(4, parent_id=3)
        self.set_organization_management_level(None)
        self.set_committee_management_level([3])
        response = self.request(
            "committee.update",
            {
                "id": 4,
                "parent_id": None,
            },
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action committee.update. Missing OrganizationManagementLevel: can_manage_organization",
            response.json["message"],
        )

    def test_update_unset_parent_with_orga_perm(self) -> None:
        self.create_committee(3)
        self.create_committee(4, parent_id=3)
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request(
            "committee.update",
            {
                "id": 4,
                "parent_id": None,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/4", {"parent_id": None, "all_parent_ids": None}
        )

    def test_update_set_ancestor_as_parent_with_ancestor_perm(self) -> None:
        self.create_committee(2)
        self.create_committee(3, parent_id=2)
        self.create_committee(4, parent_id=3)
        self.set_organization_management_level(None)
        self.set_committee_management_level([2])
        response = self.request(
            "committee.update",
            {
                "id": 4,
                "parent_id": 2,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "committee/2", {"child_ids": [3, 4], "all_child_ids": [3, 4]}
        )
        self.assert_model_exists("committee/4", {"parent_id": 2, "all_parent_ids": [2]})

    def test_update_add_forwarding_relations(
        self,
        fail_forward_from: bool = False,
        fail_forward_to: bool = False,
        fail_remove: bool = False,
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
                },
                "committee/2": {
                    "forward_to_committee_ids": [1],
                },
            }
        )
        cmls = [1]
        to_fail = {2, 3, 4, 6}
        if not fail_remove:
            cmls.append(2)
            to_fail.remove(2)
        if not fail_forward_to:
            cmls.extend([3, 5])
            to_fail.remove(3)
            to_fail.remove(6)
        if not fail_forward_from:
            cmls.append(4)
            to_fail.remove(4)
        self.set_committee_management_level(cmls)
        self.set_organization_management_level(None)
        response = self.request(
            "committee.update",
            {
                "id": 1,
                "forward_to_committee_ids": [3, 6],
                "receive_forwardings_from_committee_ids": [2, 4],
            },
        )
        if to_fail:
            self.assert_status_code(response, 403)
            msg: str = response.json["message"]
            self.assertIn(
                "You are not allowed to perform action committee.update. Missing permissions: OrganizationManagementLevel can_manage_organization in organization 1 or CommitteeManagementLevel can_manage in committee",
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
                "committee/1",
                {
                    "forward_to_committee_ids": [3, 6],
                    "receive_forwardings_from_committee_ids": [2, 4],
                },
            )

    def test_update_add_forwarding_relations_fail_forward_to(self) -> None:
        self.test_update_add_forwarding_relations(fail_forward_to=True)

    def test_update_add_forwarding_relations_fail_forward_from(self) -> None:
        self.test_update_add_forwarding_relations(fail_forward_from=True)

    def test_update_add_forwarding_relations_fail_forward_to_and_from(self) -> None:
        self.test_update_add_forwarding_relations(
            fail_forward_to=True, fail_forward_from=True
        )

    def test_update_add_forwarding_relations_fail_remove_a_forward(self) -> None:
        self.test_update_add_forwarding_relations(fail_remove=True)

    def test_update_add_forwarding_relations_fail_forward_all(self) -> None:
        self.test_update_add_forwarding_relations(
            fail_forward_to=True, fail_forward_from=True, fail_remove=True
        )
