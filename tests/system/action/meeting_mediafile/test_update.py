from tests.system.action.base import BaseActionTestCase


class MeetingMediafileUpdate(BaseActionTestCase):
    def test_update(self) -> None:
        self.create_meeting()
        self.set_models(
            {
                "mediafile/10": {
                    "title": "hOi",
                    "owner_id": "meeting/1",
                },
                "meeting_mediafile/2": {
                    "meeting_id": 1,
                    "mediafile_id": 10,
                    "is_public": True,
                },
            }
        )
        test_dict = {
            "id": 2,
            "access_group_ids": [2],
            "inherited_access_group_ids": [2],
            "is_public": False,
        }
        response = self.request("meeting_mediafile.update", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_mediafile/2", test_dict)
