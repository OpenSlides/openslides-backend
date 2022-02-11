from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class CreatePoll(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "assignment/1": {
                    "title": "test_assignment_ohneivoh9caiB8Yiungo",
                    "open_posts": 1,
                    "meeting_id": 1,
                },
                "meeting/1": {"is_active_in_organization_id": 1},
                "organization/1": {"enable_electronic_voting": True},
                "user/3": {"username": "User3"},
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
                "meeting_id": 1,
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "onehundred_percent_base": "Y",
                "min_votes_amount": 5,
                "max_votes_amount": 10,
                "max_votes_per_person": 1,
                "backend": "long",
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("title") == "test"
        assert poll.get("type") == "analog"
        assert poll.get("content_object_id") == "assignment/1"
        assert poll.get("pollmethod") == "Y"
        assert poll.get("meeting_id") == 1
        assert poll.get("option_ids") == [1]
        assert poll.get("global_option_id") == 2
        assert poll.get("state") == "finished"
        assert poll.get("onehundred_percent_base") == "Y"
        assert poll.get("is_pseudoanonymized") is False
        assert poll.get("min_votes_amount") == 5
        assert poll.get("max_votes_amount") == 10
        assert poll.get("max_votes_per_person") == 1
        assert poll.get("backend") == "long"
        assert poll.get("sequential_number") == 1
        assert "options" not in poll
        option = self.get_model("option/1")
        assert option.get("text") == "test2"
        assert option.get("poll_id") == 1
        assert option.get("meeting_id") == 1
        global_option = self.get_model("option/2")
        assert global_option.get("text") == "global option"
        assert global_option.get("used_as_global_option_in_poll_id") == 1
        assert global_option.get("meeting_id") == 1

    def test_create_correct_publish_immediately(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "content_object_id": "assignment/1",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 1,
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "onehundred_percent_base": "Y",
                "min_votes_amount": 5,
                "max_votes_amount": 10,
                "max_votes_per_person": 1,
                "publish_immediately": True,
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "published"

    def test_create_correct_with_topic(self) -> None:
        self.set_models(
            {
                "topic/12": {
                    "title": "Wichtiges Topic",
                    "text": "blablabla",
                    "meeting_id": 1,
                }
            }
        )

        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "content_object_id": "topic/12",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 1,
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "onehundred_percent_base": "Y",
                "min_votes_amount": 5,
                "max_votes_amount": 10,
                "max_votes_per_person": 1,
                "publish_immediately": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("poll/1", {"content_object_id": "topic/12"})
        self.assert_model_exists(
            "topic/12",
            {
                "title": "Wichtiges Topic",
                "text": "blablabla",
                "meeting_id": 1,
                "poll_ids": [1],
            },
        )

    def test_create_three_options(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "YNA",
                "options": [
                    {"text": "test2", "Y": "10.000000"},
                    {"text": "test3", "N": "0.999900"},
                    {"text": "test4", "N": "11.000000"},
                ],
                "meeting_id": 1,
                "onehundred_percent_base": "YNA",
                "content_object_id": "assignment/1",
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("title") == "test"
        assert poll.get("type") == "analog"
        assert poll.get("pollmethod") == "YNA"
        assert poll.get("meeting_id") == 1
        assert poll.get("option_ids") == [1, 2, 3]
        assert poll.get("global_option_id") == 4
        assert poll.get("onehundred_percent_base") == "YNA"
        option = self.get_model("option/1")
        assert option.get("text") == "test2"
        assert option.get("poll_id") == 1
        assert option.get("meeting_id") == 1
        assert option.get("yes") == "10.000000"
        assert option.get("weight") == 1
        option_2 = self.get_model("option/2")
        assert option_2.get("text") == "test3"
        assert option_2.get("poll_id") == 1
        assert option_2.get("meeting_id") == 1
        assert option_2.get("no") == "0.999900"
        assert option_2.get("weight") == 2
        option_3 = self.get_model("option/3")
        assert option_3.get("text") == "test4"
        assert option_3.get("poll_id") == 1
        assert option_3.get("meeting_id") == 1
        assert option_3.get("no") == "11.000000"
        assert option_3.get("weight") == 3
        option_4 = self.get_model("option/4")
        assert option_4.get("text") == "global option"
        assert option_4.get("used_as_global_option_in_poll_id") == 1
        assert option_4.get("meeting_id") == 1
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
                "global_yes": False,
                "global_no": False,
                "global_abstain": False,
                "description": "test_description_ieM8ThuasoSh8aecai8p",
                "meeting_id": 1,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("title"), "test_title_ahThai4pae1pi4xoogoo")
        self.assertEqual(poll.get("pollmethod"), "YN")
        self.assertEqual(poll.get("type"), "pseudoanonymous")
        self.assertTrue(poll.get("is_pseudoanonymized"))
        self.assertFalse(poll.get("global_yes"))
        self.assertFalse(poll.get("global_no"))
        self.assertFalse(poll.get("global_abstain"))
        self.assertEqual(
            poll.get("description"), "test_description_ieM8ThuasoSh8aecai8p"
        )
        self.assertEqual(poll.get("onehundred_percent_base"), "YN")

    def test_create_wrong_publish_immediately(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_ahThai4pae1pi4xoogoo",
                "pollmethod": "YN",
                "type": "pseudoanonymous",
                "meeting_id": 1,
                "options": [{"text": "test"}],
                "publish_immediately": True,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "publish_immediately only allowed for analog polls."
            in response.json["message"]
        )

    def test_no_options(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_eing5eipue5cha2Iefai",
                "pollmethod": "YNA",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "meeting_id": 1,
                "options": [],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.options must contain at least 1 items", response.json["message"]
        )
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
                "meeting_id": 1,
                "options": [{}],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn("Need text xor content_object_id.", response.json["message"])
        self.assert_model_not_exists("poll/1")

    def test_missing_keys(self) -> None:
        complete_request_data = {
            "title": "test_title_keugh8Iu9ciyooGaevoh",
            "pollmethod": "YNA",
            "type": "named",
            "meeting_id": 1,
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
        self.set_models({"group/1": {"meeting_id": 1}, "group/2": {"meeting_id": 1}})
        response = self.request(
            "poll.create",
            {
                "title": "test_title_Thoo2eiphohhi1eeXoow",
                "pollmethod": "YNA",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "entitled_group_ids": [1, 2],
                "meeting_id": 1,
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
                "entitled_group_ids": [],
                "meeting_id": 1,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("entitled_group_ids"), [])

    def test_with_groups_and_analog(self) -> None:
        self.set_models({"group/1": {"meeting_id": 1}, "group/2": {"meeting_id": 1}})
        response = self.request(
            "poll.create",
            {
                "title": "test_title_Thoo2eiphohhi1eeXoow",
                "pollmethod": "YNA",
                "type": "analog",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "entitled_group_ids": [1, 2],
                "meeting_id": 1,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "entitled_group_ids is not allowed for analog." in response.json["message"]
        )

    def test_with_100_percent_base_entitled_and_analog(self) -> None:
        self.set_models({"group/1": {"meeting_id": 1}, "group/2": {"meeting_id": 1}})
        response = self.request(
            "poll.create",
            {
                "title": "test_title_Thoo2eiphohhi1eeXoow",
                "pollmethod": "YNA",
                "type": "analog",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "entitled",
                "meeting_id": 1,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "onehundred_percent_base: value entitled is not allowed for analog."
            in response.json["message"]
        )

    def test_not_supported_type(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_yaiyeighoh0Iraet3Ahc",
                "pollmethod": "YNA",
                "type": "not_existing",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "meeting_id": 1,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")

    def test_not_allowed_type(self) -> None:
        self.update_model("organization/1", {"enable_electronic_voting": False})
        response = self.request(
            "poll.create",
            {
                "title": "test_title_yaiyeighoh0Iraet3Ahc",
                "pollmethod": "YNA",
                "type": Poll.TYPE_NAMED,
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "meeting_id": 1,
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
                "meeting_id": 1,
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
                "meeting_id": 1,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data.onehundred_percent_base must be one of ['Y', 'YN', 'YNA', 'N', 'valid', 'cast', 'entitled', 'disabled']",
            response.json["message"],
        )
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
                "meeting_id": 1,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "This onehundred_percent_base not allowed in this pollmethod"
            in response.json["message"]
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
                "meeting_id": 1,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "This onehundred_percent_base not allowed in this pollmethod"
            in response.json["message"]
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
                "meeting_id": 1,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "This onehundred_percent_base not allowed in this pollmethod"
            in response.json["message"]
        )
        self.assert_model_not_exists("poll/1")

    def test_create_poll_for_option_with_wrong_content_object(self) -> None:
        response = self.request(
            "poll.create",
            {
                "meeting_id": 1,
                "title": "Wahlgang (3)",
                "onehundred_percent_base": "valid",
                "pollmethod": "YN",
                "type": "analog",
                "options": [{"content_object_id": "assignment/1"}],
                "content_object_id": "assignment/1",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "The collection 'assignment' is not available for field 'content_object_id' in collection 'option'.",
            response.json["message"],
        )

    def test_unique_error_options_text(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "YNA",
                "onehundred_percent_base": "valid",
                "options": [
                    {"text": "test", "Y": "10.000000"},
                    {"text": "test", "A": "11.000000"},
                    {"text": "test", "N": "12.000000"},
                ],
                "meeting_id": 1,
                "content_object_id": "assignment/1",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Duplicated option in poll.options: test", response.json["message"]
        )

    def test_unique_error_options_content_object_id(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "YNA",
                "options": [
                    {"content_object_id": "user/1", "Y": "10.000000"},
                    {"text": "test4", "N": "11.000000"},
                    {"content_object_id": "user/1", "Y": "11.000000"},
                ],
                "meeting_id": 1,
                "content_object_id": "assignment/1",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Duplicated option in poll.options: user/1", response.json["message"]
        )

    def test_unique_no_error_mixed_text_content_object_id_options(self) -> None:
        self.create_meeting()
        self.set_user_groups(1, [1])
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "YN",
                "onehundred_percent_base": "valid",
                "options": [
                    {"content_object_id": "user/1", "Y": "10.000000", "N": "5.000000"},
                    {"text": "text", "Y": "10.000000"},
                ],
                "meeting_id": 1,
                "content_object_id": "assignment/1",
            },
        )
        self.assert_status_code(response, 200)

    def test_analog_poll_without_YNA_values(self) -> None:
        self.create_model("motion/3", {"meeting_id": 1})
        response = self.request(
            "poll.create",
            {
                "meeting_id": 1,
                "title": "Abstimmung",
                "onehundred_percent_base": "YNA",
                "pollmethod": "YNA",
                "type": "analog",
                "options": [{"content_object_id": "motion/3"}],
                "content_object_id": "motion/3",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "option/1",
            {
                "content_object_id": "motion/3",
                "vote_ids": [1, 2, 3],
                "yes": "-2.000000",
                "no": "-2.000000",
                "abstain": "-2.000000",
                "weight": 1,
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "text": "global option",
                "used_as_global_option_in_poll_id": 1,
                "weight": 1,
            },
        )

    def test_not_state_change(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_eing5eipue5cha2Iefai",
                "pollmethod": "YNA",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "meeting_id": 1,
                "options": [{"text": "test1"}],
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("state") == "created"

    def test_create_user_option_valid(self) -> None:
        self.set_models(
            {
                "meeting/42": {"is_active_in_organization_id": 1},
                "group/5": {"meeting_id": 42, "user_ids": [1]},
                "user/1": {
                    "group_$42_ids": [5],
                    "group_$_ids": ["42"],
                    "meeting_ids": [42],
                },
                "assignment/2": {
                    "meeting_id": 42,
                },
            }
        )
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "YNA",
                "options": [
                    {"content_object_id": "user/1"},
                ],
                "meeting_id": 42,
                "onehundred_percent_base": "YN",
                "content_object_id": "assignment/2",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "option_ids": [1],
                "meeting_id": 42,
            },
        )
        self.assert_model_exists(
            "option/1", {"content_object_id": "user/1", "poll_id": 1, "meeting_id": 42}
        )

    def test_create_user_option_invalid(self) -> None:
        self.set_models(
            {
                "meeting/42": {},
                "meeting/7": {"is_active_in_organization_id": 1},
                "group/5": {"meeting_id": 42, "user_ids": [1]},
                "user/1": {
                    "group_$42_ids": [5],
                    "group_$_ids": ["42"],
                    "meeting_ids": [42],
                },
            }
        )
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "YNA",
                "options": [
                    {"content_object_id": "user/1"},
                ],
                "meeting_id": 7,
                "onehundred_percent_base": "YN",
                "content_object_id": "assignment/1",
            },
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "The following models do not belong to meeting 7: ['user/1']"
        )

    def test_create_without_content_object(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_eing5eipue5cha2Iefai",
                "pollmethod": "YNA",
                "type": "named",
                "onehundred_percent_base": "YN",
                "meeting_id": 1,
                "options": [{"text": "test1"}],
            },
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "Creation of poll/1: You try to set following required fields to an empty value: ['content_object_id']"
        )

    def test_create_no_permissions_assignment(self) -> None:
        self.base_permission_test(
            {},
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "content_object_id": "assignment/1",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 1,
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "onehundred_percent_base": "Y",
            },
        )

    def test_create_permissions_assignment(self) -> None:
        self.base_permission_test(
            {},
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "content_object_id": "assignment/1",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 1,
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "onehundred_percent_base": "Y",
            },
            Permissions.Assignment.CAN_MANAGE,
        )

    def test_create_no_permissions_motion(self) -> None:
        self.base_permission_test(
            {"motion/23": {"meeting_id": 1}},
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "content_object_id": "motion/23",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 1,
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "onehundred_percent_base": "Y",
            },
        )

    def test_create_permissions_motion(self) -> None:
        self.base_permission_test(
            {"motion/23": {"meeting_id": 1}},
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "content_object_id": "motion/23",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 1,
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "onehundred_percent_base": "Y",
            },
            Permissions.Motion.CAN_MANAGE_POLLS,
        )

    def test_create_no_permissions_topic(self) -> None:
        self.set_models(
            {"meeting/1": {"topic_ids": [13]}, "topic/13": {"meeting_id": 1}}
        )
        self.base_permission_test(
            {},
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 1,
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "onehundred_percent_base": "Y",
                "content_object_id": "topic/1",
            },
        )

    def test_create_permissions_topic(self) -> None:
        self.set_models(
            {"meeting/1": {"topic_ids": [13]}, "topic/13": {"meeting_id": 1}}
        )
        self.base_permission_test(
            {},
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 1,
                "global_yes": True,
                "global_no": True,
                "global_abstain": True,
                "onehundred_percent_base": "Y",
                "content_object_id": "topic/1",
            },
        )
