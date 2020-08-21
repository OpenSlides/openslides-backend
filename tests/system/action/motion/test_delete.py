from openslides_backend.shared.exceptions import DatabaseException
from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class MotionActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model(
            get_fqid("meeting/789"), {"name": "name_ZpTUxzOI", "motion_ids": [111]}
        )
        self.create_model(
            get_fqid("motion/111"), {"title": "title_srtgb123", "meeting_id": 789}
        )
        response = self.client.post(
            "/", json=[{"action": "motion.delete", "data": [{"id": 111}]}],
        )
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(DatabaseException):
            self.datastore.get(get_fqid("motion/111"))

    def test_delete_wrong_id(self) -> None:
        self.create_model(get_fqid("motion/112"), {"title": "title_srtgb123"})
        with self.assertRaises(DatabaseException):
            self.client.post(
                "/", json=[{"action": "motion.delete", "data": [{"id": 111}]}],
            )
        self.assert_model_exists(get_fqid("motion/112"))
