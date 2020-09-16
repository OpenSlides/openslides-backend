from tests.system.action.base import BaseActionTestCase


class AgendaItemActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.create_model("topic/1", {"name": "test"})
        self.create_model("topic/102", {"name": "topic_kHemtGYY"})
        self.create_model(
            "agenda_item/111", {"item_number": 101, "duration": 600},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "agenda_item.update",
                    "data": [{"id": 111, "duration": 1200}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("agenda_item/111")
        assert model.get("duration") == 1200
