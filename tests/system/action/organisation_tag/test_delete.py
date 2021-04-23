from tests.system.action.base import BaseActionTestCase


class OrganisationTagDeleteActionTest(BaseActionTestCase):
    def test_delete_correct(self) -> None:
        self.set_models({"organisation_tag/1": {"name": "test", "color": "#000000"}})
        response = self.request("organisation_tag.delete", {"id": 1})
        self.assert_status_code(response, 200)
        self.assert_model_deleted("organisation_tag/1")
