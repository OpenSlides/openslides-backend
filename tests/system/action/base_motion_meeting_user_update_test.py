from tests.system.action.base import BaseActionTestCase


def build_motion_meeting_user_update_test(collection: str) -> type[BaseActionTestCase]:
    class BaseMotionMeetingUserUpdateTest(BaseActionTestCase):
        action = f"{collection}.update"
        __test__ = False

        def setUp(self) -> None:
            super().setUp()
            self.create_meeting(1)
            self.set_models(
                {
                    "meeting/1": {"meeting_user_ids": [78]},
                    "motion/357": {
                        "title": "title_YIDYXmKj",
                        "meeting_id": 1,
                    },
                    "user/78": {
                        "username": "username_loetzbfg",
                        "meeting_ids": [1],
                        "meeting_user_ids": [78],
                    },
                    "meeting_user/78": {"meeting_id": 111, "user_id": 78},
                    f"{collection}/1": {
                        "meeting_user_id": 78,
                        "meeting_id": 1,
                        "motion_id": 357,
                        "weight": 3,
                    },
                }
            )

        def test_update(self) -> None:
            response = self.request(
                self.action,
                {"id": 1, "weight": 100},
            )
            self.assert_status_code(response, 200)
            model = self.get_model(f"{collection}/1")
            assert model.get("weight") == 100

        def test_update_empty_data(self) -> None:
            response = self.request(self.action, {})
            self.assert_status_code(response, 400)
            self.assertIn(
                "data must contain ['id', 'weight'] properties",
                response.json["message"],
            )

        def test_update_wrong_field(self) -> None:
            response = self.request(
                self.action,
                {
                    "id": 1,
                    "weight": 1,
                    "wrong_field": "text_AefohteiF8",
                },
            )
            self.assert_status_code(response, 400)
            self.assertIn(
                "data must not contain {'wrong_field'} properties",
                response.json["message"],
            )

    return BaseMotionMeetingUserUpdateTest
