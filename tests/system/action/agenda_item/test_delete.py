from tests.system.action.base import BaseActionTestCase


class AgendaItemActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.create_model("agenda_item/111")
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("agenda_item/111")

    def test_delete_wrong_id(self) -> None:
        self.create_model("agenda_item/112")
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 400)
        self.assert_model_exists("agenda_item/112")

    def test_delete_topic(self) -> None:
        self.set_models(
            {
                "topic/34": {"agenda_item_id": 111},
                "agenda_item/111": {"content_object_id": "topic/34"},
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("agenda_item/111")
        self.assert_model_deleted("topic/34")

    def test_delete_with_motion(self) -> None:
        self.set_models(
            {
                "motion/34": {"agenda_item_id": 111},
                "agenda_item/111": {"content_object_id": "motion/34"},
            }
        )
        response = self.request("agenda_item.delete", {"id": 111})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("agenda_item/111")
        self.get_model("motion/34")
