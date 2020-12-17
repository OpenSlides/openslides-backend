from tests.system.action.base import BaseActionTestCase


class CommitteeCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        self.create_model("user/20", {"username": "test_user20"})
        self.create_model("user/21", {"username": "test_user21"})
        self.create_model("user/22", {"username": "test_user22"})
        committee_name = "test_committee1"
        description = "<p>Test Committee</p>"

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.create",
                    "data": [
                        {
                            "name": committee_name,
                            "organisation_id": 1,
                            "description": description,
                            "member_ids": [20, 21],
                            "manager_ids": [20, 22],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("committee/1")
        assert model.get("name") == committee_name
        assert model.get("description") == description
        assert model.get("meeting_ids") is None
        assert model.get("member_ids") == [20, 21]
        assert model.get("manager_ids") == [20, 22]

    def test_create_only_required(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        committee_name = "test_committee1"

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.create",
                    "data": [{"name": committee_name, "organisation_id": 1}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("committee/1")
        assert model.get("name") == committee_name

    def test_create_wrong_field(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.create",
                    "data": [
                        {
                            "name": "test_committee_name",
                            "organisation_id": 1,
                            "wrong_field": "test",
                        }
                    ],
                }
            ],
        )

        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {\\'wrong_field\\'} properties",
            str(response.data),
        )
        self.assert_model_not_exists("committee/1")

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "committee.create", "data": [{}]}]
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain [\\'organisation_id\\', \\'name\\'] properties",
            str(response.data),
        )
        self.assert_model_not_exists("committee/1")

    def test_create_empty_data_list(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "committee.create", "data": []}]
        )
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("committee/1")

    def test_not_existing_organisation(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.create",
                    "data": [{"organisation_id": 1, "name": "test_name"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Model \\'organisation/1\\' does not exist.",
            str(response.data),
        )
        self.assert_model_not_exists("committee/1")

    def test_not_existing_user(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        committee_name = "test_committee1"

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.create",
                    "data": [
                        {
                            "name": committee_name,
                            "organisation_id": 1,
                            "member_ids": [20, 21],
                            "manager_ids": [20, 22],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn("does not exist", str(response.data))
        self.assert_model_not_exists("committee/1")
