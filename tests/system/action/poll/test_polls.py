from openslides_backend.models.models import Poll
from tests.system.action.base import BaseActionTestCase

GROUP_ADMIN_PK = 1
GROUP_DELEGATE_PK = 1


class CreatePoll(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_model(
            "assignment/1",
            dict(
                title="test_assignment_ohneivoh9caiB8Yiungo",
                open_posts=1,
                candidate_ids=[1],
                meeting_id=113
            ),
        )
        self.create_model("meeting/113", {})

    def test_simple(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_ailai4toogh3eefaa2Vo",
                "pollmethod": "YNA",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YN",
                "majority_method": "simple",
                "meeting_id": 113,
                "options": [{"text": "test"}],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("poll/1")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("title"), "test_title_ailai4toogh3eefaa2Vo")
        self.assertEqual(poll.get("pollmethod"), "YNA")
        self.assertEqual(poll.get("type"), "named")
        # Check defaults
        # self.assertTrue(poll.get("global_yes"))
        # self.assertTrue(poll.get("global_no"))
        # self.assertTrue(poll.get("global_abstain"))
        self.assertEqual(poll.get("amount_global_yes"), None)
        self.assertEqual(poll.get("amount_global_no"), None)
        self.assertEqual(poll.get("amount_global_abstain"), None)
        self.assertEqual(poll.get("content_object_id"), "assignment/1")
        self.assertEqual(poll.get("description"), "")
        # option = self.get_model("option/1")
        # assert option.get("user_id") == 1

    def test_all_fields(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_ahThai4pae1pi4xoogoo",
                "pollmethod": "YN",
                "type": "pseudoanonymous",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "YNA",
                "majority_method": "three_quarters",
                "global_yes": False,
                "global_no": False,
                "global_abstain": False,
                "description": "test_description_ieM8ThuasoSh8aecai8p",
                "meeting_id": 113,
                "options": [{"text":"test"}],
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

    def test_no_candidates(self) -> None:
        self.update_model("assignment/1", {"candidate_ids": []})
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
            "options": [{"text":"test"}],
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
        self.create_model("group/2", {})
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
                "options": [{"text":"test"}],
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
                "options": [{"text":"test"}],
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
                "options": [{"text":"test"}],
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")

    def test_not_allowed_type(self) -> None:
        # setattr(settings, "ENABLE_ELECTRONIC_VOTING", False)
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
                "options": [{"text":"test"}],
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")
        # setattr(settings, "ENABLE_ELECTRONIC_VOTING", True)

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
                "options": [{"text":"test"}],
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
                "options": [{"text":"test"}],
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
                "options": [{"text":"test"}],
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("poll/1")

    def test_wrong_pollmethod_onehundred_percent_base_combination_1(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_Thoo2eiphohhi1eeXoow",
                "pollmethod": "YNA",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "Y",
                "majority_method": "simple",
                "meeting_id": 113,
                "options": [{"text":"test"}],
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "YNA")

    def test_wrong_pollmethod_onehundred_percent_base_combination_2(self) -> None:
        response = self.request(
            "poll.create",
            {
                "title": "test_title_Thoo2eiphohhi1eeXoow",
                "pollmethod": "YN",
                "type": "named",
                "content_object_id": "assignment/1",
                "onehundred_percent_base": "Y",
                "majority_method": "simple",
                "meeting_id": 113,
                "options": [{"text":"test"}],
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "YN")

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
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "Y")


class UpdatePoll(BaseActionTestCase):
    """
    Tests updating polls of assignments.
    """

    def setUp(self) -> None:
        super().setUp()
        self.create_model(
            "assignment/1",
            dict(
                title="test_assignment_ohneivoh9caiB8Yiungo",
                open_posts=1,
                candidate_ids=[1],
            ),
        )
        self.create_model("meeting/113", {"name": "my meeting"})
        self.create_model("group/1", {"user_ids": [1], "poll_ids": [1]})
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_beeFaihuNae1vej2ai8m",
                pollmethod="Y",
                type=Poll.TYPE_NAMED,
                onehundred_percent_base="Y",
                majority_method="simple",
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
            ),
        )
        self.create_model("option/1", {"meeting_id": 113, "poll_id": 1})
        self.create_model("option/2", {"meeting_id": 113, "poll_id": 1})
        self.update_model(
            "user/1",
            {
                "is_present_in_meeting_ids": [113],
                "group_$113_ids": [1],
                "group_$_ids": ["113"],
            },
        )

    def test_patch_title(self) -> None:
        response = self.request(
            "poll.update",
            {"title": "test_title_Aishohh1ohd0aiSut7gi", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("title"), "test_title_Aishohh1ohd0aiSut7gi")

    def test_prevent_patching_assignment(self) -> None:
        self.create_model(
            "assignment/2", dict(title="test_title_phohdah8quukooHeetuz", open_posts=1)
        )
        response = self.request(
            "poll.update",
            {"content_object_id": "assignment/2", "id": 1},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("content_object_id"), "assignment/1")  # unchanged

    def test_patch_pollmethod(self) -> None:
        response = self.request(
            "poll.update",
            {"pollmethod": "YNA", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("pollmethod"), "YNA")
        self.assertEqual(poll.get("onehundred_percent_base"), "YNA")

    def test_patch_invalid_pollmethod(self) -> None:
        response = self.request(
            "poll.update",
            {"pollmethod": "invalid"},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("pollmethod"), "Y")

    def test_patch_type(self) -> None:
        response = self.request("poll.update", {"type": "analog", "id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("type"), "analog")

    def test_patch_invalid_type(self) -> None:
        response = self.request("poll.update", {"type": "invalid", "id": 1})
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("type"), "named")

    def test_patch_not_allowed_type(self) -> None:
        # self.update_model("organisation/1", {"enable_electronic_voting": False})
        response = self.request(
            "poll.update",
            {"type": Poll.TYPE_NAMED, "id": 1},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("type"), Poll.TYPE_NAMED)

    def test_patch_groups_to_empty(self) -> None:
        response = self.request("poll.update", {"entitled_group_ids": [], "id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("entitled_group_ids") == []

    def test_patch_groups(self) -> None:
        self.create_model("group/2", {"meeting_id": 113, "poll_ids": []})
        response = self.request(
            "poll.update",
            {"entitled_group_ids": [2], "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("entitled_group_ids"), [2])

    def test_patch_title_started(self) -> None:
        self.update_model("poll/1", dict(state=Poll.STATE_STARTED))
        response = self.request(
            "poll.update",
            {"title": "test_title_Oophah8EaLaequu3toh8", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("title"), "test_title_Oophah8EaLaequu3toh8")

    def test_patch_wrong_state(self) -> None:
        self.update_model("poll/1", dict(state=Poll.STATE_STARTED))
        response = self.request(
            "poll.update",
            {"type": Poll.TYPE_NAMED, "id": 1},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("type"), Poll.TYPE_NAMED)

    def test_patch_100_percent_base(self) -> None:
        response = self.request(
            "poll.update",
            {"onehundred_percent_base": "cast", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "cast")

    def test_patch_wrong_100_percent_base(self) -> None:
        response = self.request(
            "poll.update",
            {"onehundred_percent_base": "invalid", "id": 1},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "Y")

    def test_patch_majority_method(self) -> None:
        response = self.request(
            "poll.update",
            {"majority_method": "two_thirds", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("majority_method"), "two_thirds")

    def test_patch_wrong_majority_method(self) -> None:
        response = self.request(
            "poll.update",
            {"majority_method": "invalid majority method", "id": 1},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("majority_method"), "simple")

    def test_patch_multiple_fields(self) -> None:
        response = self.request(
            "poll.update",
            {
                "id": 1,
                "title": "test_title_ees6Tho8ahheen4cieja",
                "pollmethod": "Y",
                "global_yes": True,
                "global_no": True,
                "global_abstain": False,
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("title"), "test_title_ees6Tho8ahheen4cieja")
        self.assertEqual(poll.get("pollmethod"), "Y")
        self.assertTrue(poll.get("global_yes"))
        self.assertTrue(poll.get("global_no"))
        self.assertFalse(poll.get("global_abstain"))
        self.assertEqual(poll.get("amount_global_yes"), "0.000000")
        self.assertEqual(poll.get("amount_global_no"), "0.000000")
        self.assertEqual(poll.get("amount_global_abstain"), None)

    def test_patch_majority_method_state_not_created(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED})
        response = self.request(
            "poll.update",
            {"majority_method": "two_thirds", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("majority_method"), "two_thirds")

    def test_patch_100_percent_base_state_not_created(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED})
        response = self.request(
            "poll.update",
            {"onehundred_percent_base": "cast", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "cast")

    def test_patch_wrong_100_percent_base_state_not_created(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED, "pollmethod": "YN"})
        response = self.request(
            "poll.update",
            {"onehundred_percent_base": "YNA", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "YN")


class VotePollBaseTestClass(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_model(
            "assignment/1",
            dict(
                title="test_assignment_tcLT59bmXrXif424Qw7K",
                open_posts=1,
                candidate_ids=[1],
            ),
        )
        self.create_poll()
        self.create_model("meeting/113", {"name": "my meeting"})
        self.create_model("group/1", {"user_ids": [1]})
        self.create_model("option/1", {"meeting_id": 113, "poll_id": 1})
        self.create_model("option/2", {"meeting_id": 113, "poll_id": 1})
        self.update_model(
            "user/1",
            {
                "is_present_in_meeting_ids": [113],
                "group_$113_ids": [1],
                "group_$_ids": ["113"],
            },
        )

    def create_poll(self) -> None:
        # has to be implemented by subclasses
        raise NotImplementedError()

    def start_poll(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED})

    def add_candidate(self) -> None:
        self.create_model("option/3", {"meeting_id": 113, "poll_id": 1})
        self.update_model("poll/1", {"option_ids": [1, 2, 3]})


class VotePollAnalogYNA(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_04k0y4TwPLpJKaSvIGm1",
                pollmethod="YNA",
                type=Poll.TYPE_ANALOG,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", dict(id=1))
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), None)
        self.assertEqual(poll.get("votesinvalid"), None)
        self.assertEqual(poll.get("votescast"), None)
        self.assert_model_not_exists("vote/1")

    def test_stop_poll(self) -> None:
        self.start_poll()
        response = self.request("poll.stop", dict(id=1))
        self.assert_status_code(response, 400)
        self.assertEqual(self.get_model("poll/1").get("state"), Poll.STATE_STARTED)

    def test_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {
                "value": {
                    "options": {
                        "1": {"Y": "1", "N": "2.35", "A": "-1"},
                        "2": {"Y": "30", "N": "-2", "A": "8.93"},
                    },
                    "votesvalid": "4.64",
                    "votesinvalid": "-2",
                    "votescast": "-2",
                },
                "user_id": 1,
                "id": 1,
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/6")
        self.assert_model_not_exists("vote/7")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "4.64")
        self.assertEqual(poll.get("votesinvalid"), "-2")
        self.assertEqual(poll.get("votescast"), "-2")
        self.assertEqual(poll.get("state"), Poll.STATE_FINISHED)
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "1")
        self.assertEqual(option1.get("no"), "2.35")
        self.assertEqual(option1.get("abstain"), "-1")
        self.assertEqual(option2.get("yes"), "30")
        self.assertEqual(option2.get("no"), "-2")
        self.assertEqual(option2.get("abstain"), "8.93")

    def test_vote_fractional_negative_values(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {
                "value": {
                    "options": {"1": {"Y": "1", "N": "1", "A": "1"}},
                    "votesvalid": "-1.5",
                    "votesinvalid": "-2",
                    "user_id": 1,
                    "id": 1,
                    "votescast": "-2",
                },
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_too_many_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {
                "value": {
                    "options": {
                        "1": {"Y": "1", "N": "2.35", "A": "-1"},
                        "2": {"Y": "1", "N": "2.35", "A": "-1"},
                    }
                },
                "user_id": 1,
                "id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_too_few_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {
                "value": {"options": {"1": {"Y": "1", "N": "2.35", "A": "-1"}}},
                "user_id": 1,
                "id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {
                "value": {
                    "options": {
                        "1": {"Y": "1", "N": "2.35", "A": "-1"},
                        "3": {"Y": "1", "N": "2.35", "A": "-1"},
                    }
                },
                "user_id": 1,
                "id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_value(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_data_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote", {"value": [1, 2, 5], "id": 1, "user_id": 1}
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"options": [1, "string"]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {
                "value": {"options": {"string": "some_other_string"}},
                "id": 1,
                "user_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"options": {"1": [None]}, "id": 1, "user_id": 1}},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_vote_value(self) -> None:
        self.start_poll()
        for value in "YNA":
            data = {
                "options": {"1": {"Y": "1", "N": "3", "A": "-1"}},
            }
            del data["options"]["1"][value]
            response = self.request("poll.vote", {"value": data, "id": 1, "user_id": 1})
            self.assert_status_code(response, 400)
            self.assert_model_not_exists("vote/1")

    def test_vote_state_finished(self) -> None:
        self.start_poll()
        self.request(
            "poll.vote",
            {
                "value": {
                    "options": {"1": {"Y": 5, "N": 0, "A": 1}},
                    "votesvalid": "-2",
                    "votesinvalid": "1",
                    "votescast": "-1",
                },
                "id": 1,
                "user_id": 1,
            },
        )
        self.update_model("poll/1", dict(state="finished"))
        response = self.request(
            "poll.vote",
            {
                "value": {
                    "options": {"1": {"Y": 2, "N": 2, "A": 2}},
                    "votesvalid": "4.64",
                    "votesinvalid": "-2",
                    "votescast": "3",
                },
                "id": 1,
                "user_id": 1,
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "4.64")
        self.assertEqual(poll.get("votesinvalid"), "-2")
        self.assertEqual(poll.get("votescast"), "3")
        self.assert_model_exists("vote/3")
        self.assert_model_not_exists("vote/4")
        option = self.get_model("option/1")
        self.assertEqual(option.get("yes"), "2")
        self.assertEqual(option.get("no"), "2")
        self.assertEqual(option.get("abstain"), "2")


class VotePollNamedYNA(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_OkHAIvOSIcpFnCxbaL6v",
                pollmethod="YNA",
                type=Poll.TYPE_NAMED,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assert_model_not_exists("vote/1")

    def test_vote(self) -> None:
        self.add_candidate()
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "2": "N", "3": "A"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")
        self.assert_model_exists("vote/2")
        self.assert_model_exists("vote/3")
        self.assert_model_not_exists("vote/4")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertIn(1, poll.get("voted_ids", []))
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        option3 = self.get_model("option/3")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "1.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")
        self.assertEqual(option3.get("yes"), "0.000000")
        self.assertEqual(option3.get("no"), "0.000000")
        self.assertEqual(option3.get("abstain"), "1.000000")

    def test_vote_with_voteweight(self) -> None:
        # config["users_activate_vote_weight"] = True
        self.update_model("user/1", dict(vote_weight="4.200000"))
        self.add_candidate()
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "2": "N", "3": "A"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")
        self.assert_model_exists("vote/2")
        self.assert_model_exists("vote/3")
        self.assert_model_not_exists("vote/4")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "4.200000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        option3 = self.get_model("option/3")
        self.assertEqual(option1.get("yes"), "4.200000")
        self.assertEqual(option1.get("no"), "0")
        self.assertEqual(option1.get("abstain"), "0")
        self.assertEqual(option2.get("yes"), "0")
        self.assertEqual(option2.get("no"), "4.200000")
        self.assertEqual(option2.get("abstain"), "0")
        self.assertEqual(option3.get("yes"), "0")
        self.assertEqual(option3.get("no"), "0")
        self.assertEqual(option3.get("abstain"), "4.200000")

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/2")
        vote = self.get_model("vote/1")
        self.assertEqual(vote.get("value"), "Y")

    def test_too_many_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "2": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_no_permissions(self) -> None:
        self.start_poll()
        # self.make_admin_delegate()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 0},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.start_poll()
        self.update_model("user/1", dict(is_present_in_meeting_ids=[]))
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"id": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")


class VotePollNamedY(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_Zrvh146QAdq7t6iSDwZk",
                pollmethod="Y",
                type=Poll.TYPE_NAMED,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assert_model_not_exists("vote/1")

    def test_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")
        self.assert_model_not_exists("vote/2")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertIn(1, poll.get("voted_ids", []))
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), ".0000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_global_yes(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": "Y", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        option = self.get_model("option/1")
        self.assertEqual(option.get("yes"), "1.000000")
        self.assertEqual(option.get("no"), "0.000000")
        self.assertEqual(option.get("abstain"), "0.000000")
        self.assertEqual(poll.get("amount_global_yes"), "1.000000")
        self.assertEqual(poll.get("amount_global_no"), "0.000000")
        self.assertEqual(poll.get("amount_global_abstain"), "0.000000")

    def test_global_yes_forbidden(self) -> None:
        self.update_model("poll/1", dict(global_yes=False))
        self.start_poll()
        response = self.request("poll.vote", {"value": "Y", "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        self.assertEqual(self.get_model("poll/1").get("amount_global_yes"), None)

    def test_global_no(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": "N", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        option = self.get_model("option/1")
        self.assertEqual(option.get("yes"), "0.000000")
        self.assertEqual(option.get("no"), "1.000000")
        self.assertEqual(option.get("abstain"), "0.000000")
        self.assertEqual(poll.get("amount_global_yes"), "0.000000")
        self.assertEqual(poll.get("amount_global_no"), "1.000000")
        self.assertEqual(poll.get("amount_global_abstain"), "0.000000")

    def test_global_no_forbidden(self) -> None:
        self.update_model("poll/1", dict(global_no=False))
        self.start_poll()
        response = self.request("poll.vote", {"value": "N", "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        self.assertEqual(self.get_model("poll/1").get("amount_global_no"), None)

    def test_global_abstain(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": "A", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        option = self.get_model("option/1")
        self.assertEqual(option.get("yes"), "0.000000")
        self.assertEqual(option.get("no"), "0.000000")
        self.assertEqual(option.get("abstain"), "1.000000")
        self.assertEqual(poll.get("amount_global_yes"), "0.000000")
        self.assertEqual(poll.get("amount_global_no"), "0.000000")
        self.assertEqual(poll.get("amount_global_abstain"), "1.000000")

    def test_global_abstain_forbidden(self) -> None:
        self.update_model("poll/1", dict(global_abstain=False))
        self.start_poll()
        response = self.request("poll.vote", {"value": "A", "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        self.assertEqual(self.get_model("poll/1").get("amount_global_abstain"), None)

    def test_negative_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_too_many_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 1, "3": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"3": 1}},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_no_permissions(self) -> None:
        self.start_poll()
        # self.make_admin_delegate()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 0},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.start_poll()
        self.update_model("user/1", dict(is_present_in_meeting_ids=[]))
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"id": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")


class VotePollNamedN(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_4oi49ckKFk39SDIfj30s",
                pollmethod="N",
                type=Poll.TYPE_NAMED,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assert_model_not_exists("vote/1")

    def test_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")
        self.assert_model_not_exists("vote/2")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertTrue(1 in poll.get("voted_ids", []))
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "0.000000")
        self.assertEqual(option1.get("no"), "1.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_change_vote(self) -> None:
        self.add_candidate()
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "0.000000")
        self.assertEqual(option1.get("no"), "1.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_global_yes(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": "Y", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        option = self.get_model("option/1")
        self.assertEqual(option.get("yes"), "1")
        self.assertEqual(option.get("no"), "0")
        self.assertEqual(option.get("abstain"), "0")
        self.assertEqual(poll.get("amount_global_yes"), "1")
        self.assertEqual(poll.get("amount_global_no"), "0")
        self.assertEqual(poll.get("amount_global_abstain"), "0")

    def test_global_yes_forbidden(self) -> None:
        self.update_model("poll/1", dict(global_yes=False))
        self.start_poll()
        response = self.request("poll.vote", {"value": "Y", "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("amount_global_yes"), None)

    def test_global_no(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": "N", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        option = self.get_model("option/1")
        self.assertEqual(option.get("yes"), "0.000000")
        self.assertEqual(option.get("no"), "1.000000")
        self.assertEqual(option.get("abstain"), "0.000000")
        self.assertEqual(poll.get("amount_global_yes"), "0.000000")
        self.assertEqual(poll.get("amount_global_no"), "1.000000")
        self.assertEqual(poll.get("amount_global_abstain"), "0.000000")

    def test_global_no_forbidden(self) -> None:
        self.update_model("poll/1", dict(global_no=False))
        self.start_poll()
        response = self.request("poll.vote", {"value": "N", "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        self.assertEqual(self.get_model("poll/1").get("amount_global_no"), None)

    def test_global_abstain(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": "A", "id": 1, "user_id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        option = self.get_model("option/1")
        self.assertEqual(option.get("yes"), "0.000000")
        self.assertEqual(option.get("no"), "0.000000")
        self.assertEqual(option.get("abstain"), "1.000000")
        self.assertEqual(poll.get("amount_global_yes"), "0.000000")
        self.assertEqual(poll.get("amount_global_no"), "0.000000")
        self.assertEqual(poll.get("amount_global_abstain"), "1.000000")

    def test_global_abstain_forbidden(self) -> None:
        self.update_model("poll/1", dict(global_abstain=False))
        self.start_poll()
        response = self.request("poll.vote", {"value": "A", "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        self.assertEqual(self.get_model("poll/1").get("amount_global_abstain"), None)

    def test_negative_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"3": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_no_permissions(self) -> None:
        self.start_poll()
        # self.make_admin_delegate()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 2},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.start_poll()
        self.update_model("user/1", dict(is_present_in_meeting_ids=[]))
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"id": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")


class VotePollPseudoanonymousYNA(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_OkHAIvOSIcpFnCxbaL6v",
                pollmethod="YNA",
                type=Poll.TYPE_PSEUDOANONYMOUS,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assert_model_not_exists("vote/1")

    def test_vote(self) -> None:
        self.add_candidate()
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "2": "N", "3": "A"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.get_model("vote/1")
        self.get_model("vote/2")
        self.get_model("vote/3")
        self.assert_model_not_exists("vote/4")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        option3 = self.get_model("option/3")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "1.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")
        self.assertEqual(option3.get("yes"), "0.000000")
        self.assertEqual(option3.get("no"), "0.000000")
        self.assertEqual(option3.get("abstain"), "1.000000")

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        option1 = self.get_model("option/1")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")

    def test_too_many_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_partial_vote(self) -> None:
        self.add_candidate()
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")

    def test_wrong_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y", "3": "N"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_no_permissions(self) -> None:
        self.start_poll()
        # self.make_admin_delegate()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_anonymous(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 2},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.start_poll()
        self.update_model("user/1", dict(is_present_in_meeting_ids=[]))
        response = self.request(
            "poll.vote",
            {"value": {"1": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_value(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_value_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"id": "Y"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_value(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")


class VotePollPseudoanonymousY(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_Zrvh146QAdq7t6iSDwZk",
                pollmethod="Y",
                type=Poll.TYPE_PSEUDOANONYMOUS,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")
        self.assert_model_not_exists("vote/1")

    def test_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")
        self.assert_model_not_exists("vote/2")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertTrue(1 in poll.get("voted_ids", []))
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")
        vote = self.get_model("vote/1")
        self.assertIsNone(vote.get("user_id"))

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.get_model("poll/1")
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "1.000000")
        self.assertEqual(option1.get("no"), "0.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_negative_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_options(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"3": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.start_poll()
        self.update_model("user/1", dict(is_present_in_meeting_ids=[]))
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {"value": {}, "id": 1, "user_id": 1})
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"value": [1, 2, 5]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"id": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": [None]}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")


class VotePollPseudoAnonymousN(VotePollBaseTestClass):
    def create_poll(self) -> None:
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_wWPOVJgL9afm83eamf3e",
                pollmethod="N",
                type=Poll.TYPE_PSEUDOANONYMOUS,
                state=Poll.STATE_CREATED,
                meeting_id=113,
                option_ids=[1, 2],
                entitled_group_ids=[1],
            ),
        )

    def test_start_poll(self) -> None:
        response = self.request("poll.start", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertEqual(poll.get("votesvalid"), "0.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "0.000000")

    def test_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"id": 1, "value": {"1": 1, "2": 0}, "user_id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("vote/1")
        self.assert_model_not_exists("vote/2")
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "1.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "1.000000")
        self.assertEqual(poll.get("state"), Poll.STATE_STARTED)
        self.assertTrue(1 in poll.get("voted_ids", []))
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "0")
        self.assertEqual(option1.get("no"), "1")
        self.assertEqual(option1.get("abstain"), "0")
        self.assertEqual(option2.get("yes"), "0")
        self.assertEqual(option2.get("no"), "0")
        self.assertEqual(option2.get("abstain"), "0")
        vote = self.get_model("vote/1")
        self.assertIsNone(vote.get("user_id"))

    def test_change_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": 1, "2": 0}, "id": 1, "user_id": 1},
        )
        response = self.request(
            "poll.vote",
            {"value": {"1": 0, "2": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.get_model("poll/1")
        option1 = self.get_model("option/1")
        option2 = self.get_model("option/2")
        self.assertEqual(option1.get("yes"), "0.000000")
        self.assertEqual(option1.get("no"), "1.000000")
        self.assertEqual(option1.get("abstain"), "0.000000")
        self.assertEqual(option2.get("yes"), "0.000000")
        self.assertEqual(option2.get("no"), "0.000000")
        self.assertEqual(option2.get("abstain"), "0.000000")

    def test_negative_vote(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": -1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_vote_not_present(self) -> None:
        self.start_poll()
        self.update_model("user/1", dict(is_present_in_meeting_ids=[]))

        response = self.request(
            "poll.vote",
            {"id": 1, "user_id": 1, "value": {"1": 1}},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_state(self) -> None:
        response = self.request(
            "poll.vote",
            {"value": {"1": 1}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_missing_data(self) -> None:
        self.start_poll()
        response = self.request("poll.vote", {})
        self.assert_status_code(response, 400)
        assert (
            "data must contain ['id', 'user_id', 'value'] properties"
            in response.data.decode()
        )
        self.assert_model_not_exists("vote/1")
        poll = self.get_model("poll/1")
        self.assertNotIn(1, poll.get("voted_ids", []))

    def test_wrong_data_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": [1, 2, 5], "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        assert "data.value must be object or string" in response.data.decode()
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_format(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"value": {"1": "string"}, "id": 1, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        assert "Option 1 has not a right value. (int, str)." in response.data.decode()
        self.assert_model_not_exists("vote/1")

    def test_wrong_option_id_type(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"id": 1},
        )
        self.assert_status_code(response, 400)
        self.assert_model_not_exists("vote/1")

    def test_wrong_vote_data(self) -> None:
        self.start_poll()
        response = self.request(
            "poll.vote",
            {"id": 1, "value": {"1": [None]}, "user_id": 1},
        )
        self.assert_status_code(response, 400)
        assert "Option 1 has not a right value. (int, str)." in response.data.decode()
        self.assert_model_not_exists("vote/1")


class AnonymizePoll(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_model(
            "assignment/1",
            {
                "title": "test_assignment_QLydMOqkyOHG68yZFJxl",
                "open_posts": 1,
                "candidate_ids": [1],
            },
        )
        self.create_model(
            "poll/1",
            dict(
                content_object_id="assignment/1",
                title="test_title_3LbUCNirKirpJhRHRxzW",
                pollmethod="YNA",
                type=Poll.TYPE_NAMED,
                state=Poll.STATE_FINISHED,
                option_ids=[11],
                meeting_id=113,
                voted_ids=[1, 2],
            ),
        )
        self.create_model("option/11", {"meeting_id": 113, "poll_id": 1})
        self.create_model("meeting/113", {"name": "my meeting"})

        self.create_model(
            "vote/1", dict(user_id=1, option_id=11, value="Y", weight="1.000000")
        )
        self.create_model("user/2", dict(username="test_user_2"))
        self.create_model(
            "vote/2", dict(user_id=2, option_id=11, value="N", weight="1.000000")
        )

    def test_anonymize_poll(self) -> None:
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("votesvalid"), "2.000000")
        self.assertEqual(poll.get("votesinvalid"), "0.000000")
        self.assertEqual(poll.get("votescast"), "2.000000")
        option = self.get_model("option/11")
        self.assertEqual(option.get("yes"), "1.000000")
        self.assertEqual(option.get("no"), "1.000000")
        self.assertEqual(option.get("abstain"), "0.000000")
        self.assertTrue(1 in poll.get("voted_ids", []))
        self.assertTrue(2 in poll.get("voted_ids", []))
        for vote_fqid in ("vote/1", "vote/2"):
            vote = self.get_model(vote_fqid)
            assert vote.get("user_id") is None

    def test_anonymize_wrong_state(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_CREATED})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 400)
        for vote_fqid in ("vote/1", "vote/2"):
            vote = self.get_model(vote_fqid)
            assert vote.get("user_id")

    def test_anonymize_wrong_type(self) -> None:
        self.update_model("poll/1", {"type": Poll.TYPE_ANALOG})
        response = self.request("poll.anonymize", {"id": 1})
        self.assert_status_code(response, 400)
        for vote_fqid in ("vote/1", "vote/2"):
            vote = self.get_model(vote_fqid)
            assert vote.get("user_id")
