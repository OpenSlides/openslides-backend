from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionSubmitterCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 1},
            "user/78": {"username": "username_loetzbfg", "meeting_ids": [1]},
        }

    def test_create(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "name": "name_m123etrd",
                    "is_active_in_organization_id": 1,
                },
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "user/78": {"username": "username_loetzbfg", "meeting_ids": [111]},
            }
        )
        response = self.request(
            "motion_submitter.create", {"motion_id": 357, "user_id": 78, "weight": 100}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_submitter/1")
        assert model.get("motion_id") == 357
        assert model.get("user_id") == 78
        assert model.get("weight") == 100

    def test_create_default_weight(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "name": "name_m123etrd",
                    "is_active_in_organization_id": 1,
                },
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "user/78": {"username": "username_loetzbfg", "meeting_ids": [111]},
                "user/79": {"username": "username_wuumpoop", "meeting_ids": [111]},
                "motion_submitter/1": {"user_id": 79, "motion_id": 357, "weight": 100},
            }
        )
        response = self.request(
            "motion_submitter.create", {"motion_id": 357, "user_id": 78}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_submitter/2")
        assert model.get("motion_id") == 357
        assert model.get("user_id") == 78
        assert model.get("weight") == 101

    def test_create_weight_double_action(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "name": "name_m123etrd",
                    "is_active_in_organization_id": 1,
                },
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "user/78": {"username": "username_loetzbfg", "meeting_ids": [111]},
                "user/89": {"username": "username_ghjiuen2", "meeting_ids": [111]},
                "user/93": {"username": "username_husztw", "meeting_ids": [111]},
            }
        )
        response = self.request_multi(
            "motion_submitter.create",
            [
                {"motion_id": 357, "user_id": 78},
                {"motion_id": 357, "user_id": 89},
                {"motion_id": 357, "user_id": 93},
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("motion_submitter/1", {"weight": 1, "user_id": 78})
        self.assert_model_exists("motion_submitter/2", {"weight": 2, "user_id": 89})
        self.assert_model_exists("motion_submitter/3", {"weight": 3, "user_id": 93})

    def test_create_not_unique(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "name": "name_m123etrd",
                    "is_active_in_organization_id": 1,
                },
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "user/78": {"username": "username_loetzbfg", "meeting_ids": [111]},
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
                "meeting/111": {
                    "name": "name_m123etrd",
                    "is_active_in_organization_id": 1,
                },
                "meeting/112": {
                    "name": "name_ewadetrd",
                    "is_active_in_organization_id": 1,
                },
                "motion/357": {"title": "title_YIDYXmKj", "meeting_id": 111},
                "user/78": {"username": "username_loetzbfg", "meeting_ids": [112]},
            }
        )
        response = self.request(
            "motion_submitter.create", {"motion_id": 357, "user_id": 78}
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The following models do not belong to meeting 111: ['user/78']",
            response.json["message"],
        )

    def test_create_no_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "motion_submitter.create",
            {"motion_id": 357, "user_id": 78},
        )

    def test_create_permissions(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "motion_submitter.create",
            {"motion_id": 357, "user_id": 78},
            Permissions.Motion.CAN_MANAGE_METADATA,
        )
