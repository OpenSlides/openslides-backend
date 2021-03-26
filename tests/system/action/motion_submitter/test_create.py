from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSubmitterCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.set_models(
            {
                "meeting/111": {"name": "name_m123etrd"},
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "user/78": {"username": "username_loetzbfg", "meeting_id": 111},
            }
        )
        response = self.request(
            "motion_submitter.create", {"motion_id": 357, "user_id": 78}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_submitter/1")
        assert model.get("motion_id") == 357
        assert model.get("user_id") == 78
        assert model.get("weight") == 10000

    def test_create_not_unique(self) -> None:
        self.set_models(
            {
                "meeting/111": {"name": "name_m123etrd"},
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "user/78": {"username": "username_loetzbfg", "meeting_id": 111},
                "motion_submitter/12": {
                    "motion_id": 357,
                    "user_id": 78,
                    "meeting_id": 111,
                },
            }
        )
        response = self.request(
            "motion_submitter.create", {"motion_id": 357, "user_id": 78}
        )
        self.assert_status_code(response, 400)
        assert "(user_id, motion_id) must be unique." in response.json.get(
            "message", ""
        )

    def test_create_empty_data(self) -> None:
        response = self.request("motion_submitter.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['motion_id', 'user_id'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.set_models(
            {
                "meeting/111": {"name": "name_m123etrd"},
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "user/78": {"username": "username_lskeuebe", "meeting_id": 111},
            }
        )
        response = self.request(
            "motion_submitter.create",
            {
                "motion_id": 357,
                "user_id": 78,
                "wrong_field": "text_AefohteiF8",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_not_matching_meeting_ids(self) -> None:
        self.set_models(
            {
                "meeting/111": {"name": "name_m123etrd"},
                "meeting/112": {"name": "name_ewadetrd"},
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "user/78": {"username": "username_loetzbfg", "meeting_id": 112},
            }
        )
        response = self.request(
            "motion_submitter.create", {"motion_id": 357, "user_id": 78}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot create motion_submitter, meeting id of motion and (temporary) user don't match.",
            response.json["message"],
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            {
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 1},
                "user/78": {"username": "username_loetzbfg", "meeting_id": 1},
            },
            "motion_submitter.create",
            {"motion_id": 357, "user_id": 78},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            {
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 1},
                "user/78": {"username": "username_loetzbfg", "meeting_id": 1},
            },
            "motion_submitter.create",
            {"motion_id": 357, "user_id": 78},
            Permissions.Motion.CAN_MANAGE_METADATA,
        )
