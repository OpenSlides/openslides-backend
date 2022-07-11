from typing import Any, Dict

from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MeetingSetLogoActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_models: Dict[str, Dict[str, Any]] = {
            "meeting/1": {"name": "name_meeting1", "is_active_in_organization_id": 1},
            "mediafile/17": {
                "is_directory": False,
                "mimetype": "image/png",
                "owner_id": "meeting/1",
            },
        }

    def test_set_logo_correct(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/png",
                    "owner_id": "meeting/222",
                },
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 222, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("meeting/222")
        assert model.get("logo_$web_header_id") == 17

    def test_set_logo_wrong_place(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "image/png",
                    "owner_id": "meeting/222",
                },
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 222, "mediafile_id": 17, "place": "broken"}
        )
        self.assert_status_code(response, 400)
        assert (
            "Replacement broken does not exist in field logo__id´s replacement_enum."
            == response.json["message"]
        )

    def test_set_logo_wrong_directory(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/17": {
                    "is_directory": True,
                    "mimetype": "image/png",
                    "owner_id": "meeting/222",
                },
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 222, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 400)
        assert "Cannot set a directory." in response.json["message"]

    def test_set_logo_wrong_no_image(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_meeting222",
                    "is_active_in_organization_id": 1,
                },
                "mediafile/17": {
                    "is_directory": False,
                    "mimetype": "text/plain",
                    "owner_id": "meeting/222",
                },
            }
        )
        response = self.request(
            "meeting.set_logo", {"id": 222, "mediafile_id": 17, "place": "web_header"}
        )
        self.assert_status_code(response, 400)
        assert "Invalid mimetype" in response.json["message"]

    def test_set_logo_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.set_logo",
            {"id": 1, "mediafile_id": 17, "place": "web_header"},
        )

    def test_set_logo_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_models,
            "meeting.set_logo",
            {"id": 1, "mediafile_id": 17, "place": "web_header"},
            Permissions.Meeting.CAN_MANAGE_LOGOS_AND_FONTS,
        )
