from tests.system.action.base import BaseActionTestCase


class MeetingMediafileCreate(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_meeting()
        self.set_models(
            {"mediafile/10": {"title": "hOi", "owner_id": "organization/1"}}
        )
        test_dict = {
            "mediafile_id": 10,
            "meeting_id": 1,
            "access_group_ids": [2, 3],
            "inherited_access_group_ids": [2],
            "is_public": False,
        }
        response = self.request("meeting_mediafile.create", test_dict)
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_mediafile/1", test_dict)
        self.assert_model_exists("mediafile/10", {"meeting_mediafile_ids": [1]})

    def test_create_existing(self) -> None:
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
            "mediafile_id": 10,
            "meeting_id": 1,
            "is_public": True,
        }
        response = self.request("meeting_mediafile.create", test_dict)
        self.assert_status_code(response, 400)
        self.assertIn(
            "MeetingMediafile instance with mediafile 10 and meeting 1 already exists",
            response.json["message"],
        )
