from collections.abc import Iterable
from typing import Any, Literal, cast

from openslides_backend.action.relations.relation_manager import RelationManager
from openslides_backend.action.util.actions_map import actions_map
from openslides_backend.models.mixins import DEFAULT_PROJECTOR_OPTIONS
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.patterns import (
    CollectionField,
    fqid_from_collection_and_id,
)
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.poll.test_vote import BaseVoteTestCase

# TODO:
# Test merging and deep merging of personal_notes
# Test error field errors, require_equality errors, test special functions, all merges, all deep_merges


class UserMergeTogether(BaseVoteTestCase):
    def setUp(self) -> None:
        super().setUp()
        meeting_ids_by_committee_id = {1: [1, 2], 2: [3], 3: [4]}
        num_committees = len(meeting_ids_by_committee_id)
        num_meetings = len(
            {
                id_
                for meeting_ids in meeting_ids_by_committee_id.values()
                for id_ in meeting_ids
            }
        )
        committee_id_by_meeting_id = {
            id_: committee_id
            for id_ in range(1, num_meetings + 1)
            for committee_id, meeting_ids in meeting_ids_by_committee_id.items()
            if id_ in meeting_ids
        }
        meeting_data_by_user_id: dict[int, dict[int, list[int]]] = {
            2: {1: [1, 2], 2: [2]},
            3: {2: [2], 3: [2]},
            4: {1: [2], 2: [1], 3: [3]},
            5: {1: [2], 4: [1]},
            6: {},
        }
        meeting_ids_by_user_id: dict[int, list[int]] = {
            id_: list(meeting_data_by_user_id[id_].keys())
            for id_ in meeting_data_by_user_id
        }
        num_users = len(meeting_data_by_user_id)
        user_ids_by_meeting_id = {
            id_: [
                user_id
                for user_id, meeting_ids in meeting_ids_by_user_id.items()
                if id_ in meeting_ids
            ]
            for id_ in range(1, num_meetings + 1)
        }
        group_ids_by_user_id = {
            id_: [
                (meeting_id - 1) * 3 + group_number
                for meeting_id in data
                for group_number in data[meeting_id]
            ]
            for id_, data in meeting_data_by_user_id.items()
        }
        user_ids_by_group_id = {
            id_: [
                user_id
                for user_id in group_ids_by_user_id
                if id_ in group_ids_by_user_id[user_id]
            ]
            for id_ in range(1, num_meetings * 3 + 1)
        }
        data = {
            ONE_ORGANIZATION_FQID: {
                "limit_of_meetings": 0,
                "active_meeting_ids": [
                    meeting_id for meeting_id in committee_id_by_meeting_id
                ],
                "enable_electronic_voting": True,
                "committee_ids": list(range(1, num_committees + 1)),
                "user_ids": list(meeting_data_by_user_id.keys()),
                "enable_electronic_voting": True,
            },
            **{
                fqid_from_collection_and_id("committee", id_): {
                    "organization_id": ONE_ORGANIZATION_ID,
                    "name": f"Committee {id_}",
                    "meeting_ids": meeting_ids_by_committee_id[id_],
                    "user_ids": list(
                        {
                            user_id
                            for meeting_id in meeting_ids_by_committee_id[id_]
                            for user_id in user_ids_by_meeting_id[meeting_id]
                        }
                    ),
                }
                for id_ in range(1, num_committees + 1)
            },
            **{
                fqid_from_collection_and_id("meeting", id_): {
                    "name": f"Meeting {id_}",
                    "is_active_in_organization_id": ONE_ORGANIZATION_ID,
                    "language": "en",
                    "projector_countdown_default_time": 60,
                    "projector_countdown_warning_time": 0,
                    "motions_default_workflow_id": id_,
                    "motions_default_amendment_workflow_id": id_,
                    "motions_default_statute_amendment_workflow_id": id_,
                    "users_enable_vote_delegations": True,
                    "committee_id": committee_id_by_meeting_id[id_],
                    **{
                        f"default_projector_{option}_ids": [id_]
                        for option in DEFAULT_PROJECTOR_OPTIONS
                    },
                    "group_ids": list(range(1 + (id_ - 1) * 3, 1 + id_ * 3)),
                    "admin_group_id": 1 + (id_ - 1) * 3,
                    "meeting_user_ids": [
                        id_ * 10 + user_id for user_id in user_ids_by_meeting_id[id_]
                    ],
                    "user_ids": [user_id for user_id in user_ids_by_meeting_id[id_]],
                }
                for id_ in range(1, num_meetings + 1)
            },
            **{
                fqid_from_collection_and_id("group", id_): {
                    "meeting_id": (id_ - 1) // 3 + 1,
                    "name": f"Group {id_}",
                    "admin_group_for_meeting_id": (
                        (id_ - 1) // 3 + 1 if id_ % 3 == 1 else None
                    ),
                    "default_group_for_meeting_id": (
                        (id_ - 1) // 3 + 1 if id_ % 3 == 0 else None
                    ),
                    "meeting_user_ids": [
                        ((id_ - 1) // 3 + 1) * 10 + user_id
                        for user_id in user_ids_by_group_id[id_]
                    ],
                }
                for id_ in range(1, num_meetings * 3 + 1)
            },
            **{
                fqid_from_collection_and_id("motion_workflow", id_): {
                    "name": f"Workflow {id_}",
                    "sequential_number": 1,
                    "state_ids": [id_],
                    "first_state_id": id_,
                    "meeting_id": id_,
                }
                for id_ in range(1, num_meetings + 1)
            },
            **{
                fqid_from_collection_and_id("motion_state", id_): {
                    "name": f"State {id_}",
                    "weight": 1,
                    "css_class": "lightblue",
                    "workflow_id": id_,
                    "meeting_id": id_,
                    "allow_create_poll": True,
                }
                for id_ in range(1, num_meetings + 1)
            },
            **{
                fqid_from_collection_and_id("user", id_): {
                    "username": f"user{id_}",
                    "is_active": True,
                    "default_password": f"user{id_}",
                    "password": self.auth.hash(f"user{id_}"),
                    "meeting_ids": meeting_ids_by_user_id[id_],
                    "meeting_user_ids": [
                        meeting_id * 10 + id_
                        for meeting_id in meeting_ids_by_user_id[id_]
                    ],
                    "committee_ids": list(
                        {
                            committee_id_by_meeting_id[meeting_id]
                            for meeting_id in meeting_ids_by_user_id[id_]
                        }
                    ),
                    "organization_id": ONE_ORGANIZATION_ID,
                }
                for id_ in range(2, num_users + 2)
            },
            **{
                fqid_from_collection_and_id(
                    "meeting_user", meeting_id * 10 + user_id
                ): {
                    "user_id": user_id,
                    "meeting_id": meeting_id,
                    "group_ids": [
                        group_id
                        for group_id in group_ids_by_user_id[user_id]
                        if group_id
                        in range(1 + (meeting_id - 1) * 3, 1 + meeting_id * 3)
                    ],
                    "vote_weight": "1.000000",
                }
                for user_id in range(2, num_users + 2)
                for meeting_id in range(1, num_meetings + 1)
                if user_id in user_ids_by_meeting_id[meeting_id]
            },
        }
        self.set_models(data)

    # def create_poll(self, id_: int, content_object_id: str, meeting_id, group_ids: list[int]) -> None:
    #     meeting_fqid = f"meeting/{meeting_id}"
    #     meeting = self.datastore.get(meeting_fqid, ["poll_ids"])
    #     content_object = self.datastore.get(content_object_id, ["poll_ids"])
    #     self.set_models({
    #         f"poll/{id_}": {
    #             "content_object_id": content_object_id,
    #             "title": f"Poll {id_}",
    #             "type": "named",
    #             "pollmethod": "YNA",
    #             "type": Poll.TYPE_NAMED,
    #             "onehundred_percent_base": "Y",
    #             "state": Poll.STATE_CREATED,
    #             "meeting_id": meeting_id,
    #             "option_ids": list(range(id_*2, 2)),
    #             "entitled_group_ids": group_ids,
    #             "min_votes_amount": 1,
    #             "max_votes_amount": 1,
    #             "max_votes_per_option": 1,
    #         },
    #         **{
    #             f"option/{option_id}":{"meeting_id": meeting_id, "poll_id": id_} for option_id in range(id_*2, 2)
    #         },
    #         meeting_fqid: {
    #             "poll_ids": [*meeting.get("poll_ids", []), id_],
    #         },
    #         content_object_id: {
    #             "poll_ids": [*content_object.get("poll_ids", []), id_],
    #         }
    #     })

    # def test_not_implemented_with_superadmin(self) -> None:
    #     user = self.assert_model_exists("user/2")
    #     user.pop("meta_position")
    #     response = self.request("user.merge_together", {"id": 2, "user_ids": []})
    #     self.assert_status_code(response, 200)
    #     self.assert_model_exists("user/2", user)

    def test_configuration_up_to_date(self) -> None:
        """
        This test checks, if the merge_together function has been properly
        updated to be able to handle the current data structure.
        If this test fails, it is likely because new fields have been added
        to the collections listed in the AssertionError without considering
        the necessary changes to the user merge.
        This can be fixed by editing the collection_field_groups in the
        action class if it is the 'user' collection,
        or else in the corresponding mixin class.
        """
        action = actions_map["user.merge_together"]
        merge_together = action(
            self.services,
            self.datastore,
            RelationManager(self.datastore),
            self.get_application().logging,
            self.env,
        )
        field_groups = merge_together._collection_field_groups  # type: ignore
        collection_fields = merge_together._all_collection_fields  # type: ignore
        broken = []
        for collection in collection_fields:
            if sorted(collection_fields[collection]) != sorted(
                field
                for group in field_groups[collection].values()
                for field in cast(Iterable[CollectionField], group)
                if field in collection_fields[collection]
            ):
                broken.append(collection)
        assert broken == []

    def test_empty_payload_fields(self) -> None:
        response = self.request("user.merge_together", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['id', 'user_ids'] properties",
            response.json["message"],
        )

    def test_correct_permission(self) -> None:
        user = self.assert_model_exists("user/1")
        user.pop("meta_position")
        self.user_id = self.create_user(
            "test",
            organization_management_level=OrganizationManagementLevel.CAN_MANAGE_USERS,
        )
        self.login(self.user_id)
        response = self.request("user.merge_together", {"id": 1, "user_ids": []})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", user)

    def test_missing_permission(self) -> None:
        self.user_id = self.create_user("test")
        self.login(self.user_id)
        response = self.request("user.merge_together", {"id": 1, "user_ids": []})
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.merge_together. Missing OrganizationManagementLevel: can_manage_users",
            response.json["message"],
        )

    def test_merge_into_self(self) -> None:
        response = self.request("user.merge_together", {"id": 1, "user_ids": [2]})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/1",
            {"meeting_ids": [1, 2], "meeting_user_ids": [46, 47], "committee_ids": [1]},
        )
        self.assert_model_deleted("user/2")

    def test_merge_self_into_other_error(self) -> None:
        response = self.request("user.merge_together", {"id": 2, "user_ids": [1]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Operator may not merge himself into others.",
            response.json["message"],
        )

    def test_merge_normal(self) -> None:
        password = self.assert_model_exists("user/2")["password"]
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3]})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "is_active": True,
                "username": "user2",
                "meeting_ids": [1, 2, 3],
                "committee_ids": [1, 2],
                "organization_id": 1,
                "default_password": "user2",
                "meeting_user_ids": [12, 22, 46],
                "password": password,
            },
        )
        self.assert_model_deleted("user/3")

    def test_merge_with_saml_id(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "password": None,
                    "saml_id": "user2",
                },
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "is_active": True,
                "username": "user2",
                "meeting_ids": [1, 2, 3],
                "committee_ids": [1, 2],
                "organization_id": 1,
                "default_password": "user2",
                "meeting_user_ids": [12, 22, 46],
                "password": None,
                "saml_id": "user2",
            },
        )
        self.assert_model_deleted("user/3")
        self.assert_model_deleted("user/4")

    def test_merge_with_saml_id_error(self) -> None:
        self.set_models(
            {
                "user/3": {
                    "password": None,
                    "saml_id": "user3",
                },
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Merge of user/2: Saml_id may not exist on any user except target.",
            response.json["message"],
        )

    def test_merge_with_user_fields(self) -> None:
        password = self.assert_model_exists("user/2")["password"]
        self.set_models(
            {
                "committee/1": {"manager_ids": [2, 5]},
                "committee/3": {"manager_ids": [5]},
                "meeting/2": {"present_user_ids": [4]},
                "meeting/3": {"present_user_ids": [3, 4]},
                "meeting/4": {"present_user_ids": [5]},
                "user/2": {
                    "organization_management_level": "can_manage_organization",
                    "pronoun": "he",
                    "first_name": "Nick",
                    "is_active": False,
                    "can_change_own_password": True,
                    "gender": "male",
                    "email": "nick.everything@rob.banks",
                    "last_email_sent": 123456789,
                    "committee_management_ids": [1],
                },
                "user/3": {
                    "organization_management_level": "can_manage_users",
                    "pronoun": "she",
                    "title": "Dr.",
                    "first_name": "Rob",
                    "last_name": "Banks",
                    "is_physical_person": True,
                    "default_vote_weight": "1.234567",
                    "last_login": 987654321,
                    "is_present_in_meeting_ids": [3],
                },
                "user/4": {
                    "organization_management_level": "superadmin",
                    "is_active": True,
                    "is_physical_person": False,
                    "gender": "female",
                    "last_email_sent": 234567890,
                    "is_present_in_meeting_ids": [2, 3],
                    "member_number": "souperadmin",
                },
                "user/5": {
                    "organization_management_level": "can_manage_users",
                    "pronoun": "it",
                    "title": "Prof. Dr. Dr.",
                    "last_name": "Everything",
                    "can_change_own_password": False,
                    "is_present_in_meeting_ids": [4],
                    "committee_management_ids": [1, 3],
                },
                "user/6": {
                    "email": "rob.banks@allof.them",
                },
            }
        )
        response = self.request(
            "user.merge_together", {"id": 2, "user_ids": [3, 4, 5, 6]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "organization_management_level": "superadmin",
                "is_active": True,
                "username": "user2",
                "meeting_ids": [1, 2, 3, 4],
                "committee_ids": [1, 2, 3],
                "organization_id": 1,
                "default_password": "user2",
                "meeting_user_ids": [12, 22, 46, 47],
                "password": password,
                "pronoun": "he",
                "title": "Dr.",
                "first_name": "Nick",
                "last_name": "Banks",
                "gender": "male",
                "email": "nick.everything@rob.banks",
                "default_vote_weight": "1.234567",
                "member_number": "souperadmin",
                "is_present_in_meeting_ids": [2, 3, 4],
                "committee_management_ids": [1, 3],
                "last_email_sent": 123456789,
            },
        )
        for id_ in range(3, 7):
            self.assert_model_deleted(f"user/{id_}")
        for id_ in [23, 33, 14, 24, 34, 15, 45]:
            self.assert_model_deleted(f"meeting_user/{id_}")
        for meeting_id, id_ in {1: 12, 2: 22, 3: 46, 4: 47}.items():
            self.assert_model_exists(
                f"meeting_user/{id_}", {"user_id": 2, "meeting_id": meeting_id}
            )
        self.assert_model_exists(
            "meeting/1", {"meeting_user_ids": [12], "user_ids": [2]}
        )
        self.assert_model_exists(
            "meeting/2",
            {"meeting_user_ids": [22], "user_ids": [2], "present_user_ids": [2]},
        )
        self.assert_model_exists(
            "meeting/3",
            {"meeting_user_ids": [46], "user_ids": [2], "present_user_ids": [2]},
        )
        self.assert_model_exists(
            "meeting/4",
            {"meeting_user_ids": [47], "user_ids": [2], "present_user_ids": [2]},
        )
        self.assert_model_exists("committee/1", {"user_ids": [2], "manager_ids": [2]})
        self.assert_model_exists("committee/2", {"user_ids": [2]})
        self.assert_model_exists("committee/3", {"user_ids": [2], "manager_ids": [2]})

    def test_merge_with_archived_meeting(self) -> None:
        self.set_models(
            {
                "organization/1": {
                    "active_meeting_ids": [2, 3, 4],
                    "archived_meeting_ids": [1],
                },
                "meeting/1": {
                    "is_active_in_organization_id": None,
                    "is_archived_in_organization_id": 1,
                },
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3]})
        self.assert_status_code(response, 400)
        self.assert_model_exists("user/2")
        self.assert_model_exists("user/3")

    def set_up_polls_for_merge(self) -> None:
        self.set_models(
            {
                "meeting/1": {
                    "present_user_ids": [2, 4],
                    "assignment_ids": [1],
                },
                "meeting/2": {
                    "present_user_ids": [3, 4],
                    "motion_ids": [1],
                    "motion_submitter_ids": [1],
                },
                "meeting/3": {
                    "present_user_ids": [2, 3, 4],
                    "topic_ids": [1],
                },
                "meeting/4": {"present_user_ids": [5]},
                "user/2": {
                    "is_present_in_meeting_ids": [1],
                },
                "user/3": {
                    "is_present_in_meeting_ids": [2, 3],
                },
                "user/4": {
                    "is_present_in_meeting_ids": [1, 2, 3],
                },
                "user/5": {
                    "is_present_in_meeting_ids": [4],
                },
                "meeting_user/15": {"vote_delegated_to_id": 14},
                "meeting_user/14": {"vote_delegations_from_ids": [15]},
                "meeting_user/23": {"motion_submitter_ids": [1]},
                "assignment/1": {
                    "id": 1,
                    "title": "Assignment 1",
                    "meeting_id": 1,
                },
                "motion/1": {
                    "id": 1,
                    "text": "XDDD",
                    "title": "Motion 1",
                    "state_id": 2,
                    "meeting_id": 2,
                    "submitter_ids": [1],
                },
                "motion_state/2": {"motion_ids": [1]},
                "motion_submitter/1": {
                    "id": 1,
                    "weight": 1,
                    "motion_id": 1,
                    "meeting_id": 2,
                    "meeting_user_id": 23,
                },
                "topic/1": {
                    "id": 1,
                    "title": "Topic 1",
                    "meeting_id": 3,
                },
            }
        )
        self.request_multi(
            "poll.create",
            [
                {
                    "title": "Assignment poll 1",
                    "content_object_id": "assignment/1",
                    "type": "named",
                    "pollmethod": "Y",
                    "meeting_id": 1,
                    "options": [
                        {"content_object_id": "user/2"},
                        {"content_object_id": "user/5"},
                    ],
                    "global_no": True,
                    "min_votes_amount": 1,
                    "max_votes_amount": 2,
                    "max_votes_per_option": 1,
                    "backend": "long",
                    "entitled_group_ids": [1, 2, 3],
                },
                {
                    "title": "Assignment poll 2",
                    "content_object_id": "assignment/1",
                    "type": "named",
                    "pollmethod": "YN",
                    "meeting_id": 1,
                    "options": [
                        {"poll_candidate_user_ids": [5, 4]},
                    ],
                    "min_votes_amount": 1,
                    "max_votes_amount": 1,
                    "max_votes_per_option": 1,
                    "backend": "fast",
                    "entitled_group_ids": [1, 2, 3],
                },
                {
                    "title": "Assignment poll 3",
                    "content_object_id": "assignment/1",
                    "type": "named",
                    "pollmethod": "YN",
                    "meeting_id": 1,
                    "options": [
                        {"poll_candidate_user_ids": [2, 5]},
                    ],
                    "min_votes_amount": 1,
                    "max_votes_amount": 1,
                    "max_votes_per_option": 1,
                    "backend": "fast",
                    "entitled_group_ids": [1, 2, 3],
                },
                {
                    "title": "Assignment poll 4",
                    "content_object_id": "assignment/1",
                    "type": "pseudoanonymous",
                    "pollmethod": "Y",
                    "meeting_id": 1,
                    "options": [
                        {"content_object_id": "user/4"},
                        {"content_object_id": "user/5"},
                    ],
                    "min_votes_amount": 1,
                    "max_votes_amount": 2,
                    "max_votes_per_option": 1,
                    "backend": "long",
                    "entitled_group_ids": [1, 2, 3],
                },
                {
                    "title": "Motion poll",
                    "content_object_id": "motion/1",
                    "type": "named",
                    "pollmethod": "YNA",
                    "meeting_id": 2,
                    "options": [
                        {"content_object_id": "motion/1"},
                    ],
                    "min_votes_amount": 1,
                    "max_votes_amount": 1,
                    "max_votes_per_option": 1,
                    "backend": "fast",
                    "entitled_group_ids": [4, 5, 6],
                },
                {
                    "title": "Topic poll",
                    "content_object_id": "topic/1",
                    "type": "pseudoanonymous",
                    "pollmethod": "Y",
                    "meeting_id": 3,
                    "options": [
                        {"text": "Option 1"},
                        {"text": "Option 2"},
                        {"text": "Option 3"},
                    ],
                    "min_votes_amount": 1,
                    "max_votes_amount": 3,
                    "max_votes_per_option": 1,
                    "backend": "fast",
                    "entitled_group_ids": [7, 8, 9],
                },
            ],
        )

    def create_polls_with_correct_votes(self) -> None:
        self.set_up_polls_for_merge()
        self.request_multi("poll.start", [{"id": i} for i in range(1, 7)])
        self.login(4)
        self.request("poll.vote", {"id": 1, "value": "N"}, stop_poll_after_vote=False)
        self.request(
            "poll.vote",
            {"id": 1, "value": "N", "user_id": 5},
            start_poll_before_vote=False,
        )
        self.login(2)
        self.request("poll.vote", {"id": 2, "value": {"4": "Y"}})
        self.login(3)
        self.request("poll.vote", {"id": 5, "value": {"11": "A"}})
        self.request("poll.vote", {"id": 6, "value": {"13": 1, "14": 1, "15": 0}})
        self.login(1)
        self.request_multi("poll.stop", [{"id": i} for i in [3, 4]])

    def assert_merge_with_polls_correct(
        self, password: str, add_to_creatable_ids: int = 0
    ) -> None:
        self.assert_model_exists(
            "user/2",
            {
                "is_active": True,
                "username": "user2",
                "meeting_ids": [1, 2, 3],
                "committee_ids": [1, 2],
                "organization_id": 1,
                "default_password": "user2",
                "meeting_user_ids": [12, 22, 46 + add_to_creatable_ids],
                "password": password,
                "is_present_in_meeting_ids": [1, 2, 3],
                "poll_candidate_ids": [2, 3],
                "option_ids": [1, 8],
                "poll_voted_ids": [1, 2, 5, 6],
                "vote_ids": [1, 3, 4],
                "delegated_vote_ids": [1, 2, 3, 4],
            },
        )
        self.assert_model_exists("committee/1", {"user_ids": [2, 5]})
        self.assert_model_exists("committee/2", {"user_ids": [2]})
        for id_ in range(3, 5):
            self.assert_model_deleted(f"user/{id_}")
        for id_ in [23, 33, 14, 24, 34, *range(46, 46 + add_to_creatable_ids)]:
            self.assert_model_deleted(f"meeting_user/{id_}")
        for meeting_id, id_ in {1: 12, 2: 22, 3: 46 + add_to_creatable_ids}.items():
            self.assert_model_exists(
                f"meeting_user/{id_}", {"user_id": 2, "meeting_id": meeting_id}
            )
        self.assert_model_exists(
            "meeting_user/22",
            {"user_id": 2, "meeting_id": 2, "motion_submitter_ids": [2]},
        )
        self.assert_model_deleted("motion_submitter/1")
        self.assert_model_exists(
            "motion_submitter/2",
            {"motion_id": 1, "meeting_user_id": 22, "meeting_id": 2, "weight": 1},
        )
        self.assert_model_exists("poll_candidate/2", {"user_id": 2})
        self.assert_model_exists("poll_candidate/3", {"user_id": 2})
        self.assert_model_exists("vote/2", {"user_id": 5, "delegated_user_id": 2})
        for id_ in [1, 3, 4]:
            self.assert_model_exists(
                f"vote/{id_}", {"user_id": 2, "delegated_user_id": 2}
            )
        for id_ in [5, 6]:  # pseudoanonymous options
            self.assert_model_exists(
                f"vote/{id_}",
                {"option_id": id_ + 8, "user_id": None, "delegated_user_id": None},
            )
        self.assert_model_exists("option/1", {"content_object_id": "user/2"})
        self.assert_model_exists("option/8", {"content_object_id": "user/2"})

        def build_expected_user_dates(
            voted_present_user_delegated_merged: list[
                tuple[bool, bool, int, int | None, int | None, int | None]
            ]
        ) -> list[dict[str, Any]]:
            return [
                {
                    "voted": date[0],
                    "present": date[1],
                    "user_id": date[2],
                    "vote_delegated_to_user_id": date[3],
                    **({"user_merged_into_id": date[4]} if date[4] else {}),
                    **({"delegation_user_merged_into_id": date[5]} if date[5] else {}),
                }
                for date in voted_present_user_delegated_merged
            ]

        self.assert_model_exists(
            "poll/1",
            {
                "voted_ids": [5, 2],
                "entitled_users_at_stop": build_expected_user_dates(
                    [
                        (False, True, 2, None, None, None),
                        (True, True, 4, None, 2, None),
                        (True, False, 5, 4, None, 2),
                    ]
                ),
            },
        )
        self.assert_model_exists(
            "poll/2",
            {
                "voted_ids": [2],
                "entitled_users_at_stop": build_expected_user_dates(
                    [
                        (True, True, 2, None, None, None),
                        (False, True, 4, None, 2, None),
                        (False, False, 5, 4, None, 2),
                    ]
                ),
            },
        )
        for id_ in [3, 4]:
            self.assert_model_exists(
                f"poll/{id_}",
                {
                    "voted_ids": [],
                    "entitled_users_at_stop": build_expected_user_dates(
                        [
                            (False, True, 2, None, None, None),
                            (False, True, 4, None, 2, None),
                            (False, False, 5, 4, None, 2),
                        ]
                    ),
                },
            )
        self.assert_model_exists(
            "poll/5",
            {
                "voted_ids": [2],
                "entitled_users_at_stop": build_expected_user_dates(
                    [
                        (False, True, 4, None, 2, None),
                        (False, False, 2, None, None, None),
                        (True, True, 3, None, 2, None),
                    ]
                ),
            },
        )
        self.assert_model_exists(
            "poll/6",
            {
                "voted_ids": [2],
                "entitled_users_at_stop": build_expected_user_dates(
                    [(True, True, 3, None, 2, None), (False, True, 4, None, 2, None)]
                ),
            },
        )

    def test_merge_with_polls_correct(self) -> None:
        password = self.assert_model_exists("user/2")["password"]
        self.create_polls_with_correct_votes()
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)
        self.assert_merge_with_polls_correct(password)

    def test_polls_with_subsequent_merges(self) -> None:
        password = self.assert_model_exists("user/2")["password"]
        self.create_polls_with_correct_votes()
        response = self.request("user.merge_together", {"id": 3, "user_ids": [4]})
        self.assert_status_code(response, 200)
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3]})
        self.assert_status_code(response, 200)
        self.assert_merge_with_polls_correct(password, 1)

    def test_merge_with_polls_all_errors(self) -> None:
        self.set_up_polls_for_merge()
        self.request_multi("poll.start", [{"id": i} for i in range(1, 7)])
        self.login(4)
        self.request("poll.vote", {"id": 1, "value": "N"}, stop_poll_after_vote=False)
        self.request(
            "poll.vote",
            {"id": 1, "value": "N", "user_id": 5},
            start_poll_before_vote=False,
        )
        self.login(2)
        self.request("poll.vote", {"id": 2, "value": {"4": "Y"}})
        self.login(3)
        self.request("poll.vote", {"id": 5, "value": {"11": "A"}})
        self.request("poll.vote", {"id": 6, "value": {"13": 1, "14": 1, "15": 0}})
        self.login(1)
        self.request("poll.stop", {"id": 3})
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4, 5]})
        self.assert_status_code(response, 400)
        assert (
            "Cannot carry out merge into user/2, because "
            + " and ".join(
                [
                    "some of the users are entitled to vote in currently running polls in meeting(s) 1",
                    "some of the selected users have different delegations roles in meeting(s) 1",
                    "some of the selected users are delegating votes to each other in meeting(s) 1",
                    "among the selected users multiple voted in poll(s) 1",
                    "multiple of the selected users are among the options in poll(s) 1, 4",
                    "multiple of the selected users are in the same candidate list in poll(s) 2, 3",
                ]
            )
            in response.json["message"]
        )

    def add_assignment_or_motion_models_for_meetings(
        self,
        data: dict[str, Any],
        collection: Literal["assignment", "motion"],
        sub_collection: str,
        back_relation: str,
        meeting_user_id_lists_per_meeting_id: dict[int, list[list[int]]],
    ) -> None:
        next_model_id = 1
        next_sub_model_id = 1
        for (
            meeting_id,
            meeting_user_id_lists,
        ) in meeting_user_id_lists_per_meeting_id.items():
            sub_models_per_meeting_user_id: dict[int, list[int]] = {
                meeting_user_id: []
                for li in meeting_user_id_lists
                for meeting_user_id in li
            }
            if (
                meeting_fqid := fqid_from_collection_and_id("meeting", meeting_id)
            ) not in data:
                data[meeting_fqid] = {}
            data[meeting_fqid][collection + "_ids"] = list(
                range(
                    next_model_id,
                    next_model_id + len(meeting_user_id_lists),
                )
            )
            data[meeting_fqid][sub_collection + "_ids"] = list(
                range(
                    next_sub_model_id,
                    next_sub_model_id + sum([len(li) for li in meeting_user_id_lists]),
                )
            )
            for meeting_user_id_list in meeting_user_id_lists:
                data[fqid_from_collection_and_id(collection, next_model_id)] = {
                    "title": f"{collection} {next_model_id}",
                    "meeting_id": meeting_id,
                    back_relation: list(
                        range(
                            next_sub_model_id,
                            next_sub_model_id + len(meeting_user_id_list),
                        )
                    ),
                }
                weight = 1
                for meeting_user_id in meeting_user_id_list:
                    data[
                        fqid_from_collection_and_id(sub_collection, next_sub_model_id)
                    ] = {
                        "weight": weight,
                        collection + "_id": next_model_id,
                        "meeting_user_id": meeting_user_id,
                        "meeting_id": meeting_id,
                    }
                    sub_models_per_meeting_user_id[meeting_user_id].append(
                        next_sub_model_id
                    )
                    next_sub_model_id += 1
                    weight += 1
                next_model_id += 1
            for (
                meeting_user_id,
                sub_model_ids,
            ) in sub_models_per_meeting_user_id.items():
                if (
                    meeting_user_fqid := fqid_from_collection_and_id(
                        "meeting_user", meeting_user_id
                    )
                ) not in data:
                    data[meeting_user_fqid] = {}
                data[meeting_user_fqid][sub_collection + "_ids"] = sub_model_ids

    def assert_assignment_or_motion_model_test_was_correct(
        self,
        collection: Literal["assignment", "motion"],
        sub_collection: str,
        back_relation: str,
        expected: dict[int, dict[int, tuple[int, int, int] | None]],
    ) -> None:
        """
        expected needs to have the following format:
        {
            meeting_id: {
                sub_model_id: (model_id, meeting_user_id, weight) | None
            }
        }

        wherein None is used instead of the data tuple if the model is
        supposed to have been deleteded
        """
        for meeting_id, expected_sub_models in expected.items():
            self.assert_model_exists(
                f"meeting/{meeting_id}",
                {
                    sub_collection
                    + "_ids": [
                        id_
                        for id_, sub_model in expected_sub_models.items()
                        if sub_model is not None
                    ]
                },
            )
            sub_model_ids_by_collection_id: dict[str, dict[int, list[int]]] = {
                collection: {},
                "meeting_user": {},
            }
            for sub_model_id, sub_model in expected_sub_models.items():
                sub_model_fqid = fqid_from_collection_and_id(
                    sub_collection, sub_model_id
                )
                if sub_model is None:
                    self.assert_model_deleted(sub_model_fqid)
                else:
                    model_id = sub_model[0]
                    meeting_user_id = sub_model[1]
                    self.assert_model_exists(
                        sub_model_fqid,
                        {
                            "meeting_id": meeting_id,
                            collection + "_id": model_id,
                            "meeting_user_id": meeting_user_id,
                            "weight": sub_model[2],
                        },
                    )
                    for coll, value in [
                        (collection, model_id),
                        ("meeting_user", meeting_user_id),
                    ]:
                        if value not in sub_model_ids_by_collection_id[coll]:
                            sub_model_ids_by_collection_id[coll][value] = []
                        sub_model_ids_by_collection_id[coll][value].append(sub_model_id)
            for coll, field in [
                (collection, back_relation),
                ("meeting_user", sub_collection + "_ids"),
            ]:
                for id_, values in sub_model_ids_by_collection_id[coll].items():
                    model = self.assert_model_exists(
                        fqid_from_collection_and_id(coll, id_)
                    )
                    assert sorted(model[field]) == sorted(values)

    def base_assignment_or_motion_model_test(
        self,
        collection: Literal["assignment", "motion"],
        sub_collection: str,
    ) -> None:
        back_relation = "_".join(sub_collection.split("_")[1:]) + "_ids"
        data: dict[str, Any] = {}
        self.add_assignment_or_motion_models_for_meetings(
            data,
            collection,
            sub_collection,
            back_relation,
            {
                1: [
                    [12, 15],
                    [15, 14],
                    [14, 12],
                    [12, 14, 15],
                    [14, 12, 15],
                    [15, 14, 12],
                ],
                2: [[24, 22, 23]],
                3: [[34], [33]],
                4: [[45]],
            },
        )
        self.set_models(data)
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)
        expected: dict[int, dict[int, tuple[int, int, int] | None]] = {
            # meeting_id:sub_model_id:(model_id, meeting_user_id, weight) | None if deleted
            1: {
                1: (1, 12, 1),
                2: (1, 15, 2),
                3: (2, 15, 1),
                4: (2, 12, 2),
                5: None,
                6: (3, 12, 1),
                7: (4, 12, 1),
                8: None,
                9: (4, 15, 3),
                10: None,
                11: (5, 12, 1),
                12: (5, 15, 3),
                13: (6, 15, 1),
                14: None,
                15: (6, 12, 2),
            },
            2: {
                16: None,
                17: (7, 22, 1),
                18: None,
            },
            3: {
                19: (8, 46, 1),
                20: (9, 46, 1),
            },
            4: {
                21: (10, 45, 1),
            },
        }
        self.assert_assignment_or_motion_model_test_was_correct(
            collection, sub_collection, back_relation, expected
        )

    def test_with_assignment_candidates(self) -> None:
        self.base_assignment_or_motion_model_test("assignment", "assignment_candidate")

    def test_with_motion_working_group_speakers(self) -> None:
        self.base_assignment_or_motion_model_test(
            "motion", "motion_working_group_speaker"
        )

    def test_with_motion_editor(self) -> None:
        self.base_assignment_or_motion_model_test("motion", "motion_editor")

    def test_with_motion_submitters(
        self,
    ) -> None:
        data: dict[str, Any] = {}
        self.add_assignment_or_motion_models_for_meetings(
            data,
            "motion",
            "motion_submitter",
            "submitter_ids",
            {
                1: [
                    [12, 15],
                    [15, 14],
                    [14, 12],
                    [12, 14, 15],
                    [14, 12, 15],
                    [15, 14, 12],
                ],
                2: [[24, 22, 23]],
                3: [[34], [33]],
                4: [[45]],
            },
        )
        self.set_models(data)
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)
        expected: dict[int, dict[int, tuple[int, int, int] | None]] = {
            # meeting_id:sub_model_id:(model_id, meeting_user_id, weight) | None if deleted
            1: {
                1: (1, 12, 1),
                2: (1, 15, 2),
                3: (2, 15, 1),
                4: None,
                5: None,
                6: (3, 12, 1),
                7: (4, 12, 1),
                8: None,
                9: (4, 15, 3),
                10: None,
                11: (5, 12, 1),
                12: (5, 15, 3),
                13: (6, 15, 1),
                14: None,
                15: (6, 12, 2),
                22: (2, 12, 2),  # created to replace 4
            },
            2: {
                16: None,
                17: (7, 22, 1),
                18: None,
            },
            3: {
                19: None,
                20: None,
                23: (9, 46, 1),  # created to replace 20
                24: (8, 46, 1),  # created to replace 19
            },
            4: {
                21: (10, 45, 1),
            },
        }
        self.assert_assignment_or_motion_model_test_was_correct(
            "motion", "motion_submitter", "submitter_ids", expected
        )
