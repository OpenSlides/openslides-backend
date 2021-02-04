from tests.system.action.base import BaseActionTestCase


class MotionSetSupportSelfActionTest(BaseActionTestCase):
    def test_meeting_support_system_deactivated(self) -> None:
        self.create_model(
            "motion/1",
            {
                "title": "motion_1",
                "meeting_id": 1,
                "state_id": 1,
            },
        )
        self.create_model(
            "meeting/1",
            {
                "name": "name_meeting_1",
                "motion_ids": [1],
                "motions_supporters_min_amount": 0,
            },
        )
        self.create_model(
            "motion_state/1",
            {
                "name": "state_1",
                "allow_support": False,
                "motion_ids": [1],
                "meeting_id": 1,
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.set_support_self",
                    "data": [{"motion_id": 1, "support": True}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Motion supporters system deactivated." in response.json.get(
            "message", ""
        )

    def test_state_doesnt_allow_support(self) -> None:
        self.create_model(
            "motion/1",
            {
                "title": "motion_1",
                "meeting_id": 1,
                "state_id": 1,
            },
        )
        self.create_model(
            "meeting/1",
            {
                "name": "name_meeting_1",
                "motion_ids": [1],
                "motions_supporters_min_amount": 1,
            },
        )
        self.create_model(
            "motion_state/1",
            {
                "name": "state_1",
                "allow_support": False,
                "motion_ids": [1],
                "meeting_id": 1,
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.set_support_self",
                    "data": [{"motion_id": 1, "support": True}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "The state does not allow support." in response.json.get("message", "")

    def test_support(self) -> None:
        self.create_model(
            "motion/1",
            {
                "title": "motion_1",
                "meeting_id": 1,
                "state_id": 1,
                "supporter_ids": [],
            },
        )
        self.create_model(
            "meeting/1",
            {
                "name": "name_meeting_1",
                "motion_ids": [1],
                "motions_supporters_min_amount": 1,
            },
        )
        self.create_model(
            "motion_state/1",
            {
                "name": "state_1",
                "allow_support": True,
                "motion_ids": [1],
                "meeting_id": 1,
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.set_support_self",
                    "data": [{"motion_id": 1, "support": True}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("supporter_ids") == [1]
        user_1 = self.get_model("user/1")
        assert user_1.get("supported_motion_$1_ids") == [1]
        assert user_1.get("supported_motion_$_ids") == ["1"]

    def test_unsupport(self) -> None:
        self.update_model(
            "user/1",
            {"supported_motion_$_ids": ["1"], "supported_motion_$1_ids": [1]},
        )
        self.create_model(
            "motion/1",
            {
                "title": "motion_1",
                "meeting_id": 1,
                "state_id": 1,
                "supporter_ids": [1],
            },
        )
        self.create_model(
            "meeting/1",
            {
                "name": "name_meeting_1",
                "motion_ids": [1],
                "motions_supporters_min_amount": 1,
            },
        )
        self.create_model(
            "motion_state/1",
            {
                "name": "state_1",
                "allow_support": True,
                "motion_ids": [1],
                "meeting_id": 1,
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.set_support_self",
                    "data": [{"motion_id": 1, "support": False}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("supporter_ids") == []
        user_1 = self.get_model("user/1")
        assert user_1.get("supported_motion_$1_ids") == []
        assert user_1.get("supported_motion_$_ids") == []

    def test_unsupport_no_change(self) -> None:
        self.create_model(
            "motion/1",
            {
                "title": "motion_1",
                "meeting_id": 1,
                "state_id": 1,
                "supporter_ids": [],
            },
        )
        self.create_model(
            "meeting/1",
            {
                "name": "name_meeting_1",
                "motion_ids": [1],
                "motions_supporters_min_amount": 1,
            },
        )
        self.create_model(
            "motion_state/1",
            {
                "name": "state_1",
                "allow_support": True,
                "motion_ids": [1],
                "meeting_id": 1,
            },
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.set_support_self",
                    "data": [{"motion_id": 1, "support": False}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("supporter_ids") == []
