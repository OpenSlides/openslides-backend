import base64
from time import time

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MediafileUploadActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "fn_jumbo.txt"
        file_content = base64.b64encode(b"testtesttest").decode()
        start_time = round(time())
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 110,
                "filename": filename,
                "file": file_content,
            },
        )
        self.assert_status_code(response, 200)
        mediafile = self.get_model("mediafile/1")
        assert mediafile.get("title") == "title_xXRGTLAJ"
        assert mediafile.get("meeting_id") == 110
        assert mediafile.get("filename") == filename
        assert mediafile.get("file") is None
        assert mediafile.get("mimetype") == "text/plain"
        assert mediafile.get("filesize") == 12
        assert mediafile.get("list_of_speakers_id") == 1
        assert mediafile.get("create_timestamp") >= start_time
        assert not mediafile.get("is_directory")
        self.media.upload_mediafile.assert_called_with(file_content, 1, "text/plain")

    def test_create_cannot_guess_mimetype(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 110,
                "filename": "fn_jumbo.tasdde",
                "file": file_content,
            },
        )
        self.assert_status_code(response, 400)
        assert "Cannot guess mimetype for fn_jumbo.tasdde." in response.json.get(
            "message", ""
        )
        self.assert_model_not_exists("mediafile/1")
        self.media.upload_mediafile.assert_not_called()

    def test_create_access_group(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_DsJFXoot",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/10": {
                    "title": "title_CgKPfByo",
                    "is_directory": True,
                    "inherited_access_group_ids": [],
                    "is_public": True,
                    "meeting_id": 110,
                },
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 110,
                "filename": "fn_jumbo.txt",
                "file": file_content,
                "parent_id": 10,
                "access_group_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        mediafile = self.get_model("mediafile/11")
        assert mediafile.get("title") == "title_xXRGTLAJ"
        assert mediafile.get("meeting_id") == 110
        assert mediafile.get("filename") == "fn_jumbo.txt"
        assert mediafile.get("file") is None
        assert mediafile.get("is_public") is True
        assert mediafile.get("inherited_access_group_ids") == []
        self.media.upload_mediafile.assert_called_with(file_content, 11, "text/plain")

    def test_upload_pdf(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "test.pdf"
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 110,
                "filename": filename,
                "file": file_content,
            },
        )
        self.assert_status_code(response, 200)
        mediafile = self.get_model("mediafile/1")
        # PyPDF assumes the file is encrypted since it is not valid
        assert mediafile.get("pdf_information") == {"pages": 0, "encrypted": True}
        self.media.upload_mediafile.assert_called_with(
            file_content, 1, "application/pdf"
        )

    def test_error_in_resource_upload(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "raises_upload_error.swf"
        used_mimetype = "application/x-shockwave-flash"
        raw_content = b"raising upload error in mock"
        file_content = base64.b64encode(raw_content).decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 110,
                "filename": filename,
                "file": file_content,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn("Mocked error on media service upload", response.json["message"])
        self.assert_model_not_exists("resource/1")
        self.media.upload_mediafile.assert_called_with(file_content, 1, used_mimetype)

    def test_without_filename(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 110,
                "file": file_content,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['title', 'meeting_id', 'filename', 'file'] properties",
            response.json["message"],
        )

    def test_upload_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 1,
                "filename": "fn_jumbo.txt",
                "file": base64.b64encode(b"testtesttest").decode(),
            },
        )

    def test_upload_permissions(self) -> None:
        self.base_permission_test(
            {},
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 1,
                "filename": "fn_jumbo.txt",
                "file": base64.b64encode(b"testtesttest").decode(),
            },
            Permissions.Mediafile.CAN_MANAGE,
        )

    def test_create_added_mimetype_ttf(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name", "is_active_in_organization_id": 1}
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 110,
                "filename": "fn_jumbo.ttf",
                "file": file_content,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("mediafile/1", {"mimetype": "font/ttf"})
