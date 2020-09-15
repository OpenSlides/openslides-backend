from openslides_backend.shared.exceptions import DatabaseException
from tests.system.action.base import BaseActionTestCase
from tests.util import get_fqid


class TagActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model(get_fqid("tag/111"), {"name": "name_srtgb123"})
        response = self.client.post(
            "/",
            json=[
                {"action": "tag.update", "data": [{"id": 111, "name": "name_Xcdfgee"}]}
            ],
        )
        self.assertEqual(response.status_code, 200)
        self.assert_model_exists(get_fqid("tag/111"))
        model = self.datastore.get(get_fqid("tag/111"))
        assert model.get("name") == "name_Xcdfgee"

    def test_update_wrong_id(self) -> None:
        self.create_model(get_fqid("tag/111"), {"name": "name_srtgb123"})
        with self.assertRaises(DatabaseException):
            self.client.post(
                "/",
                json=[
                    {
                        "action": "tag.update",
                        "data": [{"id": 112, "name": "name_Xcdfgee"}],
                    }
                ],
            )
        model = self.datastore.get(get_fqid("tag/111"))
        assert model.get("name") == "name_srtgb123"
