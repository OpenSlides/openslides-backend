from tests.system.action.base import BaseActionTestCase


class MotionCommentSectionActionTest(BaseActionTestCase):
    def test_update_correct_all_fields(self) -> None:
        self.create_model("meeting/222", {"name": "name_xQyvfmsS"})
        self.create_model(
            "motion_comment_section/111",
            {"name": "name_srtgb123", "meeting_id": 222},
        )
        self.create_model("group/23", {"name": "name_asdfetza"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_comment_section.update",
                    "data": [
                        {
                            "id": 111,
                            "name": "name_iuqAPRuD",
                            "read_group_ids": [23],
                            "write_group_ids": [23],
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_comment_section/111")
        assert model.get("name") == "name_iuqAPRuD"
        assert model.get("meeting_id") == 222
        assert model.get("read_group_ids") == [23]
        assert model.get("write_group_ids") == [23]

    def test_update_wrong_id(self) -> None:
        self.create_model("meeting/222", {"name": "name_xQyvfmsS"})
        self.create_model("group/23", {"name": "name_asdfetza"})
        self.create_model("group/24", {"name": "name_faofetza"})
        self.create_model(
            "motion_comment_section/111",
            {"name": "name_srtgb123", "meeting_id": 222, "read_group_ids": [23]},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_comment_section.update",
                    "data": [{"id": 112, "read_group_ids": [24]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_comment_section/111")
        assert model.get("read_group_ids") == [23]
