import typing

from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from .base_poll_test import BasePollTestCase


class CreatePoll(BasePollTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_meeting()
        self.set_models(
            {
                "assignment/1": {
                    "title": "test_assignment_ohneivoh9caiB8Yiungo",
                    "open_posts": 1,
                    "meeting_id": 1,
                },
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
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
                "max_votes_per_option": 1,
                "backend": "long",
                "amount_global_yes": "2.000000",
            },
        )
        self.assert_status_code(response, 200)
        poll = self.assert_model_exists(
            "poll/1",
            {
                "title": "test",
                "type": "analog",
                "content_object_id": "assignment/1",
                "pollmethod": "Y",
                "meeting_id": 1,
                "option_ids": [1],
                "global_option_id": 2,
                "state": "finished",
                "onehundred_percent_base": "Y",
                "is_pseudoanonymized": False,
                "min_votes_amount": 5,
                "max_votes_amount": 10,
                "max_votes_per_option": 1,
                "backend": "long",
                "sequential_number": 1,
            },
        )
        assert "options" not in poll
        self.assert_model_exists(
            "option/1",
            {"text": "test2", "poll_id": 1, "meeting_id": 1, "yes": "10.000000"},
        )
        self.assert_model_exists(
            "option/2",
            {
                "text": "global option",
                "used_as_global_option_in_poll_id": 1,
                "meeting_id": 1,
                "yes": "2.000000",
                "no": "-2.000000",
            },
        )
        self.assert_history_information("assignment/1", ["Ballot created"])

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
                "max_votes_per_option": 1,
                "publish_immediately": True,
            },
        )
        self.assert_status_code(response, 200)
        poll = self.assert_model_exists("poll/1", {"state": "published"})
        assert "publish_immediately" not in poll

    def test_create_correct_default_values(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "content_object_id": "assignment/1",
                "pollmethod": "YN",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 1,
                "onehundred_percent_base": "Y",
                "votesvalid": "3.000000",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1", {"votesvalid": "3.000000", "votesinvalid": "-2.000000"}
        )
        self.assert_model_exists("vote/1", {"value": "Y", "weight": "10.000000"})
        self.assert_model_exists("vote/2", {"value": "N", "weight": "-2.000000"})

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
                "max_votes_per_option": 1,
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
                "amount_global_yes": "5.000000",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "YNA",
                "meeting_id": 1,
                "option_ids": [1, 2, 3],
                "global_option_id": 4,
                "onehundred_percent_base": "YNA",
            },
        )
        self.assert_model_exists(
            "option/1",
            {
                "text": "test2",
                "poll_id": 1,
                "meeting_id": 1,
                "yes": "10.000000",
                "weight": 1,
            },
        )
        self.assert_model_exists(
            "option/2",
            {
                "text": "test3",
                "poll_id": 1,
                "meeting_id": 1,
                "no": "0.999900",
                "weight": 2,
            },
        )
        self.assert_model_exists(
            "option/3",
            {
                "text": "test4",
                "poll_id": 1,
                "meeting_id": 1,
                "no": "11.000000",
                "weight": 3,
            },
        )
        option_4 = self.assert_model_exists(
            "option/4",
            {
                "text": "global option",
                "used_as_global_option_in_poll_id": 1,
                "meeting_id": 1,
                "weight": 1,
            },
        )
        assert option_4.get("yes") is None

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
        self.assert_model_exists(
            "poll/1",
            {
                "title": "test_title_ahThai4pae1pi4xoogoo",
                "pollmethod": "YN",
                "type": "pseudoanonymous",
                "is_pseudoanonymized": True,
                "global_yes": False,
                "global_no": False,
                "global_abstain": False,
                "description": "test_description_ieM8ThuasoSh8aecai8p",
                "onehundred_percent_base": "YN",
            },
        )

    def test_create_wrong_publish_immediately(self) -> None:
        response = self.request(
            "poll.create",
            {
                "content_object_id": "assignment/1",
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
        self.assertIn(
            "Need one of text, content_object_id or poll_candidate_user_ids.",
            response.json["message"],
        )
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
        self.assert_model_exists("poll/1", {"entitled_group_ids": [1, 2]})

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
        self.assert_model_exists("poll/1", {"entitled_group_ids": []})

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
        self.update_model(ONE_ORGANIZATION_FQID, {"enable_electronic_voting": False})
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
            "data.onehundred_percent_base must be one of ['Y', 'YN', 'YNA', 'N', 'valid', 'cast', 'entitled', 'entitled_present', 'disabled']",
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
        self.set_models(
            {
                "meeting_user/1": {"meeting_id": 1, "user_id": 1},
                "user/1": {"meeting_ids": [1]},
            }
        )
        self.set_user_groups(1, [1])
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "YN",
                "onehundred_percent_base": "valid",
                "options": [
                    {
                        "content_object_id": "user/1",
                        "Y": "10.000000",
                        "N": "5.000000",
                    },
                    {"text": "text", "Y": "10.000000"},
                ],
                "meeting_id": 1,
                "content_object_id": "assignment/1",
            },
        )
        self.assert_status_code(response, 200)

    def test_analog_poll_without_YNA_values(self) -> None:
        self.set_models(
            {
                "motion/3": {"meeting_id": 1, "state_id": 444},
                "motion_state/444": {"meeting_id": 1, "allow_create_poll": True},
            }
        )
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
        self.assert_history_information("motion/3", ["Voting created"])

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
        self.assert_model_exists("poll/1", {"state": "created"})

    def test_create_user_option_valid(self) -> None:
        self.create_meeting(42)
        self.set_models(
            {
                "meeting/42": {
                    "meeting_user_ids": [1],
                },
                "group/5": {"meeting_id": 42, "meeting_user_ids": [1]},
                "user/1": {
                    "meeting_user_ids": [1],
                    "meeting_ids": [42],
                },
                "meeting_user/1": {
                    "meeting_id": 42,
                    "user_id": 1,
                    "group_ids": [5],
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
            "option/1",
            {"content_object_id": "user/1", "poll_id": 1, "meeting_id": 42},
        )

    def test_create_user_option_invalid(self) -> None:
        self.create_meeting(7)
        self.create_meeting(42)
        self.set_models(
            {
                "meeting/42": {"meeting_user_ids": [1]},
                "group/5": {"meeting_id": 42, "meeting_user_ids": [1]},
                "user/1": {
                    "meeting_user_ids": [1],
                    "meeting_ids": [42],
                },
                "meeting_user/1": {
                    "meeting_id": 42,
                    "user_id": 1,
                    "group_ids": [5],
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
        assert response.json["message"] == "No 'content_object_id' was given"

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
            Permissions.Assignment.CAN_MANAGE_POLLS,
        )

    def test_create_permissions_assignment_not_working_with_just_can_manage(
        self,
    ) -> None:
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
            fail=True,
        )

    def test_create_permissions_assignment_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
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

    def test_create_forbidden_to_create_poll(self) -> None:
        self.set_models(
            {
                "motion/23": {"meeting_id": 1, "state_id": 444},
                "motion_state/444": {"meeting_id": 1, "allow_create_poll": False},
            }
        )
        response = self.request(
            "poll.create",
            {
                "meeting_id": 1,
                "title": "Abstimmung",
                "onehundred_percent_base": "YNA",
                "pollmethod": "YNA",
                "type": "analog",
                "options": [{"content_object_id": "motion/23"}],
                "content_object_id": "motion/23",
            },
        )
        self.assert_status_code(response, 400)
        assert "Motion state doesn't allow to create poll." in response.json["message"]

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
            {
                "motion/23": {"meeting_id": 1, "state_id": 444},
                "motion_state/444": {"meeting_id": 1, "allow_create_poll": True},
            },
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

    def test_non_negative_max_votes_per_option(self) -> None:
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
                "max_votes_per_option": -1,
                "backend": "long",
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")

    def test_max_votes_per_option_smaller_max_votes_amount(self) -> None:
        """Also asserts that default values are respected."""
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 1,
                "max_votes_per_option": 2,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "The maximum votes per option cannot be higher than the maximum amount of votes in total."
        )
        self.assert_model_not_exists("poll/1")

    def test_max_votes_amount_smaller_min(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": "analog",
                "pollmethod": "Y",
                "options": [{"text": "test2", "Y": "10.000000"}],
                "meeting_id": 1,
                "min_votes_amount": 5,
                "max_votes_amount": 2,
                "max_votes_per_option": 2,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            response.json["message"]
            == "The minimum amount of votes cannot be higher than the maximum amount of votes."
        )
        self.assert_model_not_exists("poll/1")

    def test_create_poll_candidate_list(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": Poll.TYPE_NAMED,
                "content_object_id": "assignment/1",
                "pollmethod": "YNA",
                "options": [{"poll_candidate_user_ids": [1, 3]}],
                "meeting_id": 1,
                "backend": "long",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("assignment/1", {"poll_ids": [1]})
        self.assert_model_exists(
            "poll/1",
            {"title": "test", "option_ids": [1], "content_object_id": "assignment/1"},
        )
        self.assert_model_exists(
            "option/1", {"content_object_id": "poll_candidate_list/1", "poll_id": 1}
        )
        self.assert_model_exists(
            "poll_candidate_list/1",
            {"option_id": 1, "meeting_id": 1, "poll_candidate_ids": [1, 2]},
        )
        self.assert_model_exists(
            "poll_candidate/1",
            {"user_id": 1, "weight": 1, "poll_candidate_list_id": 1, "meeting_id": 1},
        )
        self.assert_model_exists(
            "poll_candidate/2",
            {"user_id": 3, "weight": 2, "poll_candidate_list_id": 1, "meeting_id": 1},
        )
        self.assert_model_exists(
            "meeting/1", {"poll_candidate_list_ids": [1], "poll_candidate_ids": [1, 2]}
        )
        self.assert_model_exists(
            "meeting/1",
            {
                "poll_ids": [1],
                "option_ids": [1, 2],
                "poll_candidate_ids": [1, 2],
                "poll_candidate_list_ids": [1],
            },
        )

    def test_create_poll_candidate_lists(self) -> None:
        self.set_models(
            {
                "user/2": {"username": "User2"},
                "user/4": {"username": "User4"},
            }
        )
        response = self.request(
            "poll.create",
            {
                "title": "test",
                "type": Poll.TYPE_PSEUDOANONYMOUS,
                "content_object_id": "assignment/1",
                "pollmethod": "YNA",
                "options": [
                    {"poll_candidate_user_ids": [1, 3]},
                    {"poll_candidate_user_ids": [2, 4]},
                ],
                "meeting_id": 1,
                "backend": "long",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "title": "test",
                "option_ids": [1, 2],
                "content_object_id": "assignment/1",
            },
        )
        self.assert_model_exists(
            "option/1", {"content_object_id": "poll_candidate_list/1", "poll_id": 1}
        )
        self.assert_model_exists(
            "option/2", {"content_object_id": "poll_candidate_list/2", "poll_id": 1}
        )
        self.assert_model_exists(
            "poll_candidate_list/1",
            {"option_id": 1, "meeting_id": 1, "poll_candidate_ids": [1, 2]},
        )
        self.assert_model_exists(
            "poll_candidate_list/2",
            {"option_id": 2, "meeting_id": 1, "poll_candidate_ids": [3, 4]},
        )

    def test_with_anonymous_in_entitled_group_ids(self) -> None:
        self.create_meeting()
        self.set_anonymous()
        response = self.request(
            "poll.create",
            {
                "meeting_id": 1,
                "options": [{"text": "test"}],
                "pollmethod": "YNA",
                "title": "test",
                "type": Poll.TYPE_NAMED,
                "entitled_group_ids": [4],
                "content_object_id": "assignment/1",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Anonymous group is not allowed in entitled_group_ids.",
            response.json["message"],
        )

    def test_live_voting_named_motion_poll(self) -> None:
        self.set_models(
            {
                "motion/3": {"meeting_id": 1, "state_id": 444},
                "motion_state/444": {"meeting_id": 1, "allow_create_poll": True},
            }
        )
        response = self.request(
            "poll.create",
            {
                "title": "test_title_yaiyeighoh0Iraet3Ahc",
                "pollmethod": "YNA",
                "type": Poll.TYPE_NAMED,
                "content_object_id": "motion/3",
                "onehundred_percent_base": "YN",
                "meeting_id": 1,
                "options": [{"text": "test"}],
                "live_voting_enabled": True,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1", {"type": Poll.TYPE_NAMED, "live_voting_enabled": True}
        )

    def test_live_voting_named_assignment_poll(self) -> None:
        self.base_live_voting_assigment()

    def test_live_votng_named_assignment_poll_wrong_pollmethod(self) -> None:
        self.base_live_voting_assigment({"pollmethod": "YN"})

    def test_live_votng_named_assignment_poll_wrong_globalyes(self) -> None:
        self.base_live_voting_assigment({"global_yes": True})

    def test_live_votng_named_assignment_poll_wrong_max_votes(self) -> None:
        self.base_live_voting_assigment({"max_votes_amount": 2})

    def base_live_voting_assigment(
        self, error_dict: dict[str, typing.Any] | None = None
    ) -> None:
        self.set_models(
            {
                "assignment/3": {"meeting_id": 1},
            }
        )

        response = self.request(
            "poll.create",
            {
                "title": "test_title_yaiyeighoh0Iraet3Ahc",
                "pollmethod": "Y",
                "type": Poll.TYPE_NAMED,
                "content_object_id": "assignment/3",
                "onehundred_percent_base": "Y",
                "meeting_id": 1,
                "options": [{"text": "test"}],
                "live_voting_enabled": True,
                **(error_dict if error_dict else {}),
            },
        )
        if not error_dict:
            self.assert_status_code(response, 200)
            self.assert_model_exists(
                "poll/1", {"type": Poll.TYPE_NAMED, "live_voting_enabled": True}
            )
        else:
            self.assert_status_code(response, 400)
            self.assert_model_not_exists("poll/1")
            assert (
                "live_voting_enabled only allowed for named motion polls and named Yes assignment polls."
            ) in response.json["message"]

    def test_live_voting_not_allowed_type_analog(self) -> None:
        self.base_live_voting_not_allowed(Poll.TYPE_ANALOG, True)

    def test_live_voting_not_allowed_type_pseudoanonymous(self) -> None:
        self.base_live_voting_not_allowed(Poll.TYPE_PSEUDOANONYMOUS, True)

    def test_live_voting_not_allowed_is_motion_poll_false(self) -> None:
        self.base_live_voting_not_allowed(Poll.TYPE_NAMED, False)

    def base_live_voting_not_allowed(
        self, poll_type: str, is_motion_poll: bool
    ) -> None:
        request_data = {
            "title": "test_title_yaiyeighoh0Iraet3Ahc",
            "pollmethod": "YNA",
            "type": poll_type,
            "content_object_id": "assignment/1",
            "onehundred_percent_base": "YN",
            "meeting_id": 1,
            "options": [{"text": "test"}],
            "live_voting_enabled": True,
        }
        if is_motion_poll:
            self.set_models(
                {
                    "motion/3": {"meeting_id": 1, "state_id": 444},
                    "motion_state/444": {"meeting_id": 1, "allow_create_poll": True},
                }
            )
            request_data["content_object_id"] = "motion/3"

        response = self.request("poll.create", request_data)
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")
        assert (
            "live_voting_enabled only allowed for named motion polls and named Yes assignment polls."
        ) in response.json["message"]
