from tests.system.action.base import BaseActionTestCase


class CommitteeImportMeeting(BaseActionTestCase):
    def test_no_meeting_collection(self) -> None:
        self.set_models(
            {
                "committee/1": {},
            }
        )
        response = self.request(
            "committee.import_meeting", {"id": 1, "meeting_json": {"meeting": []}}
        )
        self.assert_status_code(response, 400)
        assert (
            "Need exact one meeting in meeting collection." in response.json["message"]
        )

    def test_too_many_meeting_collections(self) -> None:
        self.set_models(
            {
                "committee/1": {},
            }
        )
        response = self.request(
            "committee.import_meeting",
            {"id": 1, "meeting_json": {"meeting": [{"id": 1}, {"id": 2}]}},
        )
        self.assert_status_code(response, 400)
        assert (
            "Need exact one meeting in meeting collection." in response.json["message"]
        )

    def test_include_organization(self) -> None:
        self.set_models(
            {
                "committee/1": {},
            }
        )
        response = self.request(
            "committee.import_meeting",
            {
                "id": 1,
                "meeting_json": {"meeting": [{"id": 1}], "organization": [{"id": 1}]},
            },
        )
        self.assert_status_code(response, 400)
        assert "organization must be empty." in response.json["message"]

    def test_not_empty_password(self) -> None:
        self.set_models(
            {
                "committee/1": {},
            }
        )
        response = self.request(
            "committee.import_meeting",
            {
                "id": 1,
                "meeting_json": {
                    "meeting": [{"id": 1}],
                    "user": [{"id": 1, "password": "test"}],
                },
            },
        )
        self.assert_status_code(response, 400)
        assert "User password must be an empty string." in response.json["message"]

    def test_save_meeting(self) -> None:
        self.set_models(
            {
                "committee/1": {},
            }
        )
        response = self.request(
            "committee.import_meeting",
            {
                "id": 1,
                "meeting_json": {
                    "meeting": [
                        {
                            "id": 1,
                            "name": "Test",
                            "description": "blablabla",
                            "committee_id": 1,
                            "default_group_id": 1,
                            "motions_default_amendment_workflow_id": 1,
                            "motions_default_statute_amendment_workflow_id": 1,
                            "motions_default_workflow_id": 1,
                            "projector_countdown_default_time": 60,
                            "projector_countdown_warning_time": 60,
                            "reference_projector_id": 1,
                        }
                    ],
                    "user": [{"id": 2, "password": "", "username": "test"}],
                },
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting/1", {"name": "Test", "description": "blablabla"}
        )
        self.assert_model_exists("user/2", {"username": "test"})
