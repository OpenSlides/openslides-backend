from decimal import Decimal

from tests.system.action.base import BaseActionTestCase


class OptionCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting(111)

    def test_create(self) -> None:
        response = self.request(
            "option.create", {"text": "testtesttest", "meeting_id": 111, "weight": 10}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("option/1")
        assert model.get("text") == "testtesttest"
        assert model.get("meeting_id") == 111
        assert model.get("weight") == 10

    def test_create_without_text_and_content_object_id(self) -> None:
        response = self.request("option.create", {"meeting_id": 111, "weight": 10})
        self.assert_status_code(response, 400)
        assert (
            "Need one of text, content_object_id or poll_candidate_user_ids."
            in response.json["message"]
        )

    def test_create_with_both_text_and_content_object_id(self) -> None:
        self.set_models(
            {
                "motion/112": {
                    "sequential_number": 11,
                    "title": "mosh pit",
                    "state_id": 111,
                    "meeting_id": 111,
                },
                "list_of_speakers/23": {
                    "content_object_id": "motion/112",
                    "sequential_number": 11,
                    "meeting_id": 111,
                },
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
        self.assert_model_exists("option/1", {"vote_ids": [1, 2, 3], "text": "test"})
        self.assert_model_exists(
            "vote/1", {"value": "Y", "weight": Decimal("1.000000"), "option_id": 1}
        )
        self.assert_model_exists(
            "vote/2", {"value": "N", "weight": Decimal("2.500000"), "option_id": 1}
        )
        self.assert_model_exists(
            "vote/3", {"value": "A", "weight": Decimal("0.666667"), "option_id": 1}
        )
