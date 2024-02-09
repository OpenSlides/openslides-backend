from openslides_backend.models.models import Poll
from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID

from .base_poll_test import BasePollTestCase


class UpdatePollTestCase(BasePollTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.set_models(
            {
                "assignment/1": {
                    "title": "test_assignment_ohneivoh9caiB8Yiungo",
                    "open_posts": 1,
                },
                "meeting/1": {
                    "name": "my meeting",
                    "is_active_in_organization_id": 1,
                    "meeting_user_ids": [11],
                },
                ONE_ORGANIZATION_FQID: {"enable_electronic_voting": True},
                "group/1": {"meeting_user_ids": [11], "poll_ids": [1]},
                "poll/1": {
                    "content_object_id": "assignment/1",
                    "title": "test_title_beeFaihuNae1vej2ai8m",
                    "pollmethod": "Y",
                    "type": Poll.TYPE_NAMED,
                    "onehundred_percent_base": "Y",
                    "state": Poll.STATE_CREATED,
                    "meeting_id": 1,
                    "option_ids": [1, 2],
                    "entitled_group_ids": [1],
                    "min_votes_amount": 1,
                    "max_votes_amount": 1,
                    "max_votes_per_option": 1,
                },
                "option/1": {"meeting_id": 1, "poll_id": 1},
                "option/2": {"meeting_id": 1, "poll_id": 1},
                "user/1": {
                    "is_present_in_meeting_ids": [1],
                    "meeting_user_ids": [11],
                },
                "meeting_user/11": {
                    "user_id": 1,
                    "meeting_id": 1,
                    "group_ids": [1],
                },
            }
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
                "max_votes_per_option": 1,
                "global_yes": False,
                "global_no": True,
                "global_abstain": True,
            },
        )
        self.assert_status_code(response, 400)
        assert ("data must not contain {'type'} properties") in response.json["message"]

    def test_optional_state_created(self) -> None:
        response = self.request(
            "poll.update",
            {
                "id": 1,
                "pollmethod": "Y",
                "min_votes_amount": 1,
                "max_votes_amount": 1,
                "max_votes_per_option": 1,
                "global_yes": False,
                "global_no": True,
                "global_abstain": True,
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("pollmethod") == "Y"
        assert poll.get("min_votes_amount") == 1
        assert poll.get("max_votes_amount") == 1
        assert poll.get("max_votes_per_option") == 1
        assert poll.get("global_yes") is False
        assert poll.get("global_no") is True
        assert poll.get("global_abstain") is True
        self.assert_history_information("assignment/1", ["Ballot updated"])

    def test_not_allowed_for_analog(self) -> None:
        self.update_model("poll/1", {"type": "analog"})
        response = self.request("poll.update", {"id": 1, "entitled_group_ids": []})
        self.assert_status_code(response, 400)
        assert (
            "Following options are not allowed in this state and type: "
            "entitled_group_ids"
        ) in response.json["message"]

    def test_not_allowed_for_non_analog(self) -> None:
        response = self.request(
            "poll.update",
            {
                "id": 1,
                "votesvalid": "10.000000",
                "votesinvalid": "11.000000",
                "votescast": "3.000000",
                "publish_immediately": True,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "Following options are not allowed in this state and type: "
            "votesvalid, votesinvalid, votescast, publish_immediately"
        ) in response.json["message"]

    def test_update_title(self) -> None:
        response = self.request(
            "poll.update",
            {"title": "test_title_Aishohh1ohd0aiSut7gi", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("title"), "test_title_Aishohh1ohd0aiSut7gi")

    def test_prevent_updating_content_object(self) -> None:
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

    def test_update_pollmethod(self) -> None:
        response = self.request(
            "poll.update",
            {"pollmethod": "YNA", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("pollmethod"), "YNA")
        self.assertEqual(poll.get("onehundred_percent_base"), "Y")

    def test_update_backend(self) -> None:
        response = self.request(
            "poll.update",
            {"backend": "long", "id": 1},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("poll/1", {"backend": "long"})

    def test_update_backend_not_allowed(self) -> None:
        self.set_models({"poll/1": {"state": Poll.STATE_FINISHED}})
        response = self.request(
            "poll.update",
            {"backend": "long", "id": 1},
        )
        self.assert_status_code(response, 400)
        assert (
            "Following options are not allowed in this state and type: backend"
            in response.json["message"]
        )

    def test_update_invalid_pollmethod(self) -> None:
        response = self.request(
            "poll.update",
            {"pollmethod": "invalid"},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("pollmethod"), "Y")

    def test_update_groups_to_empty(self) -> None:
        response = self.request("poll.update", {"entitled_group_ids": [], "id": 1})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("entitled_group_ids") == []

    def test_update_groups(self) -> None:
        self.create_model("group/2", {"meeting_id": 1, "poll_ids": []})
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

    def test_update_max_votes_per_option(self) -> None:
        response = self.request(
            "poll.update",
            {"max_votes_per_option": 5, "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("max_votes_per_option"), 5)

    def test_update_negative_fields(self) -> None:
        for field in ("max_votes_per_option", "max_votes_amount", "min_votes_amount"):
            response = self.request(
                "poll.update",
                {field: -3, "id": 1},
            )
            self.assert_status_code(response, 400)
            poll = self.get_model("poll/1")
            self.assertEqual(poll.get(field), 1)

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
                "max_votes_per_option": 2,
            },
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("title"), "test_title_ees6Tho8ahheen4cieja")
        self.assertEqual(poll.get("pollmethod"), "Y")
        self.assertTrue(poll.get("global_yes"))
        self.assertTrue(poll.get("global_no"))
        self.assertFalse(poll.get("global_abstain"))
        self.assertEqual(poll.get("max_votes_per_option"), 2)

    def test_update_max_votes_per_option_state_not_created(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED})
        response = self.request(
            "poll.update",
            {"max_votes_per_option": 3, "id": 1},
        )
        self.assert_status_code(response, 400)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("max_votes_per_option"), 1)

    def test_update_100_percent_base_state_not_created(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED})
        response = self.request(
            "poll.update",
            {"onehundred_percent_base": "cast", "id": 1},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "cast")

    def test_update_wrong_100_percent_base_state_not_created(self) -> None:
        self.update_model("poll/1", {"state": Poll.STATE_STARTED, "pollmethod": "YN"})
        response = self.request(
            "poll.update",
            {"onehundred_percent_base": "YNA", "id": 1},
        )
        self.assert_status_code(response, 400)
        assert (
            "This onehundred_percent_base not allowed in this pollmethod"
            in response.json["message"]
        )
        poll = self.get_model("poll/1")
        self.assertEqual(poll.get("onehundred_percent_base"), "Y")

    def test_update_wrong_100_percent_base_entitled_and_analog(self) -> None:
        self.update_model(
            "poll/1",
            {"state": Poll.STATE_STARTED, "pollmethod": "YN", "type": Poll.TYPE_ANALOG},
        )
        response = self.request(
            "poll.update",
            {"onehundred_percent_base": "entitled", "id": 1},
        )
        self.assert_status_code(response, 400)
        assert (
            "onehundred_percent_base: value entitled is not allowed for analog."
            in response.json["message"]
        )

    def test_state_change(self) -> None:
        self.update_model("poll/1", {"type": Poll.TYPE_ANALOG})
        response = self.request("poll.update", {"id": 1, "votescast": "1.000000"})
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("state") == Poll.STATE_FINISHED

    def test_state_change_2_published(self) -> None:
        self.update_model("poll/1", {"type": Poll.TYPE_ANALOG})
        response = self.request(
            "poll.update",
            {"id": 1, "votescast": "1.000000", "publish_immediately": True},
        )
        self.assert_status_code(response, 200)
        poll = self.get_model("poll/1")
        assert poll.get("state") == Poll.STATE_PUBLISHED
        assert "publish_immediately" not in poll

    def test_default_vote_values(self) -> None:
        self.update_model("poll/1", {"type": Poll.TYPE_ANALOG})
        response = self.request(
            "poll.update",
            {"id": 1, "votescast": "1.000000"},
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "poll/1",
            {
                "votescast": "1.000000",
                "votesvalid": "-2.000000",
                "votesinvalid": "-2.000000",
            },
        )

    def test_motion_history_information(self) -> None:
        self.set_models(
            {
                "poll/1": {"content_object_id": "motion/1"},
                "motion/1": {"meeting_id": 1, "poll_ids": [1]},
            }
        )
        response = self.request(
            "poll.update",
            {"id": 1, "title": "test"},
        )
        self.assert_status_code(response, 200)
        self.assert_history_information("motion/1", ["Voting updated"])

    def test_update_no_permissions(self) -> None:
        self.base_permission_test(
            {},
            "poll.update",
            {"title": "test_title_Aishohh1ohd0aiSut7gi", "id": 1},
        )

    def test_update_permissions(self) -> None:
        self.base_permission_test(
            {},
            "poll.update",
            {"title": "test_title_Aishohh1ohd0aiSut7gi", "id": 1},
            Permissions.Assignment.CAN_MANAGE,
        )
