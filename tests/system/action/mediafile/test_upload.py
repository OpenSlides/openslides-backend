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
        mediafile = self.assert_model_exists(
            "mediafile/1",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 110,
                "filename": filename,
                "file": None,
                "mimetype": "text/plain",
                "filesize": 12,
                "list_of_speakers_id": 1,
                "is_public": True,
            },
        )
        assert mediafile.get("create_timestamp", 0) >= start_time
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

    def test_create_media_access_group(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_DsJFXoot",
                    "is_active_in_organization_id": 1,
                    "group_ids": [1],
                },
                "group/1": {"meeting_id": 110, "name": "grp1"},
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
                "access_group_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/11",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 110,
                "filename": "fn_jumbo.txt",
                "file": None,
                "is_public": False,
                "access_group_ids": [1],
                "inherited_access_group_ids": [1],
            },
        )
        self.media.upload_mediafile.assert_called_with(file_content, 11, "text/plain")
        self.assert_model_exists(
            "group/1",
            {
                "mediafile_access_group_ids": [11],
                "mediafile_inherited_access_group_ids": [11],
            },
        )

    def test_create_media_directory_group(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_DsJFXoot",
                    "is_active_in_organization_id": 1,
                    "group_ids": [1],
                },
                "group/1": {"meeting_id": 110, "name": "grp1"},
                "mediafile/10": {
                    "title": "title_CgKPfByo",
                    "is_directory": True,
                    "inherited_access_group_ids": [1],
                    "is_public": False,
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
        self.assert_model_exists(
            "mediafile/11",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 110,
                "filename": "fn_jumbo.txt",
                "file": None,
                "is_public": False,
                "access_group_ids": [],
                "inherited_access_group_ids": [1],
            },
        )
        self.media.upload_mediafile.assert_called_with(file_content, 11, "text/plain")
        self.assert_model_exists(
            "group/1", {"mediafile_inherited_access_group_ids": [11]}
        )

    def test_create_media_both_groups(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_DsJFXoot",
                    "is_active_in_organization_id": 1,
                    "group_ids": [1, 2],
                },
                "group/1": {"meeting_id": 110, "name": "grp1"},
                "group/2": {"meeting_id": 110, "name": "grp2"},
                "mediafile/10": {
                    "title": "title_CgKPfByo",
                    "is_directory": True,
                    "inherited_access_group_ids": [1],
                    "is_public": False,
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
                "access_group_ids": [1, 2],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/11",
            {
                "title": "title_xXRGTLAJ",
                "meeting_id": 110,
                "filename": "fn_jumbo.txt",
                "file": None,
                "is_public": False,
                "access_group_ids": [1, 2],
                "inherited_access_group_ids": [1],
            },
        )
        self.media.upload_mediafile.assert_called_with(file_content, 11, "text/plain")
        self.assert_model_exists(
            "group/1",
            {
                "mediafile_access_group_ids": [11],
                "mediafile_inherited_access_group_ids": [11],
            },
        )
        self.assert_model_exists("group/2", {"mediafile_access_group_ids": [11]})
