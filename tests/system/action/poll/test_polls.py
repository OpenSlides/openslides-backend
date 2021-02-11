from openslides_backend.models.models import Poll
from tests.system.action.base import BaseActionTestCase

GROUP_ADMIN_PK = 1
GROUP_DELEGATE_PK = 1


# def test_assignment_poll_db_queries():
#     """
#     Tests that only the following db queries are done:
#     * 1 request to get the polls,
#     * 1 request to get all options for all polls,
#     * 1 request to get all users for all options (candidates),
#     * 1 request to get all votes for all options,
#     * 1 request to get all users for all votes,
#     * 1 request to get all poll groups,
#     = 6 queries
#     """
#     create_assignment_polls()
#
#
# # assert count_queries(Poll.get_elements)() == 6
#
#
# def test_assignment_vote_db_queries():
#     """
#     Tests that only 1 query is done when fetching Votes
#     """
#     create_assignment_polls()
#     # assert count_queries(Vote.get_elements)() == 1
#
#
# def test_assignment_option_db_queries():
#     """
#     Tests that only the following db queries are done:
#     * 1 request to get the options,
#     * 1 request to get all votes for all options,
#     = 2 queries
#     """
#     create_assignment_polls()
#     # assert count_queries(Option.get_elements)() == 2
#
#
# def create_assignment_polls():
#     """
#     Creates 1 assignment with 3 candidates which has 5 polls in which each candidate got a random amount of votes between 0 and 10 from 3 users
#     """
#
#
# #    assignment = Assignment(title="test_assignment_ohneivoh9caiB8Yiungo", open_posts=1)
# #    assignment.save(skip_autoupdate=True)
# #
# #    group1 = self.get_model("group/1")
# #    group2 = self.get_model("group/2")
# #    for i in range(3):
# #        user = get_user_model().objects.create_user(
# #            username=f"test_username_{i}", password="test_password_UOrnlCZMD0lmxFGwEj54"
# #        )
# #        assignment.add_candidate(user)
# #
# #    for i in range(5):
# #        poll = Poll(
# #            assignment=assignment,
# #            title="test_title_UnMiGzEHmwqplmVBPNEZ",
# #            pollmethod=Poll.POLLMETHOD_YN,
# #            type=Poll.TYPE_NAMED,
# #        )
# #        poll.save(skip_autoupdate=True)
# #        poll.create_options(skip_autoupdate=True)
# #        poll.groups.add(group1)
# #        poll.groups.add(group2)
# #
# #        for j in range(3):
# #            user = get_user_model().objects.create_user(
# #                username=f"test_username_{i}{j}",
# #                password="test_password_kbzj5L8ZtVxBllZzoW6D",
# #            )
# #            poll.voted.add(user)
# #            for option in poll.options.all():
# #                weight = random.randint(0, 10)
# #                if weight > 0:
# #                    Vote.objects.create(
# #                        user=user, option=option, value="Y", weight=Decimal(weight)
# #                    )
#
#
# class CreatePoll(BaseActionTestCase):
#     def advancedSetUp(self) -> None:
#         self.assignment = Assignment.objects.create(
#             title="test_assignment_ohneivoh9caiB8Yiungo", open_posts=1
#         )
#         self.assignment.add_candidate(self.admin)
#
#     def test_simple(self) -> None:
#         with self.assertNumQueries(40):
#             response = self.client.post(
#                 "assignmentpoll-list",
#                 {
#                     "title": "test_title_ailai4toogh3eefaa2Vo",
#                     "pollmethod": Poll.POLLMETHOD_YNA,
#                     "type": "named",
#                     "assignment_id": self.assignment.id,
#                     "onehundred_percent_base": Poll.PERCENT_BASE_YN,
#                     "majority_method": Poll.MAJORITY_SIMPLE,
#                 },
#             )
#         self.assert_status_code(response, 200)
#         self.assertTrue(Poll.objects.exists())
#         poll = Poll.objects.get()
#         self.assertEqual(poll.title, "test_title_ailai4toogh3eefaa2Vo")
#         self.assertEqual(poll.pollmethod, Poll.POLLMETHOD_YNA)
#         self.assertEqual(poll.type, "named")
#         # Check defaults
#         self.assertTrue(poll.global_yes)
#         self.assertTrue(poll.global_no)
#         self.assertTrue(poll.global_abstain)
#         self.assertEqual(poll.amount_global_yes, None)
#         self.assertEqual(poll.amount_global_no, None)
#         self.assertEqual(poll.amount_global_abstain, None)
#         self.assertFalse(poll.allow_multiple_votes_per_candidate)
#         self.assertEqual(poll.votes_amount, 1)
#         self.assertEqual(poll.assignment.id, self.assignment.id)
#         self.assertEqual(poll.description, "")
#         self.assertTrue(poll.options.exists())
#         option = Option.objects.get()
#         self.assertTrue(option.user.id, self.admin.id)
#
#     def test_all_fields(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_ahThai4pae1pi4xoogoo",
#                 "pollmethod": Poll.POLLMETHOD_YN,
#                 "type": "pseudoanonymous",
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YNA,
#                 "majority_method": Poll.MAJORITY_THREE_QUARTERS,
#                 "global_yes": False,
#                 "global_no": False,
#                 "global_abstain": False,
#                 "allow_multiple_votes_per_candidate": True,
#                 "votes_amount": 5,
#                 "description": "test_description_ieM8ThuasoSh8aecai8p",
#             },
#         )
#         self.assert_status_code(response, 200)
#         self.assertTrue(Poll.objects.exists())
#         poll = Poll.objects.get()
#         self.assertEqual(poll.title, "test_title_ahThai4pae1pi4xoogoo")
#         self.assertEqual(poll.pollmethod, Poll.POLLMETHOD_YN)
#         self.assertEqual(poll.type, "pseudoanonymous")
#         self.assertFalse(poll.global_yes)
#         self.assertFalse(poll.global_no)
#         self.assertFalse(poll.global_abstain)
#         self.assertTrue(poll.allow_multiple_votes_per_candidate)
#         self.assertEqual(poll.votes_amount, 5)
#         self.assertEqual(poll.description, "test_description_ieM8ThuasoSh8aecai8p")
#
#     def test_no_candidates(self) -> None:
#         self.assignment.remove_candidate(self.admin)
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_eing5eipue5cha2Iefai",
#                 "pollmethod": Poll.POLLMETHOD_YNA,
#                 "type": "named",
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YN,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#             },
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.exists())
#
#     def test_missing_keys(self) -> None:
#         complete_request_data = {
#             "title": "test_title_keugh8Iu9ciyooGaevoh",
#             "pollmethod": Poll.POLLMETHOD_YNA,
#             "type": "named",
#             "assignment_id": self.assignment.id,
#             "onehundred_percent_base": Poll.PERCENT_BASE_YN,
#             "majority_method": Poll.MAJORITY_SIMPLE,
#         }
#         for key in complete_request_data.keys():
#             request_data = {
#                 _key: value
#                 for _key, value in complete_request_data.items()
#                 if _key != key
#             }
#             response = self.client.post("assignmentpoll-list"), request_data
#             self.assert_status_code(response, 400)
#             self.assertFalse(Poll.objects.exists())
#
#     def test_with_groups(self) -> None:
#         group1 = self.get_model("group/1")
#         group2 = self.get_model("group/2")
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_Thoo2eiphohhi1eeXoow",
#                 "pollmethod": Poll.POLLMETHOD_YNA,
#                 "type": "named",
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YN,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#                 "groups_id": [1, 2],
#             },
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertTrue(group1 in poll.groups.all())
#         self.assertTrue(group2 in poll.groups.all())
#
#     def test_with_empty_groups(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_Thoo2eiphohhi1eeXoow",
#                 "pollmethod": Poll.POLLMETHOD_YNA,
#                 "type": "named",
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YN,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#                 "groups_id": [],
#             },
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertFalse(poll.groups.exists())
#
#     def test_not_supported_type(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_yaiyeighoh0Iraet3Ahc",
#                 "pollmethod": Poll.POLLMETHOD_YNA,
#                 "type": "not_existing",
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YN,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#             },
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.exists())
#
#     def test_not_allowed_type(self) -> None:
#         # setattr(settings, "ENABLE_ELECTRONIC_VOTING", False)
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_yaiyeighoh0Iraet3Ahc",
#                 "pollmethod": Poll.POLLMETHOD_YNA,
#                 "type": Poll.TYPE_NAMED,
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YN,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#             },
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.exists())
#         # setattr(settings, "ENABLE_ELECTRONIC_VOTING", True)
#
#     def test_not_supported_pollmethod(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_SeVaiteYeiNgie5Xoov8",
#                 "pollmethod": "not_existing",
#                 "type": "named",
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YN,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#             },
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.exists())
#
#     def test_not_supported_onehundred_percent_base(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_Thoo2eiphohhi1eeXoow",
#                 "pollmethod": Poll.POLLMETHOD_YNA,
#                 "type": "named",
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": "invalid base",
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#             },
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.exists())
#
#     def test_not_supported_majority_method(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_Thoo2eiphohhi1eeXoow",
#                 "pollmethod": Poll.POLLMETHOD_YNA,
#                 "type": "named",
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YN,
#                 "majority_method": "invalid majority method",
#             },
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.exists())
#
#     def test_wrong_pollmethod_onehundred_percent_base_combination_1(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_Thoo2eiphohhi1eeXoow",
#                 "pollmethod": Poll.POLLMETHOD_YNA,
#                 "type": "named",
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_Y,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#             },
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.onehundred_percent_base, Poll.PERCENT_BASE_YNA)
#
#     def test_wrong_pollmethod_onehundred_percent_base_combination_2(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_Thoo2eiphohhi1eeXoow",
#                 "pollmethod": Poll.POLLMETHOD_YN,
#                 "type": "named",
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_Y,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#             },
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.onehundred_percent_base, Poll.PERCENT_BASE_YN)
#
#     def test_wrong_pollmethod_onehundred_percent_base_combination_3(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_Thoo2eiphohhi1eeXoow",
#                 "pollmethod": Poll.POLLMETHOD_Y,
#                 "type": "named",
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YNA,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#             },
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.onehundred_percent_base, Poll.PERCENT_BASE_Y)
#
#     def test_create_with_votes(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_dKbv5tV47IzY1oGHXdSz",
#                 "pollmethod": Poll.POLLMETHOD_Y,
#                 "type": Poll.TYPE_ANALOG,
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YNA,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#                 "votes": {
#                     "options": {"1": {"Y": 1}},
#                     "votesvalid": "-2",
#                     "votesinvalid": "-2",
#                     "votescast": "-2",
#                 },
#             },
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.state, Poll.STATE_FINISHED)
#         self.assertTrue(Vote.objects.exists())
#
#     def test_create_with_votes2(self) -> None:
#         user, _ = self.create_user()
#         self.assignment.add_candidate(user)
#         self.assignment.remove_candidate(self.admin)
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_dKbv5tV47IzY1oGHXdSz",
#                 "pollmethod": Poll.POLLMETHOD_Y,
#                 "type": Poll.TYPE_ANALOG,
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YNA,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#                 "votes": {
#                     "options": {"2": {"Y": 1}},
#                     "votesvalid": "-2",
#                     "votesinvalid": "11",
#                     "votescast": "-2",
#                 },
#             },
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.state, Poll.STATE_FINISHED)
#         self.assertTrue(Vote.objects.exists())
#
#     def test_create_with_votes_publish_immediately_method_y(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_dKbv5tV47IzY1oGHXdSz",
#                 "pollmethod": Poll.POLLMETHOD_Y,
#                 "type": Poll.TYPE_ANALOG,
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YNA,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#                 "votes": {
#                     "options": {"1": {"Y": 1}},
#                     "votesvalid": "-2",
#                     "votesinvalid": "-2",
#                     "votescast": "-2",
#                 },
#                 "publish_immediately": "1",
#             },
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.state, Poll.STATE_PUBLISHED)
#         self.assertTrue(Vote.objects.exists())
#
#     def test_create_with_votes_publish_immediately_method_n(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_greoGKPO3FeBAfwpefl3",
#                 "pollmethod": Poll.POLLMETHOD_N,
#                 "type": Poll.TYPE_ANALOG,
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YNA,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#                 "votes": {
#                     "options": {"1": {"N": 1}},
#                     "votesvalid": "-2",
#                     "votesinvalid": "-2",
#                     "votescast": "-2",
#                     "amount_global_yes": 1,
#                     "amount_global_no": 2,
#                     "amount_global_abstain": 3,
#                 },
#                 "publish_immediately": "1",
#             },
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.state, Poll.STATE_PUBLISHED)
#         self.assertTrue(Vote.objects.exists())
#         self.assertEqual(poll.amount_global_yes, Decimal("1"))
#         self.assertEqual(poll.amount_global_no, Decimal("2"))
#         self.assertEqual(poll.amount_global_abstain, Decimal("3"))
#         option = poll.options.get(pk=1)
#         self.assertEqual(option.yes, Decimal("0"))
#         self.assertEqual(option.no, Decimal("1"))
#         self.assertEqual(option.abstain, Decimal("0"))
#
#     def test_create_with_invalid_votes(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_dKbv5tV47IzY1oGHXdSz",
#                 "pollmethod": Poll.POLLMETHOD_Y,
#                 "type": Poll.TYPE_ANALOG,
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YNA,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#                 "votes": {
#                     "options": {"1": {"Y": 1}},
#                     "votesvalid": "-2",
#                     "votesinvalid": "-2",
#                 },
#             },
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.exists())
#         self.assertFalse(Vote.objects.exists())
#
#     def test_create_with_votes_wrong_type(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-list",
#             {
#                 "title": "test_title_dKbv5tV47IzY1oGHXdSz",
#                 "pollmethod": Poll.POLLMETHOD_Y,
#                 "type": Poll.TYPE_NAMED,
#                 "assignment_id": self.assignment.id,
#                 "onehundred_percent_base": Poll.PERCENT_BASE_YNA,
#                 "majority_method": Poll.MAJORITY_SIMPLE,
#                 "votes": {
#                     "options": {"1": {"Y": 1}},
#                     "votesvalid": "-2",
#                     "votesinvalid": "-2",
#                     "votescast": "-2",
#                 },
#             },
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.exists())
#         self.assertFalse(Vote.objects.exists())
#
#
# class UpdatePoll(BaseActionTestCase):
#     """
#     Tests updating polls of assignments.
#     """
#
#     def advancedSetUp(self) -> None:
#         self.assignment = Assignment.objects.create(
#             title="test_assignment_ohneivoh9caiB8Yiungo", open_posts=1
#         )
#         self.assignment.add_candidate(self.admin)
#         self.group = self.get_model("group/1")
#         self.poll = Poll.objects.create(
#             assignment=self.assignment,
#             title="test_title_beeFaihuNae1vej2ai8m",
#             pollmethod=Poll.POLLMETHOD_Y,
#             type=Poll.TYPE_NAMED,
#             onehundred_percent_base=Poll.PERCENT_BASE_Y,
#             majority_method=Poll.MAJORITY_SIMPLE,
#         )
#         self.poll.create_options()
#         self.poll.groups.add(self.group)
#
#     def test_patch_title(self) -> None:
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"title": "test_title_Aishohh1ohd0aiSut7gi"},
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.title, "test_title_Aishohh1ohd0aiSut7gi")
#
#     def test_prevent_patching_assignment(self) -> None:
#         assignment = Assignment(title="test_title_phohdah8quukooHeetuz", open_posts=1)
#         assignment.save()
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"assignment_id": assignment.id},
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.assignment.id, self.assignment.id)  # unchanged
#
#     def test_patch_pollmethod(self) -> None:
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"pollmethod": Poll.POLLMETHOD_YNA},
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.pollmethod, Poll.POLLMETHOD_YNA)
#         self.assertEqual(poll.onehundred_percent_base, Poll.PERCENT_BASE_YNA)
#
#     def test_patch_invalid_pollmethod(self) -> None:
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"pollmethod": "invalid"},
#         )
#         self.assert_status_code(response, 400)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.pollmethod, Poll.POLLMETHOD_Y)
#
#     def test_patch_type(self) -> None:
#         response = self.client.patch("assignmentpoll-detail", {"type": "analog"})
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.type, "analog")
#
#     def test_patch_invalid_type(self) -> None:
#         response = self.client.patch("assignmentpoll-detail", {"type": "invalid"})
#         self.assert_status_code(response, 400)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.type, "named")
#
#     def test_patch_not_allowed_type(self) -> None:
#         # setattr(settings, "ENABLE_ELECTRONIC_VOTING", False)
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"type": Poll.TYPE_NAMED},
#         )
#         self.assert_status_code(response, 400)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.type, Poll.TYPE_NAMED)
#         # setattr(settings, "ENABLE_ELECTRONIC_VOTING", True)
#
#     def test_patch_groups_to_empty(self) -> None:
#         response = self.client.patch("assignmentpoll-detail", {"groups_id": []})
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertFalse(poll.groups.exists())
#
#     def test_patch_groups(self) -> None:
#         group2 = self.get_model("group/2")
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"groups_id": [group2.id]},
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.groups.count(), 1)
#         self.assertEqual(poll.groups.get(), group2)
#
#     def test_patch_title_started(self) -> None:
#         self.poll.state = 2
#         self.poll.save()
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"title": "test_title_Oophah8EaLaequu3toh8"},
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.title, "test_title_Oophah8EaLaequu3toh8")
#
#     def test_patch_wrong_state(self) -> None:
#         self.poll.state = 2
#         self.poll.save()
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"type": Poll.TYPE_NAMED},
#         )
#         self.assert_status_code(response, 400)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.type, Poll.TYPE_NAMED)
#
#     def test_patch_100_percent_base(self) -> None:
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"onehundred_percent_base": "cast"},
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.onehundred_percent_base, "cast")
#
#     def test_patch_wrong_100_percent_base(self) -> None:
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"onehundred_percent_base": "invalid"},
#         )
#         self.assert_status_code(response, 400)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.onehundred_percent_base, Poll.PERCENT_BASE_Y)
#
#     def test_patch_majority_method(self) -> None:
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"majority_method": Poll.MAJORITY_TWO_THIRDS},
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.majority_method, Poll.MAJORITY_TWO_THIRDS)
#
#     def test_patch_wrong_majority_method(self) -> None:
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"majority_method": "invalid majority method"},
#         )
#         self.assert_status_code(response, 400)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.majority_method, Poll.MAJORITY_SIMPLE)
#
#     def test_patch_multiple_fields(self) -> None:
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {
#                 "title": "test_title_ees6Tho8ahheen4cieja",
#                 "pollmethod": Poll.POLLMETHOD_Y,
#                 "global_yes": True,
#                 "global_no": True,
#                 "global_abstain": False,
#                 "allow_multiple_votes_per_candidate": True,
#                 "votes_amount": 42,
#             },
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.title, "test_title_ees6Tho8ahheen4cieja")
#         self.assertEqual(poll.pollmethod, Poll.POLLMETHOD_Y)
#         self.assertTrue(poll.global_yes)
#         self.assertTrue(poll.global_no)
#         self.assertFalse(poll.global_abstain)
#         self.assertEqual(poll.amount_global_yes, Decimal("0"))
#         self.assertEqual(poll.amount_global_no, Decimal("0"))
#         self.assertEqual(poll.amount_global_abstain, None)
#         self.assertTrue(poll.allow_multiple_votes_per_candidate)
#         self.assertEqual(poll.votes_amount, 42)
#
#     def test_patch_majority_method_state_not_created(self) -> None:
#         self.poll.state = 2
#         self.poll.save()
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"majority_method": "two_thirds"},
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.majority_method, "two_thirds")
#
#     def test_patch_100_percent_base_state_not_created(self) -> None:
#         self.poll.state = 2
#         self.poll.save()
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"onehundred_percent_base": "cast"},
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.onehundred_percent_base, "cast")
#
#     def test_patch_wrong_100_percent_base_state_not_created(self) -> None:
#         self.poll.state = 2
#         self.poll.pollmethod = Poll.POLLMETHOD_YN
#         self.poll.save()
#         response = self.client.patch(
#             "assignmentpoll-detail",
#             {"onehundred_percent_base": Poll.PERCENT_BASE_YNA},
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.onehundred_percent_base, "YN")
#
#
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


