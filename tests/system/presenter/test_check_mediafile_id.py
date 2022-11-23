from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from .base import PRESENTER_URL, BasePresenterTestCase


class TestCheckMediafileId(BasePresenterTestCase):
    def test_simple(self) -> None:
        self.create_model(
            "mediafile/1",
            {
                "filename": "the filename",
                "is_directory": False,
                "owner_id": "meeting/1",
            },
        )
        self.create_model("meeting/1")
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": True, "filename": "the filename"})

    def test_is_directory(self) -> None:
        self.create_model(
            "mediafile/1", {"filename": "the filename", "is_directory": True}
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": False})

    def test_non_existent(self) -> None:
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": False})

    def test_request_without_token(self) -> None:
        self.create_model(
            "mediafile/1",
            {
                "filename": "the filename",
                "is_directory": False,
                "owner_id": "meeting/1",
            },
        )
        self.create_model("meeting/1")
        self.client.auth_data.pop("access_token", None)
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": True, "filename": "the filename"})

    def test_no_permissions(self) -> None:
        self.set_models(
            {
                "meeting/1": {"mediafile_ids": [1]},
                "mediafile/1": {
                    "owner_id": "meeting/1",
                    "filename": "the filename",
                    "is_directory": False,
                },
                "user/1": {"organization_management_level": None},
            }
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 403)

    def test_permission_in_admin_group(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "filename": "the filename",
                    "is_directory": False,
                    "owner_id": "meeting/1",
                },
                "meeting/1": {"admin_group_id": 2},
                "group/2": {"user_ids": [1]},
                "user/1": {"organization_management_level": None, "group_$1_ids": [2]},
            }
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)

    def test_permission_logo(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "filename": "the filename",
                    "is_directory": False,
                    "owner_id": "meeting/1",
                    "used_as_logo_web_header_in_meeting_id": 1,
                },
                "meeting/1": {"enable_anonymous": True},
                "user/1": {"organization_management_level": None},
            }
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)

    def test_permission_font(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "filename": "the filename",
                    "is_directory": False,
                    "owner_id": "meeting/1",
                    "used_as_font_bold_in_meeting_id": 1,
                },
                "meeting/1": {"enable_anonymous": True},
                "user/1": {"organization_management_level": None},
            }
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)

    def test_permission_projector_can_see(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "filename": "the filename",
                    "is_directory": False,
                    "owner_id": "meeting/1",
                    "projection_ids": [1],
                },
                "meeting/1": {"default_group_id": 2},
                "group/2": {
                    "user_ids": [1],
                    "permissions": [Permissions.Projector.CAN_SEE],
                },
                "user/1": {"organization_management_level": None, "group_$1_ids": [2]},
                "projection/1": {"meeting_id": 1, "current_projector_id": 1},
                "projector/1": {"meeting_id": 1, "current_projection_ids": [1]},
            }
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)

    def test_can_see_and_is_public(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "filename": "the filename",
                    "is_directory": False,
                    "owner_id": "meeting/1",
                    "is_public": True,
                },
                "meeting/1": {"default_group_id": 2},
                "group/2": {
                    "user_ids": [1],
                    "permissions": [Permissions.Mediafile.CAN_SEE],
                },
                "user/1": {"organization_management_level": None, "group_$1_ids": [2]},
            }
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)

    def test_can_see_and_inherited_groups(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "filename": "the filename",
                    "is_directory": False,
                    "owner_id": "meeting/1",
                    "inherited_access_group_ids": [2],
                },
                "meeting/1": {"default_group_id": 2},
                "group/2": {
                    "user_ids": [1],
                    "permissions": [Permissions.Mediafile.CAN_SEE],
                },
                "user/1": {"organization_management_level": None, "group_$1_ids": [2]},
            }
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)

    def test_simple_organization(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"mediafile_ids": [1]},
                "mediafile/1": {
                    "is_directory": False,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "token": "web_logo",
                    "mimetype": "text/plain",
                },
            }
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": True, "filename": "web_logo.txt"})

    def test_organization_without_token(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"mediafile_ids": [1]},
                "mediafile/1": {
                    "is_directory": False,
                    "filename": "the filename",
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "mimetype": "text/plain",
                },
            }
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": True, "filename": "the filename"})

    def test_anonymous_organization(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"mediafile_ids": [1]},
                "mediafile/1": {
                    "is_directory": False,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "mimetype": "text/plain",
                },
            }
        )

        response = self.anon_client.post(
            PRESENTER_URL,
            json=[{"presenter": "check_mediafile_id", "data": {"mediafile_id": 1}}],
        )
        status_code = response.status_code
        self.assertEqual(status_code, 403)

    def test_anonymous_organization_with_token(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"mediafile_ids": [1]},
                "mediafile/1": {
                    "is_directory": False,
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "token": "web_logo",
                    "mimetype": "text/plain",
                },
            }
        )

        response = self.anon_client.post(
            PRESENTER_URL,
            json=[{"presenter": "check_mediafile_id", "data": {"mediafile_id": 1}}],
        )
        status_code = response.status_code
        self.assertEqual(status_code, 200)
        data = response.json[0]
        self.assertEqual(data, {"ok": True, "filename": "web_logo.txt"})
