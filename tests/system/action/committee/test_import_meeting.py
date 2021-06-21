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
