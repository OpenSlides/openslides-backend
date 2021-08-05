from openslides_backend.permissions.permissions import Permissions

from .base import BasePresenterTestCase


class TestCheckMediafileId(BasePresenterTestCase):
    def test_simple(self) -> None:
        self.create_model(
            "mediafile/1",
            {"filename": "the filename", "is_directory": False, "meeting_id": 1},
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
        payload = {"presenter": "check_mediafile_id", "data": {"mediafile_id": 1}}
        response = self.client.post("/", json=[payload])
        self.assert_status_code(response, 400)

    def test_request_without_token(self) -> None:
        self.create_model(
            "mediafile/1",
            {"filename": "the filename", "is_directory": False, "meeting_id": 1},
        )
        self.create_model("meeting/1")
        self.client.headers = {}
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": True, "filename": "the filename"})

    def test_no_permissions(self) -> None:
        self.set_models(
            {
                "mediafile/1": {"filename": "the filename", "is_directory": False},
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
                    "meeting_id": 1,
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
                    "meeting_id": 1,
                    "used_as_logo_$_in_meeting_id": ["test"],
                    "used_as_logo_$test_in_meeting_id": 1,
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
                    "meeting_id": 1,
                    "used_as_font_$_in_meeting_id": ["test"],
                    "used_as_font_$test_in_meeting_id": 1,
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
                    "meeting_id": 1,
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
                    "meeting_id": 1,
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
                    "meeting_id": 1,
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
