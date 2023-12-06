import base64
from time import time

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
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
                "owner_id": "meeting/110",
                "filename": filename,
                "file": file_content,
            },
        )
        self.assert_status_code(response, 200)
        mediafile = self.assert_model_exists(
            "mediafile/1",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": filename,
                "file": None,
                "mimetype": "text/plain",
                "filesize": 12,
                "is_public": True,
            },
        )
        assert mediafile.get("create_timestamp", 0) >= start_time
        assert not mediafile.get("is_directory")
        self.media.upload_mediafile.assert_called_with(file_content, 1, "text/plain")

    def test_create_orga(self) -> None:
        filename = "fn_jumbo.txt"
        file_content = base64.b64encode(b"testtesttest").decode()
        start_time = round(time())
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": ONE_ORGANIZATION_FQID,
                "filename": filename,
                "file": file_content,
                "token": "web_logo",
            },
        )
        self.assert_status_code(response, 200)
        mediafile = self.assert_model_exists(
            "mediafile/1",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": ONE_ORGANIZATION_FQID,
                "file": None,
                "mimetype": "text/plain",
                "filesize": 12,
                "is_public": True,
                "is_directory": None,
            },
        )
        assert mediafile.get("create_timestamp", 0) >= start_time
        self.media.upload_mediafile.assert_called_with(file_content, 1, "text/plain")

    def test_create_orga_missing_token(self) -> None:
        filename = "fn_jumbo.txt"
        file_content = base64.b64encode(b"testtesttest").decode()
        start_time = round(time())
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": ONE_ORGANIZATION_FQID,
                "filename": filename,
                "file": file_content,
                "parent_id": None,
            },
        )
        self.assert_status_code(response, 200)
        mediafile = self.assert_model_exists(
            "mediafile/1",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": ONE_ORGANIZATION_FQID,
                "file": None,
                "mimetype": "text/plain",
                "filesize": 12,
                "is_public": True,
                "is_directory": None,
            },
        )
        assert mediafile.get("create_timestamp", 0) >= start_time
        self.media.upload_mediafile.assert_called_with(file_content, 1, "text/plain")

    def test_upload_orga_None_token(self) -> None:
        filename = "fn_jumbo.txt"
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": ONE_ORGANIZATION_FQID,
                "filename": filename,
                "file": file_content,
                "parent_id": None,
                "token": None,
            },
        )
        self.assert_status_code(response, 400)
        assert response.json["message"] == "Token should not be None."

    def test_create_cannot_guess_mimetype(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": "fn_jumbo.tasdde",
                "file": file_content,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "fn_jumbo.tasdde does not have a file extension that matches the determined mimetype text/plain."
            in response.json.get("message", "")
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
                    "owner_id": "meeting/110",
                },
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": "fn_jumbo.txt",
                "file": file_content,
                "parent_id": 10,
                "access_group_ids": [],
            },
        )
        self.assert_status_code(response, 200)
        mediafile = self.get_model("mediafile/11")
        assert mediafile.get("title") == "title_xXRGTLAJ"
        assert mediafile.get("owner_id") == "meeting/110"
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
        pdf_content = "JVBERi0xLjQKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZwovT3V0bGluZXMgMiAwIFIKL1BhZ2VzIDMgMCBSCj4+CmVuZG9iagoyIDAgb2JqCjw8IC9UeXBlIC9PdXRsaW5lcwovQ291bnQgMAo+PgplbmRvYmoKMyAwIG9iago8PCAvVHlwZSAvUGFnZXMKL0tpZHMgWyA0IDAgUiBdCi9Db3VudCAxCj4+CmVuZG9iago0IDAgb2JqCjw8IC9UeXBlIC9QYWdlCi9QYXJlbnQgMyAwIFIKL01lZGlhQm94IFsgMCAwIDYxMiA3OTIgXQovQ29udGVudHMgNSAwIFIKL1Jlc291cmNlcyA8PCAvUHJvY1NldCA2IDAgUgovRm9udCA8PCAvRjEgNyAwIFIgPj4KPj4KPj4KZW5kb2JqCjUgMCBvYmoKPDwgL0xlbmd0aCA3MyA+PgpzdHJlYW0KQlQKL0YxIDI0IFRmCjEwMCAxMDAgVGQKKCBBcmJpdHJhcnkgY29udGVudCApIFRqCkVUCmVuZHN0cmVhbQplbmRvYmoKNiAwIG9iagpbIC9QREYgL1RleHQgXQplbmRvYmoKNyAwIG9iago8PCAvVHlwZSAvRm9udAovU3VidHlwZSAvVHlwZTEKL05hbWUgL0YxCi9CYXNlRm9udCAvSGVsdmV0aWNhCi9FbmNvZGluZyAvTWFjUm9tYW5FbmNvZGluZwo+PgplbmRvYmoKeHJlZgowIDgKMDAwMDAwMDAwMCA2NTUzNSBmCjAwMDAwMDAwMDkgMDAwMDAgbgowMDAwMDAwMDc0IDAwMDAwIG4KMDAwMDAwMDEyMCAwMDAwMCBuCjAwMDAwMDAxNzkgMDAwMDAgbgowMDAwMDAwMzY0IDAwMDAwIG4KMDAwMDAwMDQ2NiAwMDAwMCBuCjAwMDAwMDA0OTYgMDAwMDAgbgp0cmFpbGVyCjw8IC9TaXplIDgKL1Jvb3QgMSAwIFIKPj4Kc3RhcnR4cmVmCjYyNQolJUVPRgo="
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": filename,
                "file": pdf_content,
            },
        )
        self.assert_status_code(response, 200)
        mediafile = self.get_model("mediafile/1")
        assert mediafile.get("pdf_information") == {"pages": 1}
        self.media.upload_mediafile.assert_called_with(
            pdf_content, 1, "application/pdf"
        )

    def test_upload_csv(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "test.csv"
        raw_csv_content = b"""A,B,C,D
e,f,,g
h,i,j,k
l,m,n,"""
        csv_content = base64.b64encode(raw_csv_content).decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": filename,
                "file": csv_content,
            },
        )
        self.assert_status_code(response, 200)
        # mediafile = self.get_model("mediafile/1")
        # assert mediafile.get("pdf_information") == {"pages": 1}
        self.media.upload_mediafile.assert_called_with(csv_content, 1, "text/csv")

    def test_error_in_resource_upload(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "raises_upload_error.txt"
        used_mimetype = "text/plain"
        raw_content = b"Do me a favour and trigger a mock mediaservice error, will you?"
        file_content = base64.b64encode(raw_content).decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
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
                "owner_id": "meeting/110",
                "file": file_content,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['filename'] properties",
            response.json["message"],
        )

    def test_create_directory_parent_id_parent_not_directory(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "name": "meeting_1",
                    "mediafile_ids": [7],
                    "is_active_in_organization_id": 1,
                },
                "mediafile/7": {"owner_id": "meeting/1"},
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "owner_id": "meeting/1",
                "title": "title_1",
                "parent_id": 7,
                "file": file_content,
                "filename": "test.txt",
            },
        )
        self.assert_status_code(response, 400)
        assert "Parent is not a directory." in response.json["message"]

    def test_create_directory_parent_id_owner_mismatch(self) -> None:
        self.set_models(
            {
                "meeting/1": {"mediafile_ids": [7], "is_active_in_organization_id": 1},
                "meeting/2": {"is_active_in_organization_id": 1},
                "mediafile/7": {"owner_id": "meeting/1", "is_directory": True},
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "owner_id": "meeting/2",
                "title": "title_1",
                "parent_id": 7,
                "file": file_content,
                "filename": "test.txt",
            },
        )
        self.assert_status_code(response, 400)
        assert "Owner and parent don't match." in response.json["message"]

    def test_create_directory_title_parent_id_unique(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "mediafile_ids": [6, 7],
                    "is_active_in_organization_id": 1,
                },
                "mediafile/6": {
                    "is_directory": True,
                    "owner_id": "meeting/1",
                    "child_ids": [7],
                    "title": "parent",
                },
                "mediafile/7": {
                    "title": "title_1",
                    "owner_id": "meeting/1",
                    "parent_id": 6,
                },
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "owner_id": "meeting/1",
                "title": "title_1",
                "parent_id": 6,
                "file": file_content,
                "filename": "test.txt",
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "File 'title_1' already exists in folder 'parent'."
            in response.json["message"]
        )

    def test_create_directory_owner_access_groups_dont_match(self) -> None:
        self.set_models(
            {
                "meeting/1": {"group_ids": [11], "is_active_in_organization_id": 1},
                "meeting/2": {"is_active_in_organization_id": 1},
                "group/11": {"meeting_id": 1},
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "owner_id": "meeting/2",
                "title": "title_1",
                "access_group_ids": [11],
                "file": file_content,
                "filename": "test.txt",
            },
        )
        self.assert_status_code(response, 400)
        assert "Owner and access groups don't match." in response.json["message"]

    def test_upload_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/1",
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
                "owner_id": "meeting/1",
                "filename": "fn_jumbo.txt",
                "file": base64.b64encode(b"testtesttest").decode(),
            },
            Permissions.Mediafile.CAN_MANAGE,
        )

    def test_upload_orga_owner_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": ONE_ORGANIZATION_FQID,
                "filename": "fn_jumbo.txt",
                "token": "weblogo",
                "file": base64.b64encode(b"testtesttest").decode(),
            },
        )

    def test_upload_orga_owner_permissions(self) -> None:
        self.base_permission_test(
            {},
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": ONE_ORGANIZATION_FQID,
                "token": "weblogo",
                "filename": "fn_jumbo.txt",
                "file": base64.b64encode(b"testtesttest").decode(),
            },
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        )

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
                    "owner_id": "meeting/110",
                },
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
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
                "owner_id": "meeting/110",
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
                    "owner_id": "meeting/110",
                },
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
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
                "owner_id": "meeting/110",
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
                    "owner_id": "meeting/110",
                },
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
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
                "owner_id": "meeting/110",
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
