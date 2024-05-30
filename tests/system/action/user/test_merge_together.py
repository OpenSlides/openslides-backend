from collections.abc import Iterable
from typing import cast

from openslides_backend.action.relations.relation_manager import RelationManager
from openslides_backend.action.util.actions_map import actions_map
from openslides_backend.models.mixins import DEFAULT_PROJECTOR_OPTIONS
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.patterns import (
    CollectionField,
    fqid_from_collection_and_id,
)
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase

# TODO:
# Test merge on poll_candidates
# Test error when trying to merge users who are on the same candidate list
# Test merging and deep merging of assignment_candidates, motion_submitters,
#   personal_notes, motion_editors and motion_working_group_speakers
# Check all possible poll related errors (check_poll) method


class UserMergeTogether(BaseActionTestCase):
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
                }
                for user_id in range(2, num_users + 2)
                for meeting_id in range(1, num_meetings + 1)
                if user_id in user_ids_by_meeting_id[meeting_id]
            },
        }
        self.set_models(data)

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
