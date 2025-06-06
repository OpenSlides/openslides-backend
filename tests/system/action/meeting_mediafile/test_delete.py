from tests.system.action.base import BaseActionTestCase


class MeetingMediafileDelete(BaseActionTestCase):
    def test_delete(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "meeting/1": {"mediafile_ids": [10], "meeting_mediafile_ids": [2]},
                "mediafile/10": {
                    "title": "hOi",
                    "meeting_mediafile_ids": [2],
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/2": {
                    "meeting_id": 1,
                    "access_group_ids": [],
                    "inherited_access_group_ids": [],
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
        self.set_models(
            {
                "meeting/1": {
                    "mediafile_ids": [10],
                    "meeting_mediafile_ids": [2],
                    "list_of_speakers_ids": [3],
                    "all_projection_ids": [4],
                    "logo_projector_main_id": 2,
                },
                "group/1": {
                    "name": "X",
                    "meeting_id": 1,
                    "meeting_mediafile_access_group_ids": [2],
                    "meeting_mediafile_inherited_access_group_ids": [2],
                },
                "mediafile/10": {
                    "title": "hOi",
                    "meeting_mediafile_ids": [2],
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/2": {
                    "meeting_id": 1,
                    "access_group_ids": [1],
                    "inherited_access_group_ids": [1],
                    "mediafile_id": 10,
                    "is_public": False,
                    "list_of_speakers_id": 3,
                    "projection_ids": [4],
                    "attachment_ids": ["topic/5"],
                    "used_as_logo_projector_main_in_meeting_id": 1,
                },
                "list_of_speakers/3": {
                    "meeting_id": 1,
                    "content_object_id": "meeting_mediafile/2",
                },
                "projection/4": {
                    "meeting_id": 1,
                    "content_object_id": "meeting_mediafile/2",
                },
                "topic/5": {"meeting_id": 1, "attachment_meeting_mediafile_ids": [2]},
            }
        )
        response = self.request("meeting_mediafile.delete", {"id": 2})
        self.assert_status_code(response, 200)
        self.assert_model_not_exists("meeting_mediafile/2")
        self.assert_model_exists("mediafile/10", {"meeting_mediafile_ids": []})
        self.assert_model_exists(
            "group/1",
            {
                "meeting_mediafile_access_group_ids": [],
                "meeting_mediafile_inherited_access_group_ids": [],
            },
        )
        self.assert_model_not_exists("list_of_speakers/3")
        self.assert_model_not_exists("projection/4")
        self.assert_model_exists("topic/5", {"attachment_meeting_mediafile_ids": []})
        self.assert_model_exists(
            "meeting/1", {"meeting_mediafile_ids": [], "logo_projector_main_id": None}
        )
