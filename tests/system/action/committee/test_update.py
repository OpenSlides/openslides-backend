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
                "organisation/1": {"name": "test_organisation1"},
                "user/20": {"username": "test_user20"},
                "user/21": {"username": "test_user21"},
            }
        )

        response = self.request(
            "committee.create",
            {
                "name": self.COMMITTEE_NAME,
                "organisation_id": 1,
                "description": "<p>Test description</p>",
                "user_ids": [20, 21],
            },
        )
        self.assert_status_code(response, 200)

        response = self.request(
            "committee.create",
            {
                "name": "forwarded_committee",
                "organisation_id": 1,
            },
        )
        self.assert_status_code(response, 200)

    def create_meetings(self) -> None:
        self.create_model("meeting/200")
        self.create_model("meeting/201")

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
                "organisation/1": {
                    "name": "test_organisation1",
                    "committee_ids": [1, 2, 3],
                },
                "committee/1": {"name": "committee_1", "organisation_id": 1},
                "committee/2": {"name": "committee_2", "organisation_id": 1},
                "committee/3": {"name": "committee_3", "organisation_id": 1},
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

    def test_update_complex_1(self) -> None:
        """A->C and B->C exist, test that the request for C with {B, D}->C works and sets the reverse relations on A and D correctly."""
        self.set_models(
            {
                "organisation/1": {
                    "name": "test_organisation1",
                    "committee_ids": [1, 2, 3, 4],
                },
                "committee/1": {
                    "name": "committee_A",
                    "organisation_id": 1,
                    "forward_to_committee_ids": [3],
                },
                "committee/2": {
                    "name": "committee_B",
                    "organisation_id": 1,
                    "forward_to_committee_ids": [3],
                },
                "committee/3": {
                    "name": "committee_C",
                    "organisation_id": 1,
                    "receive_forwardings_from_committee_ids": [1, 2],
                },
                "committee/4": {"name": "committee_D", "organisation_id": 1},
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
                "organisation/1": {
                    "name": "test_organisation1",
                    "committee_ids": [1, 2, 3, 4],
                },
                "committee/1": {
                    "name": "committee_A",
                    "organisation_id": 1,
                    "receive_forwardings_from_committee_ids": [3],
                },
                "committee/2": {
                    "name": "committee_B",
                    "organisation_id": 1,
                    "receive_forwardings_from_committee_ids": [3],
                },
                "committee/3": {
                    "name": "committee_C",
                    "organisation_id": 1,
                    "forward_to_committee_ids": [1, 2],
                },
                "committee/4": {"name": "committee_D", "organisation_id": 1},
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
                "organisation/1": {
                    "name": "test_organisation1",
                    "committee_ids": [1, 2, 3],
                },
                "committee/1": {
                    "name": "committee_A",
                    "organisation_id": 1,
                    "receive_forwardings_from_committee_ids": [3],
                },
                "committee/2": {
                    "name": "committee_B",
                    "organisation_id": 1,
                    "receive_forwardings_from_committee_ids": [3],
                },
                "committee/3": {
                    "name": "committee_C",
                    "organisation_id": 1,
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
                "organisation/1": {
                    "name": "test_organisation1",
                    "committee_ids": [1],
                },
                "committee/1": {
                    "name": "committee_A",
                    "organisation_id": 1,
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
                "organisation/1": {
                    "name": "test_organisation1",
                    "committee_ids": [1, 2, 3, 4],
                },
                "committee/1": {
                    "name": "committee_A",
                    "organisation_id": 1,
                    "forward_to_committee_ids": [2],
                },
                "committee/2": {
                    "name": "committee_B",
                    "organisation_id": 1,
                    "receive_forwardings_from_committee_ids": [1],
                    "forward_to_committee_ids": [3, 4],
                },
                "committee/3": {
                    "name": "committee_C",
                    "organisation_id": 1,
                    "receive_forwardings_from_committee_ids": [2],
                },
                "committee/4": {
                    "name": "committee_D",
                    "organisation_id": 1,
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

    def test_update_wrong_id(self) -> None:
        self.create_data()
        response = self.request("committee.update", {"id": 200, "name": "xxxxx"})
        self.assert_status_code(response, 400)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertEqual(model.get("name"), self.COMMITTEE_NAME)

    def test_update_group_a_no_permission(self) -> None:
        self.create_data()
        self.set_models(
            {"user/1": {"organisation_management_level": "can_manage_organisation"}}
        )
        response = self.request(
            "committee.update", {"id": 1, "name": "test", "description": "blablabla"}
        )
        self.assert_status_code(response, 403)
        assert "Not manager" in response.json["message"]

    def test_update_group_a_permission(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/1": {"organisation_management_level": "can_manage_organisation"},
                "committee/1": {"manager_ids": [1]},
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
                "user/1": {"organisation_management_level": "can_manage_users"},
                "committee/1": {"manager_ids": [1]},
            }
        )
        response = self.request("committee.update", {"id": 1, "member_ids": [1, 20]})
        self.assert_status_code(response, 403)
        assert "Missing can_manage_organisation" in response.json["message"]

    def test_update_group_b_permission(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/1": {"organisation_management_level": "can_manage_organisation"},
                "committee/1": {"manager_ids": [1]},
            }
        )
        response = self.request("committee.update", {"id": 1, "member_ids": [1, 20]})
        self.assert_status_code(response, 200)

    def test_update_group_c_no_permission(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/1": {"organisation_management_level": "can_manage_users"},
                "organisation_tag/12": {"organisation_id": 1},
            }
        )
        response = self.request(
            "committee.update", {"id": 1, "organisation_tag_ids": [12]}
        )
        self.assert_status_code(response, 403)
        assert (
            "Missing can_manage_organisation and not manager."
            in response.json["message"]
        )

    def test_update_group_c_permission_1(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/1": {"organisation_management_level": "can_manage_organisation"},
                "committee/1": {"manager_ids": [20]},
                "organisation_tag/12": {"organisation_id": 1},
            }
        )
        response = self.request(
            "committee.update", {"id": 1, "organisation_tag_ids": [12]}
        )
        self.assert_status_code(response, 200)

    def test_update_group_c_permission_2(self) -> None:
        self.create_data()
        self.set_models(
            {
                "user/1": {"organisation_management_level": "can_manage_users"},
                "committee/1": {"manager_ids": [1]},
                "organisation_tag/12": {"organisation_id": 1},
            }
        )
        response = self.request(
            "committee.update", {"id": 1, "organisation_tag_ids": [12]}
        )
        self.assert_status_code(response, 200)
