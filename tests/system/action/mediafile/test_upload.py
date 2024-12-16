import base64
from textwrap import dedent
from time import time

import simplejson as json

from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import (
    INITIAL_DATA_FILE,
    ONE_ORGANIZATION_FQID,
    get_initial_data_file,
)
from tests.system.action.base import BaseActionTestCase


class MediafileUploadActionTest(BaseActionTestCase):
    png_content = "iVBORw0KGgoAAAANSUhEUgAAAAMAAAADAQMAAABs5if8AAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AYht+milIqDmYQcchQnSyIijhqFYpQIdQKrTqYXPoHTRqSFBdHwbXg4M9i1cHFWVcHV0EQ/AFxdXFSdJESv0sKLWK847iH97735e47QGhUmG53jQO64VjpZELK5lalnldEaUYgQlCYbc7JcgqB4+seIb7fxXlWcN2fo0/L2wwIScSzzLQc4g3i6U3H5LxPLLKSohGfE49ZdEHiR66rPr9xLnos8EzRyqTniUViqdjBagezkqUTTxHHNN2gfCHrs8Z5i7NeqbHWPfkLo3ljZZnrtIaRxCKWIEOCihrKqMBBnHaDFBtpOk8E+Ic8v0wulVxlMHIsoAodiucH/4PfvbULkxN+UjQBdL+47scI0LMLNOuu+33sus0TIPwMXBltf7UBzHySXm9rsSOgfxu4uG5r6h5wuQMMPpmKpXhSmJZQKADvZ/RNOWDgFois+X1rneP0AchQr1I3wMEhMFqk7PWAd/d29u3fmlb/fgD99XJ4ewrt8wAAAAZQTFRFyzQ0////9R4AGgAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+cMDAomKl1BHAcAAAALSURBVAjXY2AAAQAABgABZvTJbAAAAABJRU5ErkJggg=="

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
            },
        )
        assert mediafile.get("create_timestamp", 0) >= start_time
        assert not mediafile.get("is_directory")
        self.media.upload_mediafile.assert_called_with(file_content, 1, "text/plain")

        # It is essential that a meeting_mediafile is always created for meeting mediafiles
        # since non-existence means that the access_group will be assumed to be the meetings
        # admin group. The below line therefore is essential to ensure the correct functionality.
        self.assert_model_exists(
            "meeting_mediafile/1", {"is_public": True, "inherited_access_group_ids": []}
        )

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
                "is_directory": None,
            },
        )
        assert mediafile.get("create_timestamp", 0) >= start_time
        self.media.upload_mediafile.assert_called_with(file_content, 1, "text/plain")

    def test_upload_organization_with_published_parent(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "title": "published",
                    "is_directory": True,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": 1,
                }
            }
        )
        filename = "fn_jumbo.txt"
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": ONE_ORGANIZATION_FQID,
                "filename": filename,
                "file": file_content,
                "parent_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/2",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": ONE_ORGANIZATION_FQID,
                "file": None,
                "mimetype": "text/plain",
                "filesize": 12,
                "is_directory": None,
                "parent_id": 1,
                "published_to_meetings_in_organization_id": 1,
            },
        )

    def test_upload_organization_with_published_parent_create_meeting_mediafiles(
        self,
    ) -> None:
        self.create_meeting()
        self.create_meeting(4)
        self.create_meeting(7)
        self.set_models(
            {
                "mediafile/1": {
                    "title": "published",
                    "is_directory": True,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": 1,
                    "meeting_mediafile_ids": [11, 41],
                },
                "mediafile/2": {
                    "title": "publishedToo",
                    "is_directory": True,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "published_to_meetings_in_organization_id": 1,
                    "meeting_mediafile_ids": [42],
                },
                "meeting/1": {"meeting_mediafile_ids": [11]},
                "meeting_mediafile/11": {
                    "meeting_id": 1,
                    "mediafile_id": 1,
                    "is_public": True,
                    "inherited_access_group_ids": [],
                },
                "meeting/4": {"meeting_mediafile_ids": [41, 42]},
                "meeting_mediafile/41": {
                    "meeting_id": 4,
                    "mediafile_id": 1,
                    "access_group_ids": [5, 6],
                    "is_public": False,
                    "inherited_access_group_ids": [5],
                },
                "meeting_mediafile/42": {
                    "meeting_id": 4,
                    "mediafile_id": 2,
                    "access_group_ids": [5, 6],
                    "is_public": False,
                    "inherited_access_group_ids": [6],
                },
                "group/5": {
                    "meeting_mediafile_access_group_ids": [41, 42],
                    "meeting_mediafile_inherited_access_group_ids": [41],
                },
                "group/6": {
                    "meeting_mediafile_access_group_ids": [41, 42],
                    "meeting_mediafile_inherited_access_group_ids": [42],
                },
            }
        )
        filename = "fn_jumbo.txt"
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": ONE_ORGANIZATION_FQID,
                "filename": filename,
                "file": file_content,
                "parent_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/3",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": ONE_ORGANIZATION_FQID,
                "file": None,
                "mimetype": "text/plain",
                "filesize": 12,
                "is_directory": None,
                "parent_id": 1,
                "published_to_meetings_in_organization_id": 1,
                "meeting_mediafile_ids": [43, 44],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/43",
            {
                "meeting_id": 1,
                "mediafile_id": 3,
                "is_public": True,
                "inherited_access_group_ids": [],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/44",
            {
                "meeting_id": 4,
                "mediafile_id": 3,
                "is_public": False,
                "inherited_access_group_ids": [5],
            },
        )
        self.assert_model_not_exists("meeting_mediafile/45")

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
        filename = "fn_jumbo.unknown"
        file_content = base64.b64encode(b"testtesttest").decode()
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
        assert f"Cannot guess mimetype for {filename}." in response.json.get(
            "message", ""
        )
        self.assert_model_not_exists("mediafile/1")
        self.media.upload_mediafile.assert_not_called()

    def test_mimetype_and_extension_no_match(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "fn_jumbo.pdf"
        file_content = base64.b64encode(b"testtesttest").decode()
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
        assert (
            f"{filename} does not have a file extension that matches the determined mimetype text/plain."
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
                    "meeting_mediafile_ids": [1110],
                },
                "mediafile/10": {
                    "title": "title_CgKPfByo",
                    "is_directory": True,
                    "owner_id": "meeting/110",
                    "meeting_mediafile_ids": [1110],
                },
                "meeting_mediafile/1110": {
                    "meeting_id": 110,
                    "mediafile_id": 10,
                    "inherited_access_group_ids": [],
                    "is_public": True,
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
        mediafile = self.assert_model_exists(
            "mediafile/11",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": "fn_jumbo.txt",
                "parent_id": 10,
                "meeting_mediafile_ids": [1111],
            },
        )
        assert mediafile.get("file") is None
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "meeting_id": 110,
                "mediafile_id": 11,
                "access_group_ids": [],
                "is_public": True,
                "inherited_access_group_ids": [],
            },
        )
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
        self.media.upload_mediafile.assert_called_with(csv_content, 1, "text/csv")

    def test_upload_json_detect_json(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "test.json"
        raw_json_content = dedent(
            """
                {
                    "bruh": ["this", "is"],
                    "like": "like",
                    "totally": 1,
                    "actual": true,
                    "json": {"file": "maaaann"}
                }
                """
        ).encode()
        json_content = base64.b64encode(raw_json_content).decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": filename,
                "file": json_content,
            },
        )
        self.assert_status_code(response, 200)
        self.media.upload_mediafile.assert_called_with(
            json_content, 1, "application/json"
        )

    def test_upload_json_detect_plain_text(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "test.json"
        raw_content = (
            b"plain text, but file with json extension. We got with big json files"
        )
        json_content = base64.b64encode(raw_content).decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": filename,
                "file": json_content,
            },
        )
        self.assert_status_code(response, 200)
        self.media.upload_mediafile.assert_called_with(
            json_content, 1, "application/json"
        )

    def test_upload_json_detect_html(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "test.json"
        data = json.dumps(get_initial_data_file(INITIAL_DATA_FILE)).encode()
        json_content = base64.b64encode(data).decode()
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": filename,
                "file": json_content,
            },
        )
        self.assert_status_code(response, 200)
        self.media.upload_mediafile.assert_called_with(
            json_content, 1, "application/json"
        )

    def test_upload_svg(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "line.svg"
        svg_content = "Cjw/eG1sIHZlcnNpb249IjEuMCIgZW5jb2Rpbmc9IlVURi04IiBzdGFuZGFsb25lPSJubyI/Pgo8IS0tIENyZWF0ZWQgd2l0aCBJbmtzY2FwZSAoaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvKSAtLT4KCjxzdmcKd2lkdGg9IjIxMG1tIgpoZWlnaHQ9IjI5N21tIgp2aWV3Qm94PSIwIDAgMjEwIDI5NyIKdmVyc2lvbj0iMS4xIgppZD0ic3ZnNSIKaW5rc2NhcGU6dmVyc2lvbj0iMS4xLjIgKDBhMDBjZjUzMzksIDIwMjItMDItMDQpIgpzb2RpcG9kaTpkb2NuYW1lPSJsaW5lLnN2ZyIKeG1sbnM6aW5rc2NhcGU9Imh0dHA6Ly93d3cuaW5rc2NhcGUub3JnL25hbWVzcGFjZXMvaW5rc2NhcGUiCnhtbG5zOnNvZGlwb2RpPSJodHRwOi8vc29kaXBvZGkuc291cmNlZm9yZ2UubmV0L0RURC9zb2RpcG9kaS0wLmR0ZCIKeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgp4bWxuczpzdmc9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHNvZGlwb2RpOm5hbWVkdmlldwogICAgaWQ9Im5hbWVkdmlldzciCiAgICBwYWdlY29sb3I9IiNmZmZmZmYiCiAgICBib3JkZXJjb2xvcj0iIzY2NjY2NiIKICAgIGJvcmRlcm9wYWNpdHk9IjEuMCIKICAgIGlua3NjYXBlOnBhZ2VzaGFkb3c9IjIiCiAgICBpbmtzY2FwZTpwYWdlb3BhY2l0eT0iMC4wIgogICAgaW5rc2NhcGU6cGFnZWNoZWNrZXJib2FyZD0iMCIKICAgIGlua3NjYXBlOmRvY3VtZW50LXVuaXRzPSJtbSIKICAgIHNob3dncmlkPSJmYWxzZSIKICAgIGlua3NjYXBlOnpvb209IjAuNjA3NTYxNzMiCiAgICBpbmtzY2FwZTpjeD0iMzk3LjQ5MDQ3IgogICAgaW5rc2NhcGU6Y3k9IjU2Mi4wODI4IgogICAgaW5rc2NhcGU6d2luZG93LXdpZHRoPSIxOTIwIgogICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iMTAzMSIKICAgIGlua3NjYXBlOndpbmRvdy14PSIwIgogICAgaW5rc2NhcGU6d2luZG93LXk9IjI1IgogICAgaW5rc2NhcGU6d2luZG93LW1heGltaXplZD0iMSIKICAgIGlua3NjYXBlOmN1cnJlbnQtbGF5ZXI9ImxheWVyMSIgLz4KPGRlZnMKICAgIGlkPSJkZWZzMiI+CiAgICA8aW5rc2NhcGU6cGF0aC1lZmZlY3QKICAgIGVmZmVjdD0ic3Bpcm8iCiAgICBpZD0icGF0aC1lZmZlY3QxMDciCiAgICBpc192aXNpYmxlPSJ0cnVlIgogICAgbHBldmVyc2lvbj0iMSIgLz4KPC9kZWZzPgo8ZwogICAgaW5rc2NhcGU6bGFiZWw9IkViZW5lIDEiCiAgICBpbmtzY2FwZTpncm91cG1vZGU9ImxheWVyIgogICAgaWQ9ImxheWVyMSI+CiAgICA8cGF0aAogICAgc3R5bGU9ImZpbGw6bm9uZTtzdHJva2U6IzAwMDAwMDtzdHJva2Utd2lkdGg6MC4yNjQ1ODNweDtzdHJva2UtbGluZWNhcDpidXR0O3N0cm9rZS1saW5lam9pbjptaXRlcjtzdHJva2Utb3BhY2l0eToxIgogICAgZD0iTSA4LjkxMzcwNDIsMTEuNDU0ODAyIDExMS4wNjg4OCwzMi4wODQxMSIKICAgIGlkPSJwYXRoMTA1IgogICAgaW5rc2NhcGU6cGF0aC1lZmZlY3Q9IiNwYXRoLWVmZmVjdDEwNyIKICAgIGlua3NjYXBlOm9yaWdpbmFsLWQ9Ik0gOC45MTM3MDQyLDExLjQ1NDgwMiBDIDQyLjk2NTY5MiwxOC4zMzE1MDIgNzcuMDE3NDE5LDI1LjIwNzkzOCAxMTEuMDY4ODgsMzIuMDg0MTEiIC8+CjwvZz4KPC9zdmc+Cg=="
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": filename,
                "file": svg_content,
            },
        )
        self.assert_status_code(response, 200)

    def test_upload_png(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "red.png"
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": filename,
                "file": self.png_content,
            },
        )
        self.assert_status_code(response, 200)

    def test_upload_png_as_json(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "red.json"
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": filename,
                "file": self.png_content,
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            f"{filename} does not have a file extension that matches the determined mimetype image/png.",
            response.json["message"],
        )

    def test_upload_ttf_mimetype_sfnt(self) -> None:
        """
        There exists a mimetype 'font/sntf', whose
        extensions are ttf or otf, see https://www.iana.org/assignments/media-types/font/sfnt
        """
        sfnt_content = "AAEAAAAQAQAABAAATFRTSLVpLZsAAAbAAAAAVE9TLzJ22xUOAAABiAAAAE5jbWFwp1APwwAABSAAAAGeY3Z0IAAVBBYAAAiQAAAAEmZwZ20yRHNdAAAHLAAAAWJnbHlmStRAoQAAEXgAAP26aGRteBZioyEAAAnkAAAHlGhlYWSXgnjPAAABDAAAADZoaGVhBn4BtAAAAUQAAAAkaG10eI1/BT4AAAikAAABQGtlcm6kmKYpAAEP+AAAN25sb2NhRp4FDAABDzQAAACibWF4cAJlBb4AAAFoAAAAIG5hbWUlcYIyAAAB2AAAA0hwb3N0/58AMgABD9gAAAAgcHJlcBz/fZwAAAcUAAAAFgABAAAAAQAAxnW44F8PPPUAGQPoAAAAAHwlQAAAAAAAuRX1xv/o/uIDNANKAAAAAAAAAAAAAAAAAAEAAANK/uIAFQMA/+j/gQM0AAEAAAAAAAAAAAAAAAAAAABQAAEAAABQApQACgAAAAAAAQAAAAAACgAAAgADKQAAAAAAAAFJAZAABQAAAGQAZAAAAIwAZABkAAAAjAAyAPoAAAIAAAAAAAAAAACAAAABAAAAAAAAAAAAAAAAcGpsZgAAACAgMAKg/uIAKgNKAR4AAAAAABoBPgABAAAAAAAAAC0AAAABAAAAAAABAAUALQABAAAAAAACAAc="
        self.create_model(
            "meeting/110", {"name": "name_DsJFXoot", "is_active_in_organization_id": 1}
        )
        filename = "zenda.ttf"
        response = self.request(
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/110",
                "filename": filename,
                "file": sfnt_content,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "mediafile/1", {"filename": filename, "mimetype": "font/ttf"}
        )

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

    def test_upload_access_groups_on_orga_owner(self) -> None:
        self.set_models(
            {
                "meeting/1": {"group_ids": [11], "is_active_in_organization_id": 1},
                "group/11": {"meeting_id": 1},
            }
        )
        file_content = base64.b64encode(b"testtesttest").decode()
        response = self.request(
            "mediafile.upload",
            {
                "owner_id": "organization/1",
                "title": "title_1",
                "access_group_ids": [11],
                "file": file_content,
                "filename": "test.txt",
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "access_group_ids is not allowed in organization mediafiles."
            in response.json["message"]
        )

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

    def test_upload_permissions_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "mediafile.upload",
            {
                "title": "title_xXRGTLAJ",
                "owner_id": "meeting/1",
                "filename": "fn_jumbo.txt",
                "file": base64.b64encode(b"testtesttest").decode(),
            },
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
                    "meeting_mediafile_ids": [1110],
                },
                "group/1": {"meeting_id": 110, "name": "grp1"},
                "mediafile/10": {
                    "title": "title_CgKPfByo",
                    "is_directory": True,
                    "owner_id": "meeting/110",
                    "meeting_mediafile_ids": [1110],
                },
                "meeting_mediafile/1110": {
                    "meeting_id": 110,
                    "mediafile_id": 10,
                    "inherited_access_group_ids": [],
                    "is_public": True,
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
                "meeting_mediafile_ids": [1111],
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "meeting_id": 110,
                "mediafile_id": 11,
                "is_public": False,
                "access_group_ids": [1],
                "inherited_access_group_ids": [1],
            },
        )
        self.media.upload_mediafile.assert_called_with(file_content, 11, "text/plain")
        self.assert_model_exists(
            "group/1",
            {
                "meeting_mediafile_access_group_ids": [1111],
                "meeting_mediafile_inherited_access_group_ids": [1111],
            },
        )

    def test_create_media_directory_group(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_DsJFXoot",
                    "is_active_in_organization_id": 1,
                    "group_ids": [1],
                    "meeting_mediafile_ids": [1110],
                },
                "group/1": {"meeting_id": 110, "name": "grp1"},
                "mediafile/10": {
                    "title": "title_CgKPfByo",
                    "is_directory": True,
                    "owner_id": "meeting/110",
                    "meeting_mediafile_ids": [1110],
                },
                "meeting_mediafile/1110": {
                    "meeting_id": 110,
                    "mediafile_id": 10,
                    "inherited_access_group_ids": [1],
                    "is_public": False,
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
                "meeting_mediafile_ids": [1111],
                "parent_id": 10,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "meeting_id": 110,
                "mediafile_id": 11,
                "access_group_ids": [],
                "inherited_access_group_ids": [1],
                "is_public": False,
            },
        )
        self.media.upload_mediafile.assert_called_with(file_content, 11, "text/plain")
        self.assert_model_exists(
            "group/1", {"meeting_mediafile_inherited_access_group_ids": [1111]}
        )

    def test_create_media_both_groups(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_DsJFXoot",
                    "is_active_in_organization_id": 1,
                    "group_ids": [1, 2],
                    "meeting_mediafile_ids": [1110],
                },
                "group/1": {"meeting_id": 110, "name": "grp1"},
                "group/2": {"meeting_id": 110, "name": "grp2"},
                "mediafile/10": {
                    "title": "title_CgKPfByo",
                    "is_directory": True,
                    "owner_id": "meeting/110",
                    "meeting_mediafile_ids": [1110],
                },
                "meeting_mediafile/1110": {
                    "meeting_id": 110,
                    "mediafile_id": 10,
                    "inherited_access_group_ids": [1],
                    "is_public": False,
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
                "meeting_mediafile_ids": [1111],
                "parent_id": 10,
            },
        )
        self.assert_model_exists(
            "meeting_mediafile/1111",
            {
                "meeting_id": 110,
                "mediafile_id": 11,
                "access_group_ids": [1, 2],
                "inherited_access_group_ids": [1],
                "is_public": False,
            },
        )
        self.media.upload_mediafile.assert_called_with(file_content, 11, "text/plain")
        self.assert_model_exists(
            "group/1",
            {
                "meeting_mediafile_access_group_ids": [1111],
                "meeting_mediafile_inherited_access_group_ids": [1111],
            },
        )
        self.assert_model_exists(
            "group/2", {"meeting_mediafile_access_group_ids": [1111]}
        )
