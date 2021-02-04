from tests.system.action.base import BaseActionTestCase


class MotionSubmitterCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model("meeting/111", {"name": "name_m123etrd"})
        self.create_model("motion/357", {"title": "title_YIDYXmKj", "meeting_id": 111})
        self.create_model(
            "user/78", {"username": "username_loetzbfg", "meeting_id": 111}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_submitter.create",
                    "data": [{"motion_id": 357, "user_id": 78}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_submitter/1")
        assert model.get("motion_id") == 357
        assert model.get("user_id") == 78
        assert model.get("weight") == 10000

    def test_create_not_unique(self) -> None:
        self.create_model("meeting/111", {"name": "name_m123etrd"})
        self.create_model("motion/357", {"title": "title_YIDYXmKj", "meeting_id": 111})
        self.create_model(
            "user/78", {"username": "username_loetzbfg", "meeting_id": 111}
        )
        self.create_model(
            "motion_submitter/12", {"motion_id": 357, "user_id": 78, "meeting_id": 111}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_submitter.create",
                    "data": [{"motion_id": 357, "user_id": 78}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "(user_id, motion_id) must be unique." in response.json.get(
            "message", ""
        )

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/",
            json=[{"action": "motion_submitter.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['motion_id', 'user_id'] properties",
            response.json.get("message", ""),
        )

    def test_create_wrong_field(self) -> None:
        self.create_model("meeting/111", {"name": "name_m123etrd"})
        self.create_model("motion/357", {"title": "title_YIDYXmKj", "meeting_id": 111})
        self.create_model(
            "user/78", {"username": "username_lskeuebe", "meeting_id": 111}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_submitter.create",
                    "data": [
                        {
                            "motion_id": 357,
                            "user_id": 78,
                            "wrong_field": "text_AefohteiF8",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json.get("message", ""),
        )

    def test_create_not_matching_meeting_ids(self) -> None:
        self.create_model("meeting/111", {"name": "name_m123etrd"})
        self.create_model("meeting/112", {"name": "name_ewadetrd"})
        self.create_model("motion/357", {"title": "title_YIDYXmKj", "meeting_id": 111})
        self.create_model(
            "user/78", {"username": "username_loetzbfg", "meeting_id": 112}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_submitter.create",
                    "data": [{"motion_id": 357, "user_id": 78}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot create motion_submitter, meeting id of motion and (temporary) user don't match.",
            response.json.get("message", ""),
        )
