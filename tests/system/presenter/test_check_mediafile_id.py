from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from .base import PRESENTER_URL, BasePresenterTestCase


class TestCheckMediafileId(BasePresenterTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "committee/1": {"meeting_ids": [1]},
                "meeting/1": {
                    "admin_group_id": 2,
                    "mediafile_ids": [1, 2],
                    "committee_id": 1,
                },
                "group/2": {"meeting_id": 1, "admin_group_for_meeting_id": 1},
                "mediafile/1": {
                    "filename": "the filename",
                    "is_directory": False,
                    "owner_id": "meeting/1",
                },
            }
        )

    def test_simple(self) -> None:
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": True, "filename": "the filename"})

    def test_is_directory(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "is_directory": True,
                },
            }
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": False})

    def test_non_existent(self) -> None:
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 42})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": False})

    def test_request_without_token(self) -> None:
        self.client.auth_data.pop("access_token", None)
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": True, "filename": "the filename"})

    def test_no_permissions(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
            }
        )
        status_code, _ = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 403)

    def test_permission_in_admin_group(self) -> None:
        self.set_models(
            {
                "meeting/1": {"admin_group_id": 2},
                "user/1": {
                    "organization_management_level": None,
                    "meeting_user_ids": [1],
                },
                "group/2": {"meeting_user_ids": [1]},
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
            }
        )
        status_code, _ = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)

    def test_permission_logo(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "used_as_logo_web_header_in_meeting_id": 1,
                },
                "meeting/1": {"enable_anonymous": True},
                "user/1": {"organization_management_level": None},
            }
        )
        status_code, _ = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)

    def test_no_permission_check_committee(self) -> None:
        self.set_models(
            {
                "user/1": {"organization_management_level": None},
            }
        )
        status_code, _ = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 403)

    def test_permission_font(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "used_as_font_bold_in_meeting_id": 1,
                },
                "meeting/1": {"enable_anonymous": True},
                "user/1": {"organization_management_level": None},
            }
        )
        status_code, _ = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)

    def test_permission_projector_can_see(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "projection_ids": [1],
                },
                "meeting/1": {"default_group_id": 3, "meeting_user_ids": [1]},
                "group/3": {
                    "meeting_user_ids": [1],
                    "permissions": [Permissions.Projector.CAN_SEE],
                },
                "user/1": {
                    "organization_management_level": None,
                    "meeting_user_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
                "projection/1": {"meeting_id": 1, "current_projector_id": 1},
                "projector/1": {"meeting_id": 1, "current_projection_ids": [1]},
            }
        )
        status_code, _ = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)

    def test_can_see_and_is_public(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "is_public": True,
                },
                "meeting/1": {"default_group_id": 3, "meeting_user_ids": [1]},
                "group/3": {
                    "meeting_user_ids": [1],
                    "permissions": [Permissions.Mediafile.CAN_SEE],
                },
                "user/1": {
                    "organization_management_level": None,
                    "meeting_user_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
            }
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)

    def test_can_see_and_inherited_groups(self) -> None:
        self.set_models(
            {
                "mediafile/1": {
                    "inherited_access_group_ids": [2],
                },
                "meeting/1": {"default_group_id": 3, "meeting_user_ids": [1]},
                "group/3": {
                    "meeting_user_ids": [1],
                    "permissions": [Permissions.Mediafile.CAN_SEE],
                },
                "user/1": {
                    "organization_management_level": None,
                    "meeting_user_ids": [1],
                },
                "meeting_user/1": {
                    "meeting_id": 1,
                    "user_id": 1,
                    "group_ids": [2],
                },
            }
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)

    def test_simple_organization(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"mediafile_ids": [1]},
                "mediafile/1": {
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
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "mimetype": "text/plain",
                },
            }
        )

        response = self.anon_client.post(
            PRESENTER_URL,
            json=[{"presenter": "check_mediafile_id", "data": {"mediafile_id": 1}}],
        )
        self.assertEqual(response.status_code, 403)

    def test_anonymous_organization_with_token(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"mediafile_ids": [1]},
                "mediafile/1": {
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
        self.assertEqual(response.status_code, 200)
        data = response.json[0]
        self.assertEqual(data, {"ok": True, "filename": "web_logo.txt"})

    def test_anonymize_organization_with_token_no_committee_no_mimetype(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"mediafile_ids": [1]},
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "token": "web_logo",
                },
            }
        )

        response = self.anon_client.post(
            PRESENTER_URL,
            json=[{"presenter": "check_mediafile_id", "data": {"mediafile_id": 1}}],
        )
        status_code = response.status_code
        data = response.json[0]
        assert status_code == 200
        assert data["ok"] is False

    def test_anonymize_organization_with_token_no_committee_wrong_mimetype(
        self,
    ) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {"mediafile_ids": [1]},
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                    "token": "web_logo",
                    "mimetype": "xxx",
                },
            }
        )

        response = self.anon_client.post(
            PRESENTER_URL,
            json=[{"presenter": "check_mediafile_id", "data": {"mediafile_id": 1}}],
        )
        status_code = response.status_code
        data = response.json[0]
        assert status_code == 200
        assert data["ok"] is False
