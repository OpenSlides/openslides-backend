from tests.system.action.base import BaseActionTestCase


class MeetingMediafileDelete(BaseActionTestCase):
    def test_delete(self) -> None:
        self.create_meeting()
        self.create_mediafile(10, 1)
        self.set_models(
            {
                "meeting_mediafile/2": {
                    "meeting_id": 1,
                    "mediafile_id": 10,
                    "is_public": True,
                },
            }
        )
        response = self.request("meeting_mediafile.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting_mediafile/2")
        self.assert_model_exists("mediafile/10")

    def test_delete_complex(self) -> None:
        self.create_meeting()
        self.create_mediafile(10, 1)
        self.set_models(
            {
                "meeting/1": {
                    "logo_projector_main_id": 2,
                },
                "group/1": {
                    "name": "X",
                    "meeting_id": 1,
                    "meeting_mediafile_access_group_ids": [2],
                    "meeting_mediafile_inherited_access_group_ids": [2],
                },
                "meeting_mediafile/2": {
                    "meeting_id": 1,
                    "mediafile_id": 10,
                    "is_public": False,
                    "list_of_speakers_id": 3,
                    "attachment_ids": ["topic/5"],
                },
                "list_of_speakers/3": {
                    "meeting_id": 1,
                    "sequential_number": 3,
                    "content_object_id": "meeting_mediafile/2",
                },
                "projection/4": {
                    "meeting_id": 1,
                    "content_object_id": "meeting_mediafile/2",
                },
                "topic/5": {
                    "meeting_id": 1,
                    "sequential_number": 5,
                    "title": "pic me",
                },
                "agenda_item/6": {"content_object_id": "topic/5", "meeting_id": 1},
                "list_of_speakers/7": {
                    "content_object_id": "topic/5",
                    "sequential_number": 1,
                    "meeting_id": 1,
                },
            }
        )
        response = self.request("meeting_mediafile.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting_mediafile/2")
        self.assert_model_exists("mediafile/10", {"meeting_mediafile_ids": None})
        self.assert_model_exists(
            "group/1",
            {
                "meeting_mediafile_access_group_ids": None,
                "meeting_mediafile_inherited_access_group_ids": None,
            },
        )
        self.assert_model_not_exists("list_of_speakers/3")
        self.assert_model_not_exists("projection/4")
        self.assert_model_exists("topic/5", {"attachment_meeting_mediafile_ids": None})
        self.assert_model_exists(
            "meeting/1", {"meeting_mediafile_ids": None, "logo_projector_main_id": None}
        )
