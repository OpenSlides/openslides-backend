from tests.system.action.base import BaseActionTestCase


class CommitteeDeleteActionTest(BaseActionTestCase):
    COMMITTEE_ID = 1
    COMMITTEE_FQID = "committee/1"

    def create_data(self) -> None:
        self.set_models(
            {
                "organisation/1": {"committee_ids": [self.COMMITTEE_ID]},
                "user/20": {"committee_ids": [self.COMMITTEE_ID]},
                "user/21": {"committee_ids": [self.COMMITTEE_ID]},
                self.COMMITTEE_FQID: {
                    "organisation_id": 1,
                    "user_ids": [20, 21],
                },
            }
        )

    def test_delete_correct(self) -> None:
        self.create_data()
        response = self.request("committee.delete", {"id": self.COMMITTEE_ID})

        self.assert_status_code(response, 200)
        self.assert_model_deleted(self.COMMITTEE_FQID)
        self.assert_model_exists("user/20", {"committee_ids": []})
        self.assert_model_exists("user/21", {"committee_ids": []})
        self.assert_model_exists("organisation/1", {"committee_ids": []})

    def test_delete_wrong_id(self) -> None:
        self.create_data()
        response = self.request("committee.delete", {"id": 2})
        self.assert_status_code(response, 400)
        self.assertIn("Model 'committee/2' does not exist.", response.json["message"])
        self.assert_model_exists(self.COMMITTEE_FQID)

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

    def test_delete_no_permission(self) -> None:
        self.create_data()
        self.set_models(
            {"user/1": {"organisation_management_level": "can_manage_users"}}
        )

        response = self.request("committee.delete", {"id": self.COMMITTEE_ID})
        self.assert_status_code(response, 403)
        assert (
            "Missing OrganisationManagementLevel: can_manage_organisation"
            in response.json["message"]
        )

    def test_delete_permission(self) -> None:
        self.create_data()
        self.set_models(
            {"user/1": {"organisation_management_level": "can_manage_organisation"}}
        )

        response = self.request("committee.delete", {"id": self.COMMITTEE_ID})
        self.assert_status_code(response, 200)
        self.assert_model_deleted(self.COMMITTEE_FQID)
