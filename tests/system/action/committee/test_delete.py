from tests.system.action.base import BaseActionTestCase


class CommitteeDeleteActionTest(BaseActionTestCase):
    COMMITTEE_ID = 1
    COMMITTEE_FQID = "committee/1"

    def create_data(self) -> None:
        self.set_models(
            {
                "organisation/1": {"name": "test_organisation1"},
                "user/20": {"username": "test_user20"},
                "user/21": {"username": "test_user21"},
            }
        )

        self.request(
            "committee.create",
            {
                "name": "committee_testname",
                "organisation_id": 1,
                "description": "<p>Test description</p>",
                "member_ids": [20],
                "manager_ids": [21],
            },
        )

    def test_delete_correct(self) -> None:
        self.create_data()
        response = self.request("committee.delete", {"id": self.COMMITTEE_ID})

        self.assert_status_code(response, 200)
        self.assert_model_deleted(self.COMMITTEE_FQID)
        self.assert_model_exists(
            "user/20", {"member_in_meeting_ids": None, "manager_in_meeting_ids": None}
        )
        self.assert_model_exists(
            "user/21", {"member_in_meeting_ids": None, "manager_in_meeting_ids": None}
        )

    def test_delete_wrong_id(self) -> None:
        self.create_data()
        response = self.request("committee.delete", {"id": 2})
        self.assert_status_code(response, 400)
        self.assertIn("Model 'committee/2' does not exist.", response.json["message"])
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertEqual(model.get("name"), "committee_testname")

    def test_delete_protected_by_meeting(self) -> None:
        self.create_data()
        self.create_model(
            "meeting/22", {"name": "name_meeting_22", "committee_id": self.COMMITTEE_ID}
        )
        self.update_model(self.COMMITTEE_FQID, {"meeting_ids": [22]})

        response = self.request("committee.delete", {"id": self.COMMITTEE_ID})

        self.assert_status_code(response, 400)
        self.assert_model_exists(self.COMMITTEE_FQID, {"meeting_ids": [22]})
        self.assertIn(
            "meeting/22",
            response.json["message"],
        )
