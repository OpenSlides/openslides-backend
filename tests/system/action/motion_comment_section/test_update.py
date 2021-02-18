from tests.system.action.base import BaseActionTestCase


class MotionCommentSectionActionTest(BaseActionTestCase):
    def test_update_correct_all_fields(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_xQyvfmsS"},
                "motion_comment_section/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 222,
                },
                "group/23": {"meeting_id": 222, "name": "name_asdfetza"},
            }
        )
        response = self.request(
            "motion_comment_section.update",
            {
                "id": 111,
                "name": "name_iuqAPRuD",
                "read_group_ids": [23],
                "write_group_ids": [23],
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion_comment_section/111")
        assert model.get("name") == "name_iuqAPRuD"
        assert model.get("meeting_id") == 222
        assert model.get("read_group_ids") == [23]
        assert model.get("write_group_ids") == [23]

    def test_update_wrong_id(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_xQyvfmsS"},
                "group/23": {"meeting_id": 222, "name": "name_asdfetza"},
                "group/24": {"meeting_id": 222, "name": "name_faofetza"},
                "motion_comment_section/111": {
                    "name": "name_srtgb123",
                    "meeting_id": 222,
                    "read_group_ids": [23],
                },
            }
        )
        response = self.request(
            "motion_comment_section.update", {"id": 112, "read_group_ids": [24]}
        )
        self.assert_status_code(response, 400)
        model = self.get_model("motion_comment_section/111")
        assert model.get("read_group_ids") == [23]
