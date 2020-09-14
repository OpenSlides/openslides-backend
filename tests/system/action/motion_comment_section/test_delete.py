from openslides_backend.shared.exceptions import DatabaseException
from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionCommentSectionActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model(
            get_fqid("motion_comment_section/111"), {"name": "name_srtgb123"}
        )
        response = self.client.post(
            "/",
            json=[{"action": "motion_comment_section.delete", "data": [{"id": 111}]}],
        )
        self.assertEqual(response.status_code, 200)
        model = self.datastore.get(
            get_fqid("motion_comment_section/111"), get_deleted_models=2
        )
        assert model.get("meta_deleted")

    def test_delete_wrong_id(self) -> None:
        self.create_model(
            get_fqid("motion_comment_section/112"), {"name": "name_srtgb123"}
        )
        with self.assertRaises(DatabaseException):
            self.client.post(
                "/",
                json=[
                    {"action": "motion_comment_section.delete", "data": [{"id": 111}]}
                ],
            )
        self.assert_model_exists(get_fqid("motion_comment_section/112"))

    def test_delete_existing_comments(self) -> None:
        self.create_model(get_fqid("motion_comment/79"), {"name": "name_lkztu23d"})
        self.create_model(
            get_fqid("motion_comment_section/111"),
            {"name": "name_srtgb123", "comment_ids": [79]},
        )

        response = self.client.post(
            "/",
            json=[{"action": "motion_comment_section.delete", "data": [{"id": 111}]}],
        )
        assert response.status_code == 400
        assert (
            "Cannot delete motion comment section \\'111\\' with existing comments."
            in str(response.data)
        )
        self.assert_model_exists(get_fqid("motion_comment_section/111"))
