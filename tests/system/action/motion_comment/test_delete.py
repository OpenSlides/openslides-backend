from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionCommentActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("motion_comment/111", {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "motion_comment.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 200)
        model = self.datastore.get(get_fqid("motion_comment/111"), get_deleted_models=2)
        assert model.get("meta_deleted")

    def test_delete_wrong_id(self) -> None:
        self.create_model("motion_comment/112", {"name": "name_srtgb123"})
        response = self.client.post(
            "/", json=[{"action": "motion_comment.delete", "data": [{"id": 111}]}],
        )
        self.assert_status_code(response, 400)
        self.assert_model_exists("motion_comment/112")
