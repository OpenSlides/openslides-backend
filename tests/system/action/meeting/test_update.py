from typing import Any, Dict

from tests.system.action.base import BaseActionTestCase


class MeetingUpdateActionTest(BaseActionTestCase):
    def basic_test(self, datapart: Dict[str, Any]) -> Dict[str, Any]:
        self.create_model("committee/1", {"name": "test_committee"})
        self.create_model("group/1", {})
        self.create_model(
            "meeting/1",
            {
                "name": "test_name",
                "committee_id": 1,
                "default_group_id": 1,
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "meeting.update",
                    "data": [
                        {
                            "id": 1,
                            **datapart,
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        meeting = self.get_model("meeting/1")
        assert meeting.get("name") == "test_name"
        assert meeting.get("committee_id") == 1
        return meeting

    def test_update_some_fields_export(self) -> None:
        meeting = self.basic_test(
            {
                "export_csv_encoding": "utf-8",
                "export_csv_separator": ",",
                "export_pdf_pagenumber_alignment": "center",
                "export_pdf_fontsize": 11,
                "export_pdf_pagesize": "A4",
            }
        )
        assert meeting.get("export_csv_encoding") == "utf-8"
        assert meeting.get("export_csv_separator") == ","
        assert meeting.get("export_pdf_pagenumber_alignment") == "center"
        assert meeting.get("export_pdf_fontsize") == 11
        assert meeting.get("export_pdf_pagesize") == "A4"

    def test_update_some_fields_user_email(self) -> None:
        meeting = self.basic_test(
            {
                "users_email_sender": "test@example.com",
                "users_email_replyto": "test2@example.com",
                "users_email_subject": "blablabla",
                "users_email_body": "testtesttest",
            }
        )
        assert meeting.get("users_email_sender") == "test@example.com"
        assert meeting.get("users_email_replyto") == "test2@example.com"
        assert meeting.get("users_email_subject") == "blablabla"
        assert meeting.get("users_email_body") == "testtesttest"

    def test_single_relation_guest_ids(self) -> None:
        self.create_model("user/3", {})
        meeting = self.basic_test({"guest_ids": [3]})
        assert meeting.get("guest_ids") == [3]
        user_3 = self.get_model("user/3")
        assert user_3.get("guest_meeting_ids") == [1]
