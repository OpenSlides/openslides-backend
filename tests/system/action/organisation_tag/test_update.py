from tests.system.action.base import BaseActionTestCase


class OrganisationTagUpdateActionTest(BaseActionTestCase):
    def test_update_correct(self) -> None:
        self.set_models({"organisation_tag/1": {"name": "old", "color": "#000000"}})
        response = self.request(
            "organisation_tag.update", {"id": 1, "name": "test", "color": "#121212"}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "organisation_tag/1", {"name": "test", "color": "#121212"}
        )
