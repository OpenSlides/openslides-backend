from openslides_backend.models.models import Poll
from tests.system.action.base import BaseActionTestCase


class CreatePoll(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "assignment/1": {
                    "title": "test_assignment_ohneivoh9caiB8Yiungo",
                    "open_posts": 1,
                    "meeting_id": 113,
                },
                "meeting/113": {},
                "organisation/1": {"enable_electronic_voting": True},
                "user/3": {"username": "User3"}
            },
        )

    def test_create_correct(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "content_object_id": "assignment/1",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 113,
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "amount_global_yes": "1.000000",
                "amount_global_no": "1.250000",
                "amount_global_abstain": "2.500000",
                "onehundred_percent_base": "Y",
                "majority_method": "simple",
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("title") == "test"
        assert poll.get("type") == "analog"
        assert poll.get("content_object_id") == "assignment/1"
        assert poll.get("pollmethod") == "Y"
        assert poll.get("meeting_id") == 113
        assert poll.get("option_ids") == [1]
        assert poll.get("global_option_id") == 2
        assert poll.get("state") == "finished"
        assert poll.get("onehundred_percent_base") == "Y"
        assert poll.get("majority_method") == "simple"
        option = self.get_model("option/1")
        assert option.get("text") == "test2"
        assert option.get("poll_id") == 1
        assert option.get("meeting_id") == 113
        global_option = self.get_model("option/2")
        assert global_option.get("text") == "global option"
        assert global_option.get("used_as_global_option_in_poll_id") == 1
        assert global_option.get("meeting_id") == 113
        assert global_option.get("yes") == "1.000000"
        assert global_option.get("no") == "1.250000"
        assert global_option.get("abstain") == "2.500000"

    def test_create_three_options(self) -> None:
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "poll.create",
                    "data": [
                        {
                            "title": "test",
                            "type": "analog",
                            "pollmethod": "YNA",
                            "options": [
                                {"text": "test2", "Y": "10.000000"},
                                {"text": "test3", "N": "0.999900"},
                                {"text": "test4", "N": "11.000000"},
                            ],
                            "meeting_id": 113,
                            "onehundred_percent_base": "YNA",
                            "majority_method": "simple",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("title") == "test"
        assert poll.get("type") == "analog"
        assert poll.get("pollmethod") == "YNA"
        assert poll.get("meeting_id") == 113
        assert poll.get("option_ids") == [1, 2, 3]
        assert poll.get("global_option_id") == 4
        assert poll.get("onehundred_percent_base") == "YNA"
        assert poll.get("majority_method") == "simple"
        option = self.get_model("option/1")
        assert option.get("text") == "test2"
        assert option.get("poll_id") == 1
        assert option.get("meeting_id") == 113
        assert option.get("yes") == "10.000000"
        assert option.get("weight") == 1
        option_2 = self.get_model("option/2")
        assert option_2.get("text") == "test3"
        assert option_2.get("poll_id") == 1
        assert option_2.get("meeting_id") == 113
        assert option_2.get("no") == "0.999900"
        assert option_2.get("weight") == 2
        option_3 = self.get_model("option/3")
        assert option_3.get("text") == "test4"
        assert option_3.get("poll_id") == 1
        assert option_3.get("meeting_id") == 113
        assert option_3.get("no") == "11.000000"
        assert option_3.get("weight") == 3
        option_4 = self.get_model("option/4")
        assert option_4.get("text") == "global option"
        assert option_4.get("used_as_global_option_in_poll_id") == 1
        assert option_4.get("meeting_id") == 113
        assert option_4.get("weight") == 1

    def test_all_fields(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_ahThai4pae1pi4xoogoo",
                "pollmethod": "YN",
                "type": "pseudoanonymous",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "majority_method": "three_quarters",
                "global_yes": False,
                "global_no": False,
                "global_abstain": False,
                "description": "test_description_ieM8ThuasoSh8aecai8p",
                "meeting_id": 113,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("title"), "test_title_ahThai4pae1pi4xoogoo")
        self.assertEqual(poll.get("pollmethod"), "YN")
        self.assertEqual(poll.get("type"), "pseudoanonymous")
        self.assertFalse(poll.get("global_yes"))
        self.assertFalse(poll.get("global_no"))
        self.assertFalse(poll.get("global_abstain"))
        self.assertEqual(
            poll.get("description"), "test_description_ieM8ThuasoSh8aecai8p"
        )
        self.assertEqual(poll.get("onehundred_percent_base"), "YN")
        self.assertEqual(poll.get("majority_method"), "three_quarters")

    def test_no_options(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_eing5eipue5cha2Iefai",
                "pollmethod": "YNA",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "majority_method": "simple",
                "meeting_id": 113,
                "options": [],
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")

    def test_invalid_options(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_eing5eipue5cha2Iefai",
                "pollmethod": "YNA",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "majority_method": "simple",
                "meeting_id": 113,
                "options": [{}],
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")

    def test_missing_keys(self) -> None:
        complete_request_data = {
            "title": "test_title_keugh8Iu9ciyooGaevoh",
            "pollmethod": "YNA",
            "type": "named",
            "meeting_id": 113,
            "options": [{"text": "test"}],
        }
        for key in complete_request_data.keys():
            request_data = {
                _key: value
                for _key, value in complete_request_data.items()
                if _key != key
            }
            response = self.request("poll.create", request_data)
            self.assert_status_code(response, 400)
            self.assert_model_not_exists("poll/1")

    def test_with_groups(self) -> None:
        self.create_model("group/1", {"meeting_id": 113})
        self.create_model("group/2", {"meeting_id": 113})
        response = self.request(
            "poll.create",
            {
                "title": "test_title_Thoo2eiphohhi1eeXoow",
                "pollmethod": "YNA",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "majority_method": "simple",
                "entitled_group_ids": [1, 2],
                "meeting_id": 113,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("entitled_group_ids") == [1, 2]

    def test_with_empty_groups(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_Thoo2eiphohhi1eeXoow",
                "pollmethod": "YNA",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "majority_method": "simple",
                "entitled_group_ids": [],
                "meeting_id": 113,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("entitled_group_ids"), [])

    def test_not_supported_type(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_yaiyeighoh0Iraet3Ahc",
                "pollmethod": "YNA",
                "type": "not_existing",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "majority_method": "simple",
                "meeting_id": 113,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")

    def test_not_allowed_type(self) -> None:
        self.update_model("organisation/1", {"enable_electronic_voting": False})
        response = self.request(
            "poll.create",
            {
                "title": "test_title_yaiyeighoh0Iraet3Ahc",
                "pollmethod": "YNA",
                "type": Poll.TYPE_NAMED,
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "majority_method": "simple",
                "meeting_id": 113,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")

    def test_not_supported_pollmethod(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_SeVaiteYeiNgie5Xoov8",
                "pollmethod": "not_existing",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "majority_method": "simple",
                "meeting_id": 113,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")

    def test_not_supported_onehundred_percent_base(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_Thoo2eiphohhi1eeXoow",
                "pollmethod": "YNA",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "invalid base",
                "majority_method": "simple",
                "meeting_id": 113,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")

    def test_not_supported_majority_method(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_Thoo2eiphohhi1eeXoow",
                "pollmethod": "YNA",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "majority_method": "invalid majority method",
                "meeting_id": 113,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")

    def test_wrong_pollmethod_onehundred_percent_base_combination_1(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_Thoo2eiphohhi1eeXoow",
                "pollmethod": "Y",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "majority_method": "simple",
                "meeting_id": 113,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "This onehundred_percent_base not allowed in this pollmethod"
            in response.data.decode()
        )
        self.assert_model_not_exists("poll/1")

    def test_wrong_pollmethod_onehundred_percent_base_combination_2(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_Thoo2eiphohhi1eeXoow",
                "pollmethod": "YN",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YNA",
                "majority_method": "simple",
                "meeting_id": 113,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "This onehundred_percent_base not allowed in this pollmethod"
            in response.data.decode()
        )
        self.assert_model_not_exists("poll/1")

    def test_wrong_pollmethod_onehundred_percent_base_combination_3(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_Thoo2eiphohhi1eeXoow",
                "pollmethod": "Y",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YNA",
                "majority_method": "simple",
                "meeting_id": 113,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "This onehundred_percent_base not allowed in this pollmethod"
            in response.data.decode()
        )
        self.assert_model_not_exists("poll/1")

    def test_create_poll_for_option_with_wrong_content_object(self) -> None:
        response = self.request_json(
            [
                {
                    "action": "poll.create",
                    "data": [
                        {
                            "meeting_id": 113,
                            "title": "Wahlgang (3)",
                            "majority_method": "simple",
                            "onehundred_percent_base": "valid",
                            "pollmethod": "YN",
                            "type": "analog",
                            "options": [{"content_object_id": "assignment/1"}],
                            "content_object_id": "assignment/1",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The collection 'assignment' is not available for field 'content_object_id' in collection 'option'.",
            response.json["message"],
        )
