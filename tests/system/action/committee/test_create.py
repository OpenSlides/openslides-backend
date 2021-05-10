from tests.system.action.base import BaseActionTestCase


class CommitteeCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models(
            {
                "organisation/1": {"name": "test_organisation1"},
                "user/20": {"username": "test_user20"},
                "user/21": {"username": "test_user21"},
            }
        )
        committee_name = "test_committee1"
        description = "<p>Test Committee</p>"

        response = self.request(
            "committee.create",
            {
                "name": committee_name,
                "organisation_id": 1,
                "description": description,
                "user_ids": [20, 21],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("committee/1")
        assert model.get("name") == committee_name
        assert model.get("description") == description
        assert model.get("meeting_ids") is None
        assert model.get("user_ids") == [20, 21]

    def test_create_only_required(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        committee_name = "test_committee1"

        response = self.request(
            "committee.create", {"name": committee_name, "organisation_id": 1}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("committee/1")
        assert model.get("name") == committee_name

    def test_create_wrong_field(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})

        response = self.request(
            "committee.create",
            {
                "name": "test_committee_name",
                "organisation_id": 1,
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
            "data must contain ['organisation_id', 'name'] properties",
            response.json["message"],
        )
        self.assert_model_not_exists("committee/1")

    def test_create_empty_data_list(self) -> None:
        response = self.request_multi("committee.create", [])
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("committee/1")

    def test_not_existing_organisation(self) -> None:
        response = self.request(
            "committee.create", {"organisation_id": 1, "name": "test_name"}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model 'organisation/1' does not exist.",
            response.json["message"],
        )
        self.assert_model_not_exists("committee/1")

    def test_not_existing_user(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        committee_name = "test_committee1"

        response = self.request(
            "committee.create",
            {
                "name": committee_name,
                "organisation_id": 1,
                "user_ids": [20, 21],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn("does not exist", response.json["message"])
        self.assert_model_not_exists("committee/1")
