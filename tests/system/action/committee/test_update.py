from tests.system.action.base import BaseActionTestCase


class CommitteeUpdateActionTest(BaseActionTestCase):
    COMMITTEE_ID = 1
    COMMITTEE_FQID = "committee/1"
    COMMITTEE_NAME = "committee_testname"
    COMMITTEE_ID_FORWARD = 2

    def create_data(self) -> None:
        self.create_model("organisation/1", {"name": "test_organisation1"})
        self.create_model("user/20", {"username": "test_user20"})
        self.create_model("user/21", {"username": "test_user21"})

        self.client.post(
            "/",
            json=[
                {
                    "action": "committee.create",
                    "data": [
                        {
                            "name": self.COMMITTEE_NAME,
                            "organisation_id": 1,
                            "description": "<p>Test description</p>",
                            "member_ids": [20],
                            "manager_ids": [21],
                        }
                    ],
                }
            ],
        )

        self.client.post(
            "/",
            json=[
                {
                    "action": "committee.create",
                    "data": [
                        {
                            "name": "forwarded_committee",
                            "organisation_id": 1,
                        }
                    ],
                }
            ],
        )

    def create_meetings(self) -> None:
        self.create_model("meeting/200", {})
        self.create_model("meeting/201", {})

    def test_update_correct(self) -> None:
        self.create_data()
        new_name = "committee_testname_updated"
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.update",
                    "data": [{"id": self.COMMITTEE_ID, "name": new_name}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertEqual(model.get("name"), new_name)

    def test_update_everything_correct(self) -> None:
        self.create_data()
        self.create_meetings()
        new_name = "committee_testname_updated"
        new_description = "<p>New Test description</p>"
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.update",
                    "data": [
                        {
                            "id": self.COMMITTEE_ID,
                            "name": new_name,
                            "description": new_description,
                            "member_ids": [21],
                            "manager_ids": [20],
                            "forward_to_committee_ids": [self.COMMITTEE_ID_FORWARD],
                            "template_meeting_id": 200,
                            "default_meeting_id": 201,
                        },
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertEqual(model.get("name"), new_name)
        self.assertEqual(model.get("description"), new_description)
        self.assertEqual(model.get("member_ids"), [21])
        self.assertEqual(model.get("manager_ids"), [20])
        self.assertEqual(
            model.get("forward_to_committee_ids"), [self.COMMITTEE_ID_FORWARD]
        )
        self.assertEqual(model.get("template_meeting_id"), 200)
        self.assertEqual(model.get("default_meeting_id"), 201)

    def test_update_wrong_member_ids(self) -> None:
        self.create_data()
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.update",
                    "data": [
                        {
                            "id": self.COMMITTEE_ID,
                            "member_ids": [30],
                        },
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertEqual(model.get("member_ids"), [20])
        self.assertIn(
            "Model 'user/30' does not exist.",
            response.json["message"],
        )

    def test_update_wrong_manager_ids(self) -> None:
        self.create_data()
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.update",
                    "data": [
                        {
                            "id": self.COMMITTEE_ID,
                            "manager_ids": [20, 30],
                        },
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertEqual(model.get("manager_ids"), [21])
        self.assertIn(
            "Model 'user/30' does not exist.",
            response.json["message"],
        )

    def test_update_wrong_forward_committee(self) -> None:
        self.create_data()
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.update",
                    "data": [
                        {
                            "id": self.COMMITTEE_ID,
                            "forward_to_committee_ids": [101],
                        },
                    ],
                }
            ],
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
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.update",
                    "data": [
                        {
                            "id": self.COMMITTEE_ID,
                            "template_meeting_id": 299,
                        },
                    ],
                }
            ],
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
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.update",
                    "data": [
                        {
                            "id": self.COMMITTEE_ID,
                            "default_meeting_id": 299,
                        },
                    ],
                }
            ],
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
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "committee.update",
                    "data": [{"id": 200, "name": "xxxxx"}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model(self.COMMITTEE_FQID)
        self.assertEqual(model.get("name"), self.COMMITTEE_NAME)
