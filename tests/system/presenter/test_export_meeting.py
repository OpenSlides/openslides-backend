from .base import BasePresenterTestCase


class TestExportMeeting(BasePresenterTestCase):
    def test_export_meeting_example_data(self) -> None:
        self.load_example_data()
        status_code, data = self.request("export_meeting", {"meeting_id": 1})
        self.assertEqual(status_code, 200)
        export = data["export"]
        assert len(export["group"]) == 5
        assert len(export["personal_note"]) == 1
        assert len(export["tag"]) == 3
        assert len(export["agenda_item"]) == 15
        assert len(export["list_of_speakers"]) == 18
        assert len(export["speaker"]) == 13
        assert len(export["topic"]) == 8
        assert len(export["motion"]) == 4
        assert len(export["motion_submitter"]) == 4
        assert len(export["motion_comment"]) == 1
        assert len(export["motion_comment_section"]) == 1
        assert len(export["motion_category"]) == 2
        assert len(export["motion_block"]) == 1
        assert len(export["motion_change_recommendation"]) == 2
        assert len(export["motion_state"]) == 14
        assert len(export["motion_workflow"]) == 2
        assert len(export["motion_statute_paragraph"]) == 0
        assert len(export["poll"]) == 5
        assert len(export["option"]) == 13
        assert len(export["vote"]) == 9
        assert len(export["assignment"]) == 2
        assert len(export["assignment_candidate"]) == 5
        assert len(export["mediafile"]) == 3
        assert len(export["projector"]) == 2
        assert len(export["projection"]) == 4
        assert len(export["projector_message"]) == 1
        assert len(export["projector_countdown"]) == 2
        assert len(export["chat_group"]) == 2
        assert len(export["meeting"]) == 1

    def test_export_meeting_meta_field_handling(self) -> None:
        self.set_models(
            {
                "meeting/10": {"name": "test", "tag_ids": [11, 12, 13]},
                "tag/11": {"meeting_id": 10, "name": "test_tag_1"},
                "tag/12": {"meeting_id": 10, "name": "test_tag_2"},
                "tag/13": {"meeting_id": 10, "name": "test_tag_3"},
            }
        )
        status_code, data = self.request("export_meeting", {"meeting_id": 10})
        self.assertEqual(status_code, 200)
        export = data["export"]
        assert len(export["meeting"]) == 1
        assert len(export["tag"]) == 3
        for tag in export["tag"]:
            assert "meta_position" not in tag
            assert "meta_deleted" not in tag
