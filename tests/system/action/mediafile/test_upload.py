import base64
from unittest.mock import patch

from tests.system.action.base import BaseActionTestCase


class MediafileUploadActionTest(BaseActionTestCase):
    @patch("openslides_backend.action.mediafile.upload.Mediaservice")
    def test_create(self, mock) -> None:
        self.create_model("meeting/110", {"name": "name_DsJFXoot"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.upload",
                    "data": [
                        {
                            "title": "title_xXRGTLAJ",
                            "meeting_id": 110,
                            "filename": "fn_jumbo.txt",
                            "file": base64.b64encode(b"testtesttest").decode(),
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        mediafile = self.get_model("mediafile/1")
        assert mediafile.get("title") == "title_xXRGTLAJ"
        assert mediafile.get("meeting_id") == 110
        assert mediafile.get("filename") == "fn_jumbo.txt"
        assert mediafile.get("file") is None

    @patch("openslides_backend.action.mediafile.upload.Mediaservice")
    def test_create_cannot_guess_mimetype(self, mock) -> None:
        self.create_model("meeting/110", {"name": "name_DsJFXoot"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.upload",
                    "data": [
                        {
                            "title": "title_xXRGTLAJ",
                            "meeting_id": 110,
                            "filename": "fn_jumbo.tasdde",
                            "file": base64.b64encode(b"testtesttest").decode(),
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Cannot guess mimetype for fn_jumbo.tasdde." in str(response.data)

    @patch("openslides_backend.action.mediafile.upload.Mediaservice")
    def test_create_access_group(self, mock) -> None:
        self.create_model("meeting/110", {"name": "name_DsJFXoot"})
        self.create_model(
            "mediafile/10",
            {
                "title": "title_CgKPfByo",
                "is_directory": True,
                "inherited_access_group_ids": [],
                "has_inherited_access_groups": True,
                "meeting_id": 110,
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "mediafile.upload",
                    "data": [
                        {
                            "title": "title_xXRGTLAJ",
                            "meeting_id": 110,
                            "filename": "fn_jumbo.txt",
                            "file": base64.b64encode(b"testtesttest").decode(),
                            "parent_id": 10,
                            "access_group_ids": [],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        mediafile = self.get_model("mediafile/11")
        assert mediafile.get("title") == "title_xXRGTLAJ"
        assert mediafile.get("meeting_id") == 110
        assert mediafile.get("filename") == "fn_jumbo.txt"
        assert mediafile.get("file") is None
        assert mediafile.get("has_inherited_access_groups") is True
        assert mediafile.get("inherited_access_group_ids") == []
