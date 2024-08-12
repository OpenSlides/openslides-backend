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
        self.assert_model_deleted("meeting_mediafile/2")
