import pytest

import openslides_backend.action.actions  # noqa
from openslides_backend.models.models import Poll
from tests.system.action.base import BaseActionTestCase


class UpdatePollTestCase(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.create_model(
            "assignment/1",
            {
                "title": "test_assignment_ohneivoh9caiB8Yiungo",
                "open_posts": 1,
            },
        )
        self.create_model("meeting/113", {"name": "my meeting"})
        self.create_model("organisation/1", {"enable_electronic_voting": True})
        self.create_model("group/1", {"user_ids": [1], "poll_ids": [1]})
        self.create_model(
            "poll/1",
            {
                "content_object_id": "assignment/1",
                "title": "test_title_beeFaihuNae1vej2ai8m",
                "pollmethod": "Y",
                "type": Poll.TYPE_NAMED,
                "onehundred_percent_base": "Y",
                "majority_method": "simple",
                "state": Poll.STATE_CREATED,
                "meeting_id": 113,
                "option_ids": [1, 2],
                "entitled_group_ids": [1],
            },
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

    def test_catch_not_allowed(self) -> None:
        self.update_model("poll/1", {"state": "started"})
        response = self.request(
            "poll.update",
            {
                "id": 1,
                "pollmethod": "Y",
                "type": "analog",
                "min_votes_amount": 1,
                "max_votes_amount": 1,
                "global_yes": False,
                "global_no": True,
                "global_abstain": True,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Following options are not allowed in this state and type: "
            "pollmethod, type, min_votes_amount, max_votes_amount, global_yes,"
            " global_no, global_abstain"
        ) in response.data.decode()

    def test_optional_state_created(self) -> None:
        response = self.request(
            "poll.update",
            {
                "id": 1,
                "pollmethod": "Y",
                "type": "analog",
                "min_votes_amount": 1,
                "max_votes_amount": 1,
                "global_yes": False,
                "global_no": True,
                "global_abstain": True,
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("pollmethod") == "Y"
        assert poll.get("type") == "analog"
        assert poll.get("min_votes_amount") == 1
        assert poll.get("max_votes_amount") == 1
        assert poll.get("global_yes") is False
        assert poll.get("global_no") is True
        assert poll.get("global_abstain") is True

    def test_not_allowed_for_analog(self) -> None:
        self.update_model("poll/1", {"type": "analog"})
        response = self.request("poll.update", {"id": 1, "entitled_group_ids": []})
        self.assert_status_code(response, 400)
        assert (
            "Following options are not allowed in this state and type: "
            "entitled_group_ids"
        ) in response.data.decode()

    def test_not_allowed_for_non_analog(self) -> None:
        response = self.request(
            "poll.update",
            {
                "id": 1,
                "votesvalid": "10.000000",
                "votesinvalid": "11.000000",
                "votescast": "3.000000",
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Following options are not allowed in this state and type: "
            "votesvalid, votesinvalid, votescast"
        ) in response.data.decode()

    def test_update_title(self) -> None:
        response = self.request(
            "poll.update",
            {"title": "test_title_Aishohh1ohd0aiSut7gi", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("title"), "test_title_Aishohh1ohd0aiSut7gi")

    def test_prevent_updateing_content_object(self) -> None:
        self.create_model(
            "assignment/2",
            {"title": "test_title_phohdah8quukooHeetuz", "open_posts": 1},
        )
        response = self.request(
            "poll.update",
            {"content_object_id": "assignment/2", "id": 1},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("content_object_id"), "assignment/1")  # unchanged

    @pytest.mark.skip()
    def test_update_pollmethod(self) -> None:
        response = self.request(
            "poll.update",
            {"pollmethod": "YNA", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("pollmethod"), "YNA")
        self.assertEqual(poll.get("onehundred_percent_base"), "YNA")

    def test_update_invalid_pollmethod(self) -> None:
        response = self.request(
            "poll.update",
            {"pollmethod": "invalid"},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("pollmethod"), "Y")

    def test_update_type(self) -> None:
        response = self.request("poll.update", {"type": "analog", "id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("type"), "analog")

    def test_update_invalid_type(self) -> None:
        response = self.request("poll.update", {"type": "invalid", "id": 1})
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("type"), "named")

    def test_update_not_allowed_type(self) -> None:
        self.update_model("organisation/1", {"enable_electronic_voting": False})
        response = self.request(
            "poll.update",
            {"type": Poll.TYPE_NAMED, "id": 1},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("type"), Poll.TYPE_NAMED)

    def test_update_groups_to_empty(self) -> None:
        response = self.request("poll.update", {"entitled_group_ids": [], "id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("entitled_group_ids") == []

    def test_update_groups(self) -> None:
        self.create_model("group/2", {"meeting_id": 113, "poll_ids": []})
        response = self.request(
            "poll.update",
            {"entitled_group_ids": [2], "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("entitled_group_ids"), [2])

    def test_update_title_started(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED})
        response = self.request(
            "poll.update",
            {"title": "test_title_Oophah8EaLaequu3toh8", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("title"), "test_title_Oophah8EaLaequu3toh8")

    def test_update_wrong_state(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED})
        response = self.request(
            "poll.update",
            {"type": Poll.TYPE_NAMED, "id": 1},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("type"), Poll.TYPE_NAMED)

    def test_update_100_percent_base(self) -> None:
        response = self.request(
            "poll.update",
            {"onehundred_percent_base": "cast", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "cast")

    def test_update_wrong_100_percent_base(self) -> None:
        response = self.request(
            "poll.update",
            {"onehundred_percent_base": "invalid", "id": 1},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "Y")

    def test_update_majority_method(self) -> None:
        response = self.request(
            "poll.update",
            {"majority_method": "two_thirds", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("majority_method"), "two_thirds")

    def test_update_wrong_majority_method(self) -> None:
        response = self.request(
            "poll.update",
            {"majority_method": "invalid majority method", "id": 1},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("majority_method"), "simple")

    def test_update_multiple_fields(self) -> None:
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

    def test_update_majority_method_state_not_created(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED})
        response = self.request(
            "poll.update",
            {"majority_method": "two_thirds", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("majority_method"), "two_thirds")

    def test_update_100_percent_base_state_not_created(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED})
        response = self.request(
            "poll.update",
            {"onehundred_percent_base": "cast", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "cast")

    @pytest.mark.skip()
    def test_update_wrong_100_percent_base_state_not_created(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED, "pollmethod": "YN"})
        response = self.request(
            "poll.update",
            {"onehundred_percent_base": "YNA", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "YN")