# class VotePollAnalogYNA(VotePollBaseTestClass):
#     def create_poll(self) -> None:
#         return Poll.objects.create(
#             assignment=self.assignment,
#             title="test_title_04k0y4TwPLpJKaSvIGm1",
#             pollmethod=Poll.POLLMETHOD_YNA,
#             type=Poll.TYPE_ANALOG,
#         )
#
#     def test_start_poll(self) -> None:
#         response = self.client.post("assignmentpoll-start", args=[self.poll.pk])
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.state, Poll.STATE_STARTED)
#         self.assertEqual(poll.votesvalid, None)
#         self.assertEqual(poll.votesinvalid, None)
#         self.assertEqual(poll.votescast, None)
#         self.assertFalse(poll.get_votes().exists())
#
#     def test_stop_poll(self) -> None:
#         self.start_poll()
#         response = self.client.post("assignmentpoll-stop", args=[self.poll.pk])
#         self.assert_status_code(response, 400)
#         self.assertEqual(self.poll.state, Poll.STATE_STARTED)
#
#     def test_vote(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {
#                 "data": {
#                     "options": {
#                         "1": {"Y": "1", "N": "2.35", "A": "-1"},
#                         "2": {"Y": "30", "N": "-2", "A": "8.93"},
#                     },
#                     "votesvalid": "4.64",
#                     "votesinvalid": "-2",
#                     "votescast": "-2",
#                 },
#             },
#         )
#         self.assert_status_code(response, 200)
#         self.assertEqual(Vote.objects.count(), 6)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.votesvalid, Decimal("4.64"))
#         self.assertEqual(poll.votesinvalid, Decimal("-2"))
#         self.assertEqual(poll.votescast, Decimal("-2"))
#         self.assertEqual(poll.state, Poll.STATE_FINISHED)
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         self.assertEqual(option1.yes, Decimal("1"))
#         self.assertEqual(option1.no, Decimal("2.35"))
#         self.assertEqual(option1.abstain, Decimal("-1"))
#         self.assertEqual(option2.yes, Decimal("30"))
#         self.assertEqual(option2.no, Decimal("-2"))
#         self.assertEqual(option2.abstain, Decimal("8.93"))
#
#     def test_vote_fractional_negative_values(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {
#                 "data": {
#                     "options": {"1": {"Y": "1", "N": "1", "A": "1"}},
#                     "votesvalid": "-1.5",
#                     "votesinvalid": "-2",
#                     "votescast": "-2",
#                 },
#             },
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_too_many_options(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {
#                 "data": {
#                     "options": {
#                         "1": {"Y": "1", "N": "2.35", "A": "-1"},
#                         "2": {"Y": "1", "N": "2.35", "A": "-1"},
#                     }
#                 },
#             },
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_too_few_options(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"options": {"1": {"Y": "1", "N": "2.35", "A": "-1"}}}},
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_options(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {
#                 "data": {
#                     "options": {
#                         "1": {"Y": "1", "N": "2.35", "A": "-1"},
#                         "3": {"Y": "1", "N": "2.35", "A": "-1"},
#                     }
#                 }
#             },
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_no_permissions(self) -> None:
#         self.start_poll()
#         self.make_admin_delegate()
#         response = self.client.post("assignmentpoll-vote", {"data": {}})
#         self.assert_status_code(response, 403)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_state(self) -> None:
#         response = self.client.post("assignmentpoll-vote", {"data": {}})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_missing_data(self) -> None:
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": {}})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_data_format(self) -> None:
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": [1, 2, 5]})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_option_format(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"options": [1, "string"]}},
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_option_id_type(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"options": {"string": "some_other_string"}}},
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_vote_data(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"options": {"1": [None]}}},
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_missing_vote_value(self) -> None:
#         self.start_poll()
#         for value in "YNA":
#             data = {"options": {"1": {"Y": "1", "N": "3", "A": "-1"}}}
#             del data["options"]["1"][value]
#             response = self.client.post("assignmentpoll-vote", {"data": data})
#             self.assert_status_code(response, 400)
#             self.assertFalse(Vote.objects.exists())
#
#     def test_vote_state_finished(self) -> None:
#         self.start_poll()
#         self.client.post(
#             "assignmentpoll-vote",
#             {
#                 "data": {
#                     "options": {"1": {"Y": 5, "N": 0, "A": 1}},
#                     "votesvalid": "-2",
#                     "votesinvalid": "1",
#                     "votescast": "-1",
#                 }
#             },
#         )
#         self.poll.state = 3
#         self.poll.save()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {
#                 "data": {
#                     "options": {"1": {"Y": 2, "N": 2, "A": 2}},
#                     "votesvalid": "4.64",
#                     "votesinvalid": "-2",
#                     "votescast": "3",
#                 }
#             },
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.votesvalid, Decimal("4.64"))
#         self.assertEqual(poll.votesinvalid, Decimal("-2"))
#         self.assertEqual(poll.votescast, Decimal("3"))
#         self.assertEqual(poll.get_votes().count(), 3)
#         option = poll.options.get()
#         self.assertEqual(option.yes, Decimal("2"))
#         self.assertEqual(option.no, Decimal("2"))
#         self.assertEqual(option.abstain, Decimal("2"))
#
#
# class VotePollNamedYNA(VotePollBaseTestClass):
#     def create_poll(self) -> None:
#         return Poll.objects.create(
#             assignment=self.assignment,
#             title="test_title_OkHAIvOSIcpFnCxbaL6v",
#             pollmethod=Poll.POLLMETHOD_YNA,
#             type=Poll.TYPE_NAMED,
#         )
#
#     def test_start_poll(self) -> None:
#         response = self.client.post("assignmentpoll-start", args=[self.poll.pk])
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.state, Poll.STATE_STARTED)
#         self.assertEqual(poll.votesvalid, Decimal("0"))
#         self.assertEqual(poll.votesinvalid, Decimal("0"))
#         self.assertEqual(poll.votescast, Decimal("0"))
#         self.assertFalse(poll.get_votes().exists())
#
#     def test_vote(self) -> None:
#         self.add_candidate()
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y", "2": "N", "3": "A"}},
#             format="json",
#         )
#         self.assert_status_code(response, 200)
#         self.assertEqual(Vote.objects.count(), 3)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.votesvalid, Decimal("1"))
#         self.assertEqual(poll.votesinvalid, Decimal("0"))
#         self.assertEqual(poll.votescast, Decimal("1"))
#         self.assertEqual(poll.state, Poll.STATE_STARTED)
#         self.assertEqual(poll.amount_users_voted_with_individual_weight(), Decimal("1"))
#         self.assertTrue(self.admin in poll.voted.all())
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         option3 = poll.options.get(pk=3)
#         self.assertEqual(option1.yes, Decimal("1"))
#         self.assertEqual(option1.no, Decimal("0"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("0"))
#         self.assertEqual(option2.no, Decimal("1"))
#         self.assertEqual(option2.abstain, Decimal("0"))
#         self.assertEqual(option3.yes, Decimal("0"))
#         self.assertEqual(option3.no, Decimal("0"))
#         self.assertEqual(option3.abstain, Decimal("1"))
#
#     def test_vote_with_voteweight(self) -> None:
#         # config["users_activate_vote_weight"] = True
#         self.admin.vote_weight = weight = Decimal("4.2")
#         self.admin.save()
#         self.add_candidate()
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y", "2": "N", "3": "A"}},
#         )
#         self.assert_status_code(response, 200)
#         self.assertEqual(Vote.objects.count(), 3)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.votesvalid, weight)
#         self.assertEqual(poll.votesinvalid, Decimal("0"))
#         self.assertEqual(poll.votescast, Decimal("1"))
#         self.assertEqual(poll.state, Poll.STATE_STARTED)
#         self.assertEqual(poll.amount_users_voted_with_individual_weight(), weight)
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         option3 = poll.options.get(pk=3)
#         self.assertEqual(option1.yes, weight)
#         self.assertEqual(option1.no, Decimal("0"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("0"))
#         self.assertEqual(option2.no, weight)
#         self.assertEqual(option2.abstain, Decimal("0"))
#         self.assertEqual(option3.yes, Decimal("0"))
#         self.assertEqual(option3.no, Decimal("0"))
#         self.assertEqual(option3.abstain, weight)
#
#     def test_vote_without_voteweight(self) -> None:
#         self.admin.vote_weight = Decimal("4.2")
#         self.admin.save()
#         self.test_vote()
#
#     def test_change_vote(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y"}},
#             format="json",
#         )
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "N"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertEqual(Vote.objects.count(), 1)
#         vote = Vote.objects.get()
#         self.assertEqual(vote.value, "Y")
#
#     def test_option_from_wrong_poll(self) -> None:
#         self.poll2 = self.create_poll()
#         self.poll2.create_options()
#         # start both polls
#         self.poll.state = Poll.STATE_STARTED
#         self.poll.save()
#         self.poll2.state = Poll.STATE_STARTED
#         self.poll2.save()
#         option2 = self.poll2.options.get()
#         # Do request to poll with option2 (which is wrong...)
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {str(option2.id): "Y"}},
#         )
#         self.assert_status_code(response, 400)
#         self.assertEqual(Vote.objects.count(), 0)
#         option = self.poll.options.get()
#         option2 = self.poll2.options.get()
#         self.assertEqual(option.yes, Decimal("0"))
#         self.assertEqual(option.no, Decimal("0"))
#         self.assertEqual(option.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("0"))
#         self.assertEqual(option2.no, Decimal("0"))
#         self.assertEqual(option2.abstain, Decimal("0"))
#
#     def test_too_many_options(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y", "2": "N"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_partial_vote(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y"}},
#             format="json",
#         )
#         self.assert_status_code(response, 200)
#         self.assertTrue(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_options(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y", "3": "N"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_no_permissions(self) -> None:
#         self.start_poll()
#         self.make_admin_delegate()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y"}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_anonymous(self) -> None:
#         self.start_poll()
#         gclient = self.create_guest_client()
#         response = gclient.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y"}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_vote_not_present(self) -> None:
#         self.start_poll()
#         self.admin.is_present = False
#         self.admin.save()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y"}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_state(self) -> None:
#         response = self.client.post("assignmentpoll-vote", {"data": {}})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_missing_data(self) -> None:
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": {}})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#         poll = Poll.objects.get()
#         self.assertNotIn(self.admin.id, poll.voted.all())
#
#     def test_wrong_data_format(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": [1, 2, 5]},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_option_format(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "string"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_option_id_type(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"id": "Y"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_vote_data(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": [None]}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#
# class VotePollNamedY(VotePollBaseTestClass):
#     def create_poll(self) -> None:
#         return Poll.objects.create(
#             assignment=self.assignment,
#             title="test_title_Zrvh146QAdq7t6iSDwZk",
#             pollmethod=Poll.POLLMETHOD_Y,
#             type=Poll.TYPE_NAMED,
#         )
#
#     def setup_for_multiple_votes(self) -> None:
#         self.poll.allow_multiple_votes_per_candidate = True
#         self.poll.votes_amount = 3
#         self.poll.save()
#         self.add_candidate()
#
#     def test_start_poll(self) -> None:
#         response = self.client.post("assignmentpoll-start", args=[self.poll.pk])
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.state, Poll.STATE_STARTED)
#         self.assertEqual(poll.votesvalid, Decimal("0"))
#         self.assertEqual(poll.votesinvalid, Decimal("0"))
#         self.assertEqual(poll.votescast, Decimal("0"))
#         self.assertFalse(poll.get_votes().exists())
#
#     def test_vote(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1, "2": 0}},
#             format="json",
#         )
#         self.assert_status_code(response, 200)
#         self.assertEqual(Vote.objects.count(), 1)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.votesvalid, Decimal("1"))
#         self.assertEqual(poll.votesinvalid, Decimal("0"))
#         self.assertEqual(poll.votescast, Decimal("1"))
#         self.assertEqual(poll.state, Poll.STATE_STARTED)
#         self.assertTrue(self.admin in poll.voted.all())
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         self.assertEqual(option1.yes, Decimal("1"))
#         self.assertEqual(option1.no, Decimal("0"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("0"))
#         self.assertEqual(option2.no, Decimal("0"))
#         self.assertEqual(option2.abstain, Decimal("0"))
#
#     def test_change_vote(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1, "2": 0}},
#             format="json",
#         )
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 0, "2": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         poll = Poll.objects.get()
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         self.assertEqual(option1.yes, Decimal("1"))
#         self.assertEqual(option1.no, Decimal("0"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("0"))
#         self.assertEqual(option2.no, Decimal("0"))
#         self.assertEqual(option2.abstain, Decimal("0"))
#
#     def test_global_yes(self) -> None:
#         self.poll.votes_amount = 2
#         self.poll.save()
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": "Y"})
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         option = poll.options.get(pk=1)
#         self.assertEqual(option.yes, Decimal("1"))
#         self.assertEqual(option.no, Decimal("0"))
#         self.assertEqual(option.abstain, Decimal("0"))
#         self.assertEqual(poll.amount_global_yes, Decimal("1"))
#         self.assertEqual(poll.amount_global_no, Decimal("0"))
#         self.assertEqual(poll.amount_global_abstain, Decimal("0"))
#
#     def test_global_yes_forbidden(self) -> None:
#         self.poll.global_yes = False
#         self.poll.save()
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": "Y"})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#         self.assertEqual(Poll.objects.get().amount_global_yes, None)
#
#     def test_global_no(self) -> None:
#         self.poll.votes_amount = 2
#         self.poll.save()
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": "N"})
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         option = poll.options.get(pk=1)
#         self.assertEqual(option.yes, Decimal("0"))
#         self.assertEqual(option.no, Decimal("1"))
#         self.assertEqual(option.abstain, Decimal("0"))
#         self.assertEqual(poll.amount_global_yes, Decimal("0"))
#         self.assertEqual(poll.amount_global_no, Decimal("1"))
#         self.assertEqual(poll.amount_global_abstain, Decimal("0"))
#
#     def test_global_no_forbidden(self) -> None:
#         self.poll.global_no = False
#         self.poll.save()
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": "N"})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#         self.assertEqual(Poll.objects.get().amount_global_no, None)
#
#     def test_global_abstain(self) -> None:
#         self.poll.votes_amount = 2
#         self.poll.save()
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": "A"})
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         option = poll.options.get(pk=1)
#         self.assertEqual(option.yes, Decimal("0"))
#         self.assertEqual(option.no, Decimal("0"))
#         self.assertEqual(option.abstain, Decimal("1"))
#         self.assertEqual(poll.amount_global_yes, Decimal("0"))
#         self.assertEqual(poll.amount_global_no, Decimal("0"))
#         self.assertEqual(poll.amount_global_abstain, Decimal("1"))
#
#     def test_global_abstain_forbidden(self) -> None:
#         self.poll.global_abstain = False
#         self.poll.save()
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": "A"})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#         self.assertEqual(Poll.objects.get().amount_global_abstain, None)
#
#     def test_negative_vote(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": -1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_multiple_votes(self) -> None:
#         self.setup_for_multiple_votes()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 2, "2": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         self.assertEqual(option1.yes, Decimal("2"))
#         self.assertEqual(option1.no, Decimal("0"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("1"))
#         self.assertEqual(option2.no, Decimal("0"))
#         self.assertEqual(option2.abstain, Decimal("0"))
#
#     def test_multiple_votes_wrong_amount(self) -> None:
#         self.setup_for_multiple_votes()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 2, "2": 2}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_too_many_options(self) -> None:
#         self.setup_for_multiple_votes()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1, "2": 1, "3": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_options(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"2": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_no_permissions(self) -> None:
#         self.start_poll()
#         self.make_admin_delegate()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_anonymous(self) -> None:
#         self.start_poll()
#         gclient = self.create_guest_client()
#         response = gclient.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_vote_not_present(self) -> None:
#         self.start_poll()
#         self.admin.is_present = False
#         self.admin.save()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_state(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_missing_data(self) -> None:
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": {}})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#         poll = Poll.objects.get()
#         self.assertNotIn(self.admin.id, poll.voted.all())
#
#     def test_wrong_data_format(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": [1, 2, 5]},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_option_format(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "string"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_option_id_type(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"id": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_vote_data(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": [None]}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#
# class VotePollNamedN(VotePollBaseTestClass):
#     def create_poll(self) -> None:
#         return Poll.objects.create(
#             assignment=self.assignment,
#             title="test_title_4oi49ckKFk39SDIfj30s",
#             pollmethod=Poll.POLLMETHOD_N,
#             type=Poll.TYPE_NAMED,
#         )
#
#     def setup_for_multiple_votes(self) -> None:
#         self.poll.allow_multiple_votes_per_candidate = True
#         self.poll.votes_amount = 3
#         self.poll.save()
#         self.add_candidate()
#
#     def test_start_poll(self) -> None:
#         response = self.client.post("assignmentpoll-start", args=[self.poll.pk])
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.state, Poll.STATE_STARTED)
#         self.assertEqual(poll.votesvalid, Decimal("0"))
#         self.assertEqual(poll.votesinvalid, Decimal("0"))
#         self.assertEqual(poll.votescast, Decimal("0"))
#         self.assertFalse(poll.get_votes().exists())
#
#     def test_vote(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1, "2": 0}},
#             format="json",
#         )
#         self.assert_status_code(response, 200)
#         self.assertEqual(Vote.objects.count(), 1)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.votesvalid, Decimal("1"))
#         self.assertEqual(poll.votesinvalid, Decimal("0"))
#         self.assertEqual(poll.votescast, Decimal("1"))
#         self.assertEqual(poll.state, Poll.STATE_STARTED)
#         self.assertTrue(self.admin in poll.voted.all())
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         self.assertEqual(option1.yes, Decimal("0"))
#         self.assertEqual(option1.no, Decimal("1"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("0"))
#         self.assertEqual(option2.no, Decimal("0"))
#         self.assertEqual(option2.abstain, Decimal("0"))
#
#     def test_change_vote(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1, "2": 0}},
#             format="json",
#         )
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 0, "2": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         poll = Poll.objects.get()
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         self.assertEqual(option1.yes, Decimal("0"))
#         self.assertEqual(option1.no, Decimal("1"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("0"))
#         self.assertEqual(option2.no, Decimal("0"))
#         self.assertEqual(option2.abstain, Decimal("0"))
#
#     def test_global_yes(self) -> None:
#         self.poll.votes_amount = 2
#         self.poll.save()
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": "Y"})
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         option = poll.options.get(pk=1)
#         self.assertEqual(option.yes, Decimal("1"))
#         self.assertEqual(option.no, Decimal("0"))
#         self.assertEqual(option.abstain, Decimal("0"))
#         self.assertEqual(poll.amount_global_yes, Decimal("1"))
#         self.assertEqual(poll.amount_global_no, Decimal("0"))
#         self.assertEqual(poll.amount_global_abstain, Decimal("0"))
#
#     def test_global_yes_forbidden(self) -> None:
#         self.poll.global_yes = False
#         self.poll.save()
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": "Y"})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#         self.assertEqual(Poll.objects.get().amount_global_yes, None)
#
#     def test_global_no(self) -> None:
#         self.poll.votes_amount = 2
#         self.poll.save()
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": "N"})
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         option = poll.options.get(pk=1)
#         self.assertEqual(option.yes, Decimal("0"))
#         self.assertEqual(option.no, Decimal("1"))
#         self.assertEqual(option.abstain, Decimal("0"))
#         self.assertEqual(poll.amount_global_yes, Decimal("0"))
#         self.assertEqual(poll.amount_global_no, Decimal("1"))
#         self.assertEqual(poll.amount_global_abstain, Decimal("0"))
#
#     def test_global_no_forbidden(self) -> None:
#         self.poll.global_no = False
#         self.poll.save()
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": "N"})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#         self.assertEqual(Poll.objects.get().amount_global_no, None)
#
#     def test_global_abstain(self) -> None:
#         self.poll.votes_amount = 2
#         self.poll.save()
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": "A"})
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         option = poll.options.get(pk=1)
#         self.assertEqual(option.yes, Decimal("0"))
#         self.assertEqual(option.no, Decimal("0"))
#         self.assertEqual(option.abstain, Decimal("1"))
#         self.assertEqual(poll.amount_global_yes, Decimal("0"))
#         self.assertEqual(poll.amount_global_no, Decimal("0"))
#         self.assertEqual(poll.amount_global_abstain, Decimal("1"))
#
#     def test_global_abstain_forbidden(self) -> None:
#         self.poll.global_abstain = False
#         self.poll.save()
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": "A"})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#         self.assertEqual(Poll.objects.get().amount_global_abstain, None)
#
#     def test_negative_vote(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": -1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_multiple_votes(self) -> None:
#         self.setup_for_multiple_votes()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 2, "2": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         self.assertEqual(option1.yes, Decimal("0"))
#         self.assertEqual(option1.no, Decimal("2"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("0"))
#         self.assertEqual(option2.no, Decimal("1"))
#         self.assertEqual(option2.abstain, Decimal("0"))
#
#     def test_multiple_votes_wrong_amount(self) -> None:
#         self.setup_for_multiple_votes()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 2, "2": 2}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_too_many_options(self) -> None:
#         self.setup_for_multiple_votes()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1, "2": 1, "3": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_options(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"2": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_no_permissions(self) -> None:
#         self.start_poll()
#         self.make_admin_delegate()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_anonymous(self) -> None:
#         self.start_poll()
#         gclient = self.create_guest_client()
#         response = gclient.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_vote_not_present(self) -> None:
#         self.start_poll()
#         self.admin.is_present = False
#         self.admin.save()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_state(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_missing_data(self) -> None:
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": {}})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#         poll = Poll.objects.get()
#         self.assertNotIn(self.admin.id, poll.voted.all())
#
#     def test_wrong_data_format(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": [1, 2, 5]},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_option_format(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "string"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_option_id_type(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"id": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_vote_data(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": [None]}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#
# class VotePollPseudoanonymousYNA(VotePollBaseTestClass):
#     def create_poll(self) -> None:
#         return Poll.objects.create(
#             assignment=self.assignment,
#             title="test_title_OkHAIvOSIcpFnCxbaL6v",
#             pollmethod=Poll.POLLMETHOD_YNA,
#             type=Poll.TYPE_PSEUDOANONYMOUS,
#         )
#
#     def test_start_poll(self) -> None:
#         response = self.client.post("assignmentpoll-start", args=[self.poll.pk])
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.state, Poll.STATE_STARTED)
#         self.assertEqual(poll.votesvalid, Decimal("0"))
#         self.assertEqual(poll.votesinvalid, Decimal("0"))
#         self.assertEqual(poll.votescast, Decimal("0"))
#         self.assertFalse(poll.get_votes().exists())
#
#     def test_vote(self) -> None:
#         self.add_candidate()
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y", "2": "N", "3": "A"}},
#             format="json",
#         )
#         self.assert_status_code(response, 200)
#         self.assertEqual(Vote.objects.count(), 3)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.votesvalid, Decimal("1"))
#         self.assertEqual(poll.votesinvalid, Decimal("0"))
#         self.assertEqual(poll.votescast, Decimal("1"))
#         self.assertEqual(poll.state, Poll.STATE_STARTED)
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         option3 = poll.options.get(pk=3)
#         self.assertEqual(option1.yes, Decimal("1"))
#         self.assertEqual(option1.no, Decimal("0"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("0"))
#         self.assertEqual(option2.no, Decimal("1"))
#         self.assertEqual(option2.abstain, Decimal("0"))
#         self.assertEqual(option3.yes, Decimal("0"))
#         self.assertEqual(option3.no, Decimal("0"))
#         self.assertEqual(option3.abstain, Decimal("1"))
#
#     def test_change_vote(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y"}},
#             format="json",
#         )
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "N"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         poll = Poll.objects.get()
#         option1 = poll.options.get(pk=1)
#         self.assertEqual(option1.yes, Decimal("1"))
#         self.assertEqual(option1.no, Decimal("0"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#
#     def test_too_many_options(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y", "2": "N"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_partial_vote(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y"}},
#             format="json",
#         )
#         self.assert_status_code(response, 200)
#         self.assertTrue(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_options(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y", "3": "N"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_no_permissions(self) -> None:
#         self.start_poll()
#         self.make_admin_delegate()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y"}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_anonymous(self) -> None:
#         self.start_poll()
#         gclient = self.create_guest_client()
#         response = gclient.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y"}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_vote_not_present(self) -> None:
#         self.start_poll()
#         self.admin.is_present = False
#         self.admin.save()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "Y"}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_state(self) -> None:
#         response = self.client.post("assignmentpoll-vote", {"data": {}})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_missing_data(self) -> None:
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": {}})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#         poll = Poll.objects.get()
#         self.assertNotIn(self.admin.id, poll.voted.all())
#
#     def test_wrong_data_format(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": [1, 2, 5]},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_option_format(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "string"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_option_id_type(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"id": "Y"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_vote_data(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": [None]}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#
# class VotePollPseudoanonymousY(VotePollBaseTestClass):
#     def create_poll(self) -> None:
#         return Poll.objects.create(
#             assignment=self.assignment,
#             title="test_title_Zrvh146QAdq7t6iSDwZk",
#             pollmethod=Poll.POLLMETHOD_Y,
#             type=Poll.TYPE_PSEUDOANONYMOUS,
#         )
#
#     def setup_for_multiple_votes(self) -> None:
#         self.poll.allow_multiple_votes_per_candidate = True
#         self.poll.votes_amount = 3
#         self.poll.save()
#         self.add_candidate()
#
#     def test_start_poll(self) -> None:
#         response = self.client.post("assignmentpoll-start", args=[self.poll.pk])
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.state, Poll.STATE_STARTED)
#         self.assertEqual(poll.votesvalid, Decimal("0"))
#         self.assertEqual(poll.votesinvalid, Decimal("0"))
#         self.assertEqual(poll.votescast, Decimal("0"))
#         self.assertFalse(poll.get_votes().exists())
#
#     def test_vote(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1, "2": 0}},
#             format="json",
#         )
#         self.assert_status_code(response, 200)
#         self.assertEqual(Vote.objects.count(), 1)
#         poll = Poll.objects.get()
#         self.assertEqual(poll.votesvalid, Decimal("1"))
#         self.assertEqual(poll.votesinvalid, Decimal("0"))
#         self.assertEqual(poll.votescast, Decimal("1"))
#         self.assertEqual(poll.state, Poll.STATE_STARTED)
#         self.assertTrue(self.admin in poll.voted.all())
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         self.assertEqual(option1.yes, Decimal("1"))
#         self.assertEqual(option1.no, Decimal("0"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("0"))
#         self.assertEqual(option2.no, Decimal("0"))
#         self.assertEqual(option2.abstain, Decimal("0"))
#         for vote in poll.get_votes():
#             self.assertIsNone(vote.user)
#
#     def test_change_vote(self) -> None:
#         self.add_candidate()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1, "2": 0}},
#             format="json",
#         )
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 0, "2": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         poll = Poll.objects.get()
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         self.assertEqual(option1.yes, Decimal("1"))
#         self.assertEqual(option1.no, Decimal("0"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("0"))
#         self.assertEqual(option2.no, Decimal("0"))
#         self.assertEqual(option2.abstain, Decimal("0"))
#
#     def test_negative_vote(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": -1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_multiple_votes(self) -> None:
#         self.setup_for_multiple_votes()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 2, "2": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 200)
#         poll = Poll.objects.get()
#         option1 = poll.options.get(pk=1)
#         option2 = poll.options.get(pk=2)
#         self.assertEqual(option1.yes, Decimal("2"))
#         self.assertEqual(option1.no, Decimal("0"))
#         self.assertEqual(option1.abstain, Decimal("0"))
#         self.assertEqual(option2.yes, Decimal("1"))
#         self.assertEqual(option2.no, Decimal("0"))
#         self.assertEqual(option2.abstain, Decimal("0"))
#         for vote in poll.get_votes():
#             self.assertIsNone(vote.user)
#
#     def test_multiple_votes_wrong_amount(self) -> None:
#         self.setup_for_multiple_votes()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 2, "2": 2}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_too_many_options(self) -> None:
#         self.setup_for_multiple_votes()
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1, "2": 1, "3": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_options(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"2": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_no_permissions(self) -> None:
#         self.start_poll()
#         self.make_admin_delegate()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_anonymous(self) -> None:
#         self.start_poll()
#         gclient = self.create_guest_client()
#         response = gclient.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_vote_not_present(self) -> None:
#         self.start_poll()
#         self.admin.is_present = False
#         self.admin.save()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 403)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_state(self) -> None:
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_missing_data(self) -> None:
#         self.start_poll()
#         response = self.client.post("assignmentpoll-vote", {"data": {}})
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#         poll = Poll.objects.get()
#         self.assertNotIn(self.admin.id, poll.voted.all())
#
#     def test_wrong_data_format(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"data": [1, 2, 5]}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_option_format(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": "string"}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Poll.objects.get().get_votes().exists())
#
#     def test_wrong_option_id_type(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"id": 1}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#     def test_wrong_vote_data(self) -> None:
#         self.start_poll()
#         response = self.client.post(
#             "assignmentpoll-vote",
#             {"data": {"1": [None]}},
#             format="json",
#         )
#         self.assert_status_code(response, 400)
#         self.assertFalse(Vote.objects.exists())
#
#


class VotePollAnonymousN(VotePollBaseTestClass):
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
