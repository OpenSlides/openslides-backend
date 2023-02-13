from tests.system.action.base import BaseActionTestCase


class OptionCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(
            "meeting/111",
            {"name": "meeting_Xcdfgee", "is_active_in_organization_id": 1},
        )
        response = self.request(
            "option.create", {"text": "testtesttest", "meeting_id": 111, "weight": 10}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("option/1")
        assert model.get("text") == "testtesttest"
        assert model.get("meeting_id") == 111
        assert model.get("weight") == 10

    def test_create_without_text_and_content_object_id(self) -> None:
        self.create_model(
            "meeting/111",
            {"name": "meeting_Xcdfgee", "is_active_in_organization_id": 1},
        )
        response = self.request("option.create", {"meeting_id": 111, "weight": 10})
        self.assert_status_code(response, 400)
        assert (
            "Need one of text, content_object_id or poll_candidate_user_ids."
            in response.json["message"]
        )

    def test_create_with_both_text_and_content_object_id(self) -> None:
        self.set_models(
            {
                "meeting/111": {
                    "name": "meeting_Xcdfgee",
                    "is_active_in_organization_id": 1,
                },
                "motion/112": {"meeting_id": 111},
            }
        )
        response = self.request(
            "option.create",
            {
                "text": "test",
                "content_object_id": "motion/112",
                "meeting_id": 111,
                "weight": 10,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Need one of text, content_object_id or poll_candidate_user_ids."
            in response.json["message"]
        )

    def test_create_yna_votes(self) -> None:
        self.create_model(
            "meeting/111",
            {"name": "meeting_Xcdfgee", "is_active_in_organization_id": 1},
        )
        response = self.request(
            "option.create",
            {
                "text": "test",
                "meeting_id": 111,
                "weight": 10,
                "yes": "1.000000",
                "no": "2.500000",
                "abstain": "0.666667",
            },
        )
        self.assert_status_code(response, 200)
        option = self.get_model("option/1")
        assert option.get("vote_ids") == [1, 2, 3]
        assert option.get("text") == "test"
        vote_1 = self.get_model("vote/1")
        assert vote_1.get("value") == "Y"
        assert vote_1.get("weight") == "1.000000"
        assert vote_1.get("option_id") == 1
        vote_2 = self.get_model("vote/2")
        assert vote_2.get("value") == "N"
        assert vote_2.get("weight") == "2.500000"
        assert vote_2.get("option_id") == 1
        vote_3 = self.get_model("vote/3")
        assert vote_3.get("value") == "A"
        assert vote_3.get("weight") == "0.666667"
        assert vote_3.get("option_id") == 1
