from tests.system.action.base import BaseActionTestCase


class MotionSubmitterSortActionTest(BaseActionTestCase):
    def test_sort_correct_1(self) -> None:
        self.create_model("motion/222", {})
        self.create_model("motion_submitter/31", {"motion_id": 222})
        self.create_model("motion_submitter/32", {"motion_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_submitter.sort",
                    "data": [{"motion_id": 222, "motion_submitter_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model_31 = self.get_model("motion_submitter/31")
        assert model_31.get("weight") == 2
        model_32 = self.get_model("motion_submitter/32")
        assert model_32.get("weight") == 1

    def test_sort_missing_model(self) -> None:
        self.create_model("motion/222", {})
        self.create_model("motion_submitter/31", {"motion_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_submitter.sort",
                    "data": [{"motion_id": 222, "motion_submitter_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Id 32 not in db_instances." in str(response.data)

    def test_sort_another_section_db(self) -> None:
        self.create_model("motion/222", {})
        self.create_model("motion_submitter/31", {"motion_id": 222})
        self.create_model("motion_submitter/32", {"motion_id": 222})
        self.create_model("motion_submitter/33", {"motion_id": 222})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion_submitter.sort",
                    "data": [{"motion_id": 222, "motion_submitter_ids": [32, 31]}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Additional db_instances found." in str(response.data)
