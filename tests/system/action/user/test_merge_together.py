from collections.abc import Iterable
from typing import Any, Literal, cast

import pytest

from openslides_backend.action.actions.speaker.speech_state import SpeechState
from openslides_backend.action.relations.relation_manager import RelationManager
from openslides_backend.action.util.actions_map import actions_map
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.patterns import (
    CollectionField,
    fqid_from_collection_and_id,
)
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase
from tests.system.action.poll.test_vote import BaseVoteTestCase


class UserMergeTogether(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        models = {
            "user/2": {
                "username": "user2",
                "is_active": True,
                "default_password": "user2",
                "password": self.auth.hash("user2"),
                "meeting_ids": [1, 2],
                "meeting_user_ids": [12, 22],
                "committee_ids": [1],
                "organization_id": 1,
            },
            "user/3": {
                "username": "user3",
                "is_active": True,
                "default_password": "user3",
                "password": self.auth.hash("user3"),
                "meeting_ids": [2, 3],
                "meeting_user_ids": [23, 33],
                "committee_ids": [1, 2],
                "organization_id": 1,
            },
            "user/4": {
                "username": "user4",
                "is_active": True,
                "default_password": "user4",
                "password": self.auth.hash("user4"),
                "meeting_ids": [1, 2, 3],
                "meeting_user_ids": [14, 24, 34],
                "committee_ids": [1, 2],
                "organization_id": 1,
            },
            "user/5": {
                "username": "user5",
                "is_active": True,
                "default_password": "user5",
                "password": self.auth.hash("user5"),
                "meeting_ids": [1, 4],
                "meeting_user_ids": [15, 45],
                "committee_ids": [1, 3],
                "organization_id": 1,
            },
            "user/6": {
                "username": "user6",
                "is_active": True,
                "default_password": "user6",
                "password": self.auth.hash("user6"),
                "meeting_ids": [],
                "meeting_user_ids": [],
                "committee_ids": [],
                "organization_id": 1,
            },
            "organization/1": {
                "limit_of_meetings": 0,
                "active_meeting_ids": [1, 2, 3, 4],
                "enable_electronic_voting": True,
                "committee_ids": [1, 2, 3],
                "user_ids": [2, 3, 4, 5, 6],
                "genders": ["male", "female", "diverse", "non-binary"],
            },
            "committee/1": {
                "organization_id": 1,
                "name": "Committee 1",
                "meeting_ids": [1, 2],
                "user_ids": [2, 3, 4, 5],
            },
            "meeting/1": {
                "name": "Meeting 1",
                "is_active_in_organization_id": 1,
                "language": "en",
                "motions_default_workflow_id": 1,
                "motions_default_amendment_workflow_id": 1,
                "motions_default_statute_amendment_workflow_id": 1,
                "users_enable_vote_delegations": True,
                "committee_id": 1,
                "group_ids": [1, 2, 3],
                "admin_group_id": 1,
                "meeting_user_ids": [12, 14, 15],
                "user_ids": [2, 4, 5],
            },
            "group/1": {
                "meeting_id": 1,
                "name": "Group 1",
                "admin_group_for_meeting_id": 1,
                "default_group_for_meeting_id": None,
                "meeting_user_ids": [12],
            },
            "group/2": {
                "meeting_id": 1,
                "name": "Group 2",
                "admin_group_for_meeting_id": None,
                "default_group_for_meeting_id": None,
                "meeting_user_ids": [12, 14, 15],
            },
            "group/3": {
                "meeting_id": 1,
                "name": "Group 3",
                "admin_group_for_meeting_id": None,
                "default_group_for_meeting_id": 1,
                "meeting_user_ids": [],
            },
            "meeting_user/12": {
                "user_id": 2,
                "meeting_id": 1,
                "group_ids": [1, 2],
                "vote_weight": "1.000000",
            },
            "meeting_user/14": {
                "user_id": 4,
                "meeting_id": 1,
                "group_ids": [2],
                "vote_weight": "1.000000",
            },
            "meeting_user/15": {
                "user_id": 5,
                "meeting_id": 1,
                "group_ids": [2],
                "vote_weight": "1.000000",
            },
            "meeting/2": {
                "name": "Meeting 2",
                "is_active_in_organization_id": 1,
                "language": "en",
                "motions_default_workflow_id": 2,
                "motions_default_amendment_workflow_id": 2,
                "motions_default_statute_amendment_workflow_id": 2,
                "users_enable_vote_delegations": True,
                "committee_id": 1,
                "group_ids": [4, 5, 6],
                "admin_group_id": 4,
                "meeting_user_ids": [22, 23, 24],
                "user_ids": [2, 3, 4],
            },
            "group/4": {
                "meeting_id": 2,
                "name": "Group 4",
                "admin_group_for_meeting_id": 2,
                "default_group_for_meeting_id": None,
                "meeting_user_ids": [24],
            },
            "group/5": {
                "meeting_id": 2,
                "name": "Group 5",
                "admin_group_for_meeting_id": None,
                "default_group_for_meeting_id": None,
                "meeting_user_ids": [22, 23],
            },
            "group/6": {
                "meeting_id": 2,
                "name": "Group 6",
                "admin_group_for_meeting_id": None,
                "default_group_for_meeting_id": 2,
                "meeting_user_ids": [],
            },
            "meeting_user/22": {
                "user_id": 2,
                "meeting_id": 2,
                "group_ids": [5],
                "vote_weight": "1.000000",
            },
            "meeting_user/23": {
                "user_id": 3,
                "meeting_id": 2,
                "group_ids": [5],
                "vote_weight": "1.000000",
            },
            "meeting_user/24": {
                "user_id": 4,
                "meeting_id": 2,
                "group_ids": [4],
                "vote_weight": "1.000000",
            },
            "committee/2": {
                "organization_id": 1,
                "name": "Committee 2",
                "meeting_ids": [3],
                "user_ids": [3, 4],
            },
            "meeting/3": {
                "name": "Meeting 3",
                "is_active_in_organization_id": 1,
                "language": "en",
                "motions_default_workflow_id": 3,
                "motions_default_amendment_workflow_id": 3,
                "motions_default_statute_amendment_workflow_id": 3,
                "users_enable_vote_delegations": True,
                "committee_id": 2,
                "group_ids": [7, 8, 9],
                "admin_group_id": 7,
                "meeting_user_ids": [33, 34],
                "user_ids": [3, 4],
            },
            "group/7": {
                "meeting_id": 3,
                "name": "Group 7",
                "admin_group_for_meeting_id": 3,
                "default_group_for_meeting_id": None,
                "meeting_user_ids": [],
            },
            "group/8": {
                "meeting_id": 3,
                "name": "Group 8",
                "admin_group_for_meeting_id": None,
                "default_group_for_meeting_id": None,
                "meeting_user_ids": [33],
            },
            "group/9": {
                "meeting_id": 3,
                "name": "Group 9",
                "admin_group_for_meeting_id": None,
                "default_group_for_meeting_id": 3,
                "meeting_user_ids": [34],
            },
            "meeting_user/33": {
                "user_id": 3,
                "meeting_id": 3,
                "group_ids": [8],
                "vote_weight": "1.000000",
            },
            "meeting_user/34": {
                "user_id": 4,
                "meeting_id": 3,
                "group_ids": [9],
                "vote_weight": "1.000000",
            },
            "committee/3": {
                "organization_id": 1,
                "name": "Committee 3",
                "meeting_ids": [4],
                "user_ids": [5],
            },
            "meeting/4": {
                "name": "Meeting 4",
                "is_active_in_organization_id": 1,
                "language": "en",
                "motions_default_workflow_id": 4,
                "motions_default_amendment_workflow_id": 4,
                "motions_default_statute_amendment_workflow_id": 4,
                "users_enable_vote_delegations": True,
                "committee_id": 3,
                "group_ids": [10, 11, 12],
                "admin_group_id": 10,
                "meeting_user_ids": [45],
                "user_ids": [5],
            },
            "group/10": {
                "meeting_id": 4,
                "name": "Group 10",
                "admin_group_for_meeting_id": 4,
                "default_group_for_meeting_id": None,
                "meeting_user_ids": [45],
            },
            "group/11": {
                "meeting_id": 4,
                "name": "Group 11",
                "admin_group_for_meeting_id": None,
                "default_group_for_meeting_id": None,
                "meeting_user_ids": [],
            },
            "group/12": {
                "meeting_id": 4,
                "name": "Group 12",
                "admin_group_for_meeting_id": None,
                "default_group_for_meeting_id": 4,
                "meeting_user_ids": [],
            },
            "meeting_user/45": {
                "user_id": 5,
                "meeting_id": 4,
                "group_ids": [10],
                "vote_weight": "1.000000",
            },
            **{
                fqid_from_collection_and_id("motion_workflow", id_): {
                    "name": f"Workflow {id_}",
                    "sequential_number": 1,
                    "state_ids": [id_],
                    "first_state_id": id_,
                    "meeting_id": id_,
                }
                for id_ in range(1, 5)
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
                for id_ in range(1, 5)
            },
        }
        self.set_models(models)

    def test_merge_configuration_up_to_date(self) -> None:
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
            if set(collection_fields[collection]) != {
                field
                for group in field_groups[collection].values()
                for field in cast(Iterable[CollectionField], group)
            }:
                broken.append(collection)
        assert broken == []

    def test_merge_empty_payload_fields(self) -> None:
        response = self.request("user.merge_together", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['id', 'user_ids'] properties",
            response.json["message"],
        )

    def test_merge_correct_permission(self) -> None:
        user = self.assert_model_exists("user/1")
        user.pop("meta_position")
        self.user_id = self.create_user(
            "test",
            organization_management_level=OrganizationManagementLevel.CAN_MANAGE_USERS,
        )
        id2 = self.create_user("test2")
        self.login(self.user_id)
        response = self.request("user.merge_together", {"id": id2, "user_ids": []})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/1", user)

    def test_merge_missing_permission(self) -> None:
        self.user_id = self.create_user("test")
        id2 = self.create_user("test2")
        self.login(self.user_id)
        response = self.request("user.merge_together", {"id": id2, "user_ids": []})
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

    def test_merge_is_demo_user_error(self) -> None:
        self.set_models({"user/2": {"is_demo_user": True}})
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot merge user models that have is_demo_user set: Problem in user/2",
            response.json["message"],
        )

    def test_merge_forwarding_committee_ids_error(self) -> None:
        self.set_models(
            {
                "committee/3": {"forwarding_user_id": 3},
                "user/3": {"forwarding_committee_ids": [3]},
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot merge user models that have forwarding_committee_ids set: Problem in user/3",
            response.json["message"],
        )

    def test_merge_saml_id_error(self) -> None:
        self.set_models({"user/3": {"saml_id": "SAML"}})
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Merge of user/2: Saml_id may not exist on any user except target.",
            response.json["message"],
        )

    def test_merge_saml_id_no_error(self) -> None:
        self.set_models({"user/2": {"saml_id": "SAML"}})
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)

    def test_merge_member_number_error(self) -> None:
        self.set_models(
            {
                "user/2": {"member_number": "MEMNUM"},
                "user/3": {"member_number": "M3MNUM"},
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Differing values in field member_number when merging into user/2",
            response.json["message"],
        )

    def setup_complex_user_fields(self) -> None:
        self.set_models(
            {
                "committee/1": {"manager_ids": [2, 5]},
                "committee/3": {"manager_ids": [5]},
                "meeting/2": {"present_user_ids": [4], "locked_from_inside": True},
                "meeting/3": {"present_user_ids": [3, 4]},
                "meeting/4": {"present_user_ids": [5]},
                "user/2": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
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
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
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
                    "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                    "is_active": True,
                    "is_physical_person": False,
                    "gender": "female",
                    "last_email_sent": 234567890,
                    "is_present_in_meeting_ids": [2, 3],
                    "member_number": "souperadmin",
                },
                "user/5": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
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
                "meeting_user/12": {
                    "about_me": "I am an enthusiastic explorer",
                    "comment": "Nicks everything",
                },
                "meeting_user/14": {"number": "NOMNOM", "comment": "Likes soup"},
                "meeting_user/15": {
                    "about_me": "I am a raging lunatic",
                    "number": "NomDiNom",
                },
                "meeting_user/22": {
                    "number": "num?",
                    "vote_weight": "2.000000",
                },
                "meeting_user/23": {
                    "comment": "Comment 1",
                    "vote_weight": "3.000000",
                },
                "meeting_user/24": {
                    "number": "NOM!",
                    "comment": "Comment 2: Electric Boogaloo",
                },
                "meeting_user/33": {
                    "about_me": "I have a long beard",
                    "vote_weight": "1.234567",
                },
                "meeting_user/34": {
                    "about_me": "I am hairy",
                    "vote_weight": "1.000001",
                },
                "meeting_user/45": {
                    "comment": "This is a comment",
                },
            }
        )

    def test_merge_with_user_fields(self) -> None:
        password = self.assert_model_exists("user/2")["password"]
        self.setup_complex_user_fields()
        response = self.request(
            "user.merge_together", {"id": 2, "user_ids": [3, 4, 5, 6]}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                "username": "user2",
                "meeting_ids": [1, 2, 3, 4],
                "committee_ids": [1, 2, 3],
                "organization_id": 1,
                "default_password": "user2",
                "meeting_user_ids": [12, 22, 46, 47],
                "password": password,
                "pronoun": "he",
                "first_name": "Nick",
                "is_active": False,
                "can_change_own_password": True,
                "gender": "male",
                "email": "nick.everything@rob.banks",
                "is_present_in_meeting_ids": [3, 4],
                "committee_management_ids": [1, 3],
                "last_email_sent": 123456789,
                "title": None,
                "last_name": None,
                "default_vote_weight": None,
                "member_number": None,
                "is_physical_person": None,
            },
        )
        for id_ in range(3, 7):
            self.assert_model_deleted(f"user/{id_}")
        for id_ in [23, 33, 14, 24, 34, 15, 45]:
            self.assert_model_deleted(f"meeting_user/{id_}")

        self.assert_model_exists(
            "meeting_user/12",
            {
                "user_id": 2,
                "meeting_id": 1,
                "about_me": "I am an enthusiastic explorer",
                "comment": "Nicks everything",
                "number": "NOMNOM",
            },
        )
        self.assert_model_exists(
            "meeting_user/22",
            {
                "user_id": 2,
                "meeting_id": 2,
                "number": "num?",
                "vote_weight": "2.000000",
                "comment": "Comment 1",
            },
        )
        self.assert_model_exists(
            "meeting_user/46",
            {
                "user_id": 2,
                "meeting_id": 3,
                "about_me": "I have a long beard",
                "vote_weight": "1.234567",
            },
        )
        self.assert_model_exists(
            "meeting_user/47",
            {
                "user_id": 2,
                "meeting_id": 4,
                "comment": "This is a comment",
            },
        )

        self.assert_model_exists(
            "meeting/1", {"meeting_user_ids": [12], "user_ids": [2]}
        )
        self.assert_model_exists(
            "meeting/2",
            {"meeting_user_ids": [22], "user_ids": [2]},
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

        self.assert_history_information(
            "user/2",
            [
                "Updated with data from {}, {}, {} and {}",
                *[f"user/{id_}" for id_ in range(3, 7)],
            ],
        )
        for id_ in range(3, 7):
            self.assert_history_information(f"user/{id_}", ["Merged into {}", "user/2"])

    def test_merge_forbid_merging_of_higher_level_users(self) -> None:
        self.setup_complex_user_fields()
        self.set_organization_management_level(
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
        )
        response = self.request(
            "user.merge_together", {"id": 2, "user_ids": [3, 4, 5, 6]}
        )
        self.assert_status_code(response, 403)
        self.assertIn(
            "You are not allowed to perform action user.merge_together. Missing OrganizationManagementLevel: superadmin",
            response.json["message"],
        )

    def test_with_custom_fields_complex(self) -> None:
        self.setup_complex_user_fields()
        response = self.request(
            "user.merge_together",
            {
                "id": 2,
                "user_ids": [3, 4, 5, 6],
                "username": "This",
                "title": "is",
                "first_name": "completely",
                "last_name": "new data",
                "pronoun": "for",
                "member_number": "this",
                "default_password": "now",
                "gender": "female",
                "email": "user.in@this.organization",
                "is_active": False,
                "is_physical_person": None,
                "default_vote_weight": "0.424242",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "This",
                "title": "is",
                "first_name": "completely",
                "last_name": "new data",
                "pronoun": "for",
                "member_number": "this",
                "default_password": "now",
                "gender": "female",
                "email": "user.in@this.organization",
                "is_active": False,
                "is_physical_person": None,
                "default_vote_weight": "0.424242",
            },
        )

    def test_with_custom_fields_simple(self) -> None:
        response = self.request(
            "user.merge_together",
            {
                "id": 2,
                "user_ids": [3, 4, 5, 6],
                "username": "This",
                "title": "is",
                "first_name": "completely",
                "last_name": "new data",
                "pronoun": "for",
                "member_number": "this",
                "default_password": "now",
                "gender": "female",
                "email": "user.in@this.organization",
                "is_active": False,
                "is_physical_person": None,
                "default_vote_weight": "0.424242",
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "username": "This",
                "title": "is",
                "first_name": "completely",
                "last_name": "new data",
                "pronoun": "for",
                "member_number": "this",
                "default_password": "now",
                "gender": "female",
                "email": "user.in@this.organization",
                "is_active": False,
                "is_physical_person": None,
                "default_vote_weight": "0.424242",
            },
        )

    def test_with_multiple_delegations(self) -> None:
        self.set_models(
            {
                "meeting_user/15": {"vote_delegated_to_id": 14},
                "meeting_user/14": {"vote_delegations_from_ids": [15]},
                "meeting_user/23": {"vote_delegated_to_id": 24},
                "meeting_user/24": {"vote_delegations_from_ids": [23]},
                "meeting_user/33": {"vote_delegations_from_ids": [34]},
                "meeting_user/34": {"vote_delegated_to_id": 33},
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [4]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/12", {"vote_delegations_from_ids": [15]})
        self.assert_model_exists("meeting_user/22", {"vote_delegations_from_ids": [23]})
        self.assert_model_exists("meeting_user/46", {"vote_delegated_to_id": 33})

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
        self.request("poll.vote", {"id": 1, "value": "N"}, stop_poll_after_vote=False)  # type: ignore
        self.request(
            "poll.vote",
            {"id": 1, "value": "N", "user_id": 5},
            start_poll_before_vote=False,  # type: ignore
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

    @pytest.mark.skipif(
        not isinstance("UserMergeTogether", BaseVoteTestCase),
        reason="set base class to BaseVoteTestCase, if auth isn't mocked for polls anymore. Subsequently remove the skipifs.",
    )
    def test_merge_with_polls_correct(self) -> None:
        password = self.assert_model_exists("user/2")["password"]
        self.create_polls_with_correct_votes()
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)
        self.assert_merge_with_polls_correct(password)

    @pytest.mark.skipif(
        not isinstance("UserMergeTogether", BaseVoteTestCase),
        reason="set base class to BaseVoteTestCase, if auth isn't mocked for polls anymore. Subsequently remove the skipifs.",
    )
    def test_merge_with_polls_and_subsequent_merges(self) -> None:
        password = self.assert_model_exists("user/2")["password"]
        self.create_polls_with_correct_votes()
        response = self.request("user.merge_together", {"id": 3, "user_ids": [4]})
        self.assert_status_code(response, 200)
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3]})
        self.assert_status_code(response, 200)
        self.assert_merge_with_polls_correct(password, 1)

    @pytest.mark.skipif(
        not isinstance("UserMergeTogether", BaseVoteTestCase),
        reason="set base class to BaseVoteTestCase, if auth isn't mocked for polls anymore. Subsequently remove the skipifs.",
    )
    def test_merge_with_polls_all_errors(self) -> None:
        self.set_up_polls_for_merge()
        self.request_multi("poll.start", [{"id": i} for i in range(1, 7)])
        self.login(4)
        self.request("poll.vote", {"id": 1, "value": "N"}, stop_poll_after_vote=False)  # type: ignore
        self.request(
            "poll.vote",
            {"id": 1, "value": "N", "user_id": 5},
            start_poll_before_vote=False,  # type: ignore
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
                3: [[34, 33], [33]],
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
                19: None,
                20: (8, 46, 1),
                21: (9, 46, 1),
            },
            4: {
                22: (10, 45, 1),
            },
        }
        self.assert_assignment_or_motion_model_test_was_correct(
            collection, sub_collection, back_relation, expected
        )

    def test_merge_with_assignment_candidates(self) -> None:
        self.base_assignment_or_motion_model_test("assignment", "assignment_candidate")
        self.assert_history_information(
            "user/2", ["Updated with data from {} and {}", "user/3", "user/4"]
        )
        for id_ in range(2, 10):
            self.assert_history_information(f"assignment/{id_}", ["Candidates merged"])

    def test_merge_with_motion_working_group_speakers(self) -> None:
        self.base_assignment_or_motion_model_test(
            "motion", "motion_working_group_speaker"
        )

    def test_merge_with_motion_editor(self) -> None:
        self.base_assignment_or_motion_model_test("motion", "motion_editor")

    def test_merge_with_motion_submitters_and_supporters(
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
        supporter_ids_per_motion: dict[int, list[int]] = {
            # meeting/1
            1: [14],
            2: [12],
            3: [15],
            4: [12, 14],
            5: [14, 15],
            # meeting/2
            7: [23, 24],
            # meeting/3
            8: [33],
            9: [34],
            # meeting/4
            10: [45],
        }
        motion_ids_per_supporter: dict[int, list[int]] = {
            id_: [
                motion_id
                for motion_id, ids in supporter_ids_per_motion.items()
                if id_ in ids
            ]
            for id_ in {
                muser_id
                for muser_ids in supporter_ids_per_motion.values()
                for muser_id in muser_ids
            }
        }
        self.set_models(
            {
                **{
                    f"meeting_user/{id_}": {"supported_motion_ids": ids}
                    for id_, ids in motion_ids_per_supporter.items()
                },
                **{
                    f"motion/{id_}": {"supporter_meeting_user_ids": ids}
                    for id_, ids in supporter_ids_per_motion.items()
                },
            }
        )
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

        def get_motions(*m_user_ids: int) -> list[int]:
            return list(
                {
                    motion_id
                    for muser_id in m_user_ids
                    for motion_id in motion_ids_per_supporter.get(muser_id, [])
                }
            )

        new_motion_ids_per_supporter: dict[int, list[int]] = {
            12: get_motions(12, 14),
            15: motion_ids_per_supporter[15],
            22: get_motions(22, 23, 24),
            46: get_motions(33, 34),
            45: motion_ids_per_supporter[45],
        }
        for meeting_user_id, motion_ids in new_motion_ids_per_supporter.items():
            self.assert_model_exists(
                f"meeting_user/{meeting_user_id}", {"supported_motion_ids": motion_ids}
            )
        for motion_id in [1, 2, 4]:
            self.assert_model_exists(
                f"motion/{motion_id}", {"supporter_meeting_user_ids": [12]}
            )
        self.assert_model_exists("motion/3", {"supporter_meeting_user_ids": [15]})
        self.assert_model_exists("motion/5", {"supporter_meeting_user_ids": [15, 12]})
        self.assert_model_exists("motion/7", {"supporter_meeting_user_ids": [22]})
        for motion_id in [8, 9]:
            self.assert_model_exists(
                f"motion/{motion_id}", {"supporter_meeting_user_ids": [46]}
            )
        self.assert_model_exists("motion/10", {"supporter_meeting_user_ids": [45]})
        for id_ in range(2, 10):
            self.assert_history_information(f"motion/{id_}", ["Submitters merged"])

    def test_merge_with_personal_notes(self) -> None:
        # create personal notes
        data: dict[str, dict[str, Any]] = {
            **{
                f"meeting/{id_}": {
                    "motion_ids": list(range((id_ - 1) * 2 + 1, id_ * 2 + 1)),
                    "personal_note_ids": [],
                }
                for id_ in range(1, 4)
            },
            **{
                f"motion/{id_}": {
                    "meeting_id": meeting_id,
                    "title": f"Motion {id_}",
                    "text": "XD",
                    "personal_note_ids": [],
                }
                for meeting_id in range(1, 4)
                for id_ in range((meeting_id - 1) * 2 + 1, meeting_id * 2 + 1)
            },
            **{
                f"meeting_user/{id_}": {"personal_note_ids": []}
                for id_ in [12, 14, 15, 22, 23, 24, 33, 34]
            },
        }

        def add_personal_note(
            id_: int,
            motion_id: int,
            meeting_user_id: int,
            note: str | None = None,
            star: bool | None = None,
        ) -> None:
            motion_fqid = f"motion/{motion_id}"
            meeting_id = data[motion_fqid]["meeting_id"]
            date = {
                "meeting_id": meeting_id,
                "content_object_id": motion_fqid,
                "meeting_user_id": meeting_user_id,
            }
            if note is not None:
                date["note"] = note
            if star is not None:
                date["star"] = star
            data[fqid_from_collection_and_id("personal_note", id_)] = date
            for fqid in [
                motion_fqid,
                f"meeting/{meeting_id}",
                f"meeting_user/{meeting_user_id}",
            ]:
                data[fqid]["personal_note_ids"].append(id_)

        add_personal_note(1, 1, 12, "User 2's note")
        add_personal_note(2, 1, 14, "User 4's note", True)
        add_personal_note(3, 1, 15, "User 5's note")

        add_personal_note(4, 2, 14, star=True)

        add_personal_note(5, 3, 24, star=True)
        add_personal_note(6, 3, 22, "", star=False)
        add_personal_note(7, 3, 23, "User 3's note")

        add_personal_note(8, 4, 23, star=False)
        add_personal_note(9, 4, 24, star=True)

        add_personal_note(10, 5, 23, "User 3's note")

        add_personal_note(11, 6, 24, "User 4's note", star=False)
        add_personal_note(12, 6, 23, "User 3's other note")
        self.set_models(data)

        # merge users 3 and 4 into 2
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)

        # check results
        for note_id in [2, 5, 7, 8, 9, 10, 11, 12]:
            self.assert_model_deleted(f"personal_note/{note_id}")
        self.assert_model_exists("personal_note/3")

        meeting_user_by_meeting_id = {1: 12, 2: 22, 3: 46}
        note_base_data_by_motion_id = {
            id_: {
                "meeting_id": meeting_id,
                "meeting_user_id": meeting_user_by_meeting_id[meeting_id],
                "content_object_id": f"motion/{id_}",
            }
            for meeting_id in range(1, 4)
            for id_ in range((meeting_id - 1) * 2 + 1, meeting_id * 2 + 1)
        }
        self.assert_model_exists(
            "personal_note/1",
            {**note_base_data_by_motion_id[1], "note": "User 2's note", "star": True},
        )
        self.assert_model_exists(
            "personal_note/13", {**note_base_data_by_motion_id[2], "star": True}
        )
        self.assert_model_exists(
            "personal_note/6",
            {**note_base_data_by_motion_id[3], "note": "User 3's note", "star": True},
        )
        self.assert_model_exists(
            "personal_note/14", {**note_base_data_by_motion_id[4], "star": True}
        )
        self.assert_model_exists(
            "personal_note/15",
            {
                **note_base_data_by_motion_id[5],
                "note": "User 3's note",
            },
        )
        self.assert_model_exists(
            "personal_note/16",
            {
                **note_base_data_by_motion_id[6],
                "note": "User 3's other note",
                "star": False,
            },
        )

    def test_merge_on_chat_messages(self) -> None:
        # chat_message_ids
        def create_chat_messages(
            data: dict[str, Any],
            meeting_id: int,
            messages_by_meeting_user_by_group: dict[
                int, tuple[str, list[tuple[int, str]]]
            ],
            next_message_id: int = 1,
        ) -> int:
            first_message_id = next_message_id
            chat_message_ids_by_meeting_user: dict[int, list[int]] = {}
            for group_id, (
                group_name,
                messages,
            ) in messages_by_meeting_user_by_group.items():
                data[f"chat_group/{group_id}"] = {
                    "name": group_name,
                    "meeting_id": meeting_id,
                    "chat_message_ids": list(
                        range(next_message_id, next_message_id + len(messages))
                    ),
                }
                for meeting_user_id, message in messages:
                    data[f"chat_message/{next_message_id}"] = {
                        "content": message,
                        "created": next_message_id - first_message_id,
                        "meeting_user_id": meeting_user_id,
                        "chat_group_id": group_id,
                        "meeting_id": meeting_id,
                    }
                    if meeting_user_id not in chat_message_ids_by_meeting_user:
                        chat_message_ids_by_meeting_user[meeting_user_id] = []
                    chat_message_ids_by_meeting_user[meeting_user_id].append(
                        next_message_id
                    )
                    next_message_id += 1
            data[f"meeting/{meeting_id}"] = {
                "chat_group_ids": list(messages_by_meeting_user_by_group.keys()),
                "chat_message_ids": list(range(first_message_id, next_message_id)),
            }
            for (
                meeting_user_id,
                message_ids,
            ) in chat_message_ids_by_meeting_user.items():
                data[f"meeting_user/{meeting_user_id}"] = {
                    "chat_message_ids": message_ids
                }
            return next_message_id

        data: dict[str, Any] = {}
        next_id = create_chat_messages(
            data,
            1,
            {
                1: (
                    "Idle chatter",
                    [
                        (14, "Hey guys!"),
                        (15, "Hello."),
                        (12, "Nice weather today, innit?"),
                        (14, "Quite."),
                    ],
                ),
                2: (
                    "Gossip",
                    [
                        (14, "Have you guys heard?"),
                        (15, "What?"),
                        (14, "John Doe got married!"),
                        (15, "What? To whom?"),
                        (14, "Jane."),
                        (15, "Cool."),
                    ],
                ),
            },
        )
        next_id = create_chat_messages(
            data,
            3,
            {
                3: (
                    "Serious conversation",
                    [
                        (34, "Could someone change the current projection?"),
                        (33, "I'll do it!"),
                        (34, "Thanks."),
                    ],
                )
            },
            next_id,
        )
        create_chat_messages(
            data,
            2,
            {
                4: (
                    "Announcements",
                    [(23, "Lunch will be served soon."), (24, "Lunch is served.")],
                )
            },
            next_id,
        )
        self.set_models(data)

        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)

        self.assert_model_exists(
            "chat_group/1", {"name": "Idle chatter", "chat_message_ids": [1, 2, 3, 4]}
        )
        self.assert_model_exists(
            "chat_group/2", {"name": "Gossip", "chat_message_ids": [5, 6, 7, 8, 9, 10]}
        )
        self.assert_model_exists(
            "chat_group/3",
            {"name": "Serious conversation", "chat_message_ids": [11, 12, 13]},
        )
        self.assert_model_exists(
            "chat_group/4", {"name": "Announcements", "chat_message_ids": [14, 15]}
        )
        self.assert_model_exists(
            "meeting_user/12",
            {"chat_message_ids": [1, 3, 4, 5, 7, 9], "user_id": 2, "meeting_id": 1},
        )
        self.assert_model_exists(
            "meeting_user/22",
            {"chat_message_ids": [14, 15], "user_id": 2, "meeting_id": 2},
        )
        self.assert_model_exists(
            "meeting_user/46",
            {"chat_message_ids": [11, 12, 13], "user_id": 2, "meeting_id": 3},
        )
        for message_id, meeting_user_id, message in [
            # meeting 1
            (1, 12, "Hey guys!"),
            (2, 15, "Hello."),
            (3, 12, "Nice weather today, innit?"),
            (4, 12, "Quite."),
            (5, 12, "Have you guys heard?"),
            (6, 15, "What?"),
            (7, 12, "John Doe got married!"),
            (8, 15, "What? To whom?"),
            (9, 12, "Jane."),
            (10, 15, "Cool."),
            # meeting 2
            (14, 22, "Lunch will be served soon."),
            (15, 22, "Lunch is served."),
            # meeting 3
            (11, 46, "Could someone change the current projection?"),
            (12, 46, "I'll do it!"),
            (13, 46, "Thanks."),
        ]:
            fqid = f"chat_message/{message_id}"
            assert (date := data[fqid])["content"] == message
            self.assert_model_exists(fqid, {**date, "meeting_user_id": meeting_user_id})

    def test_merge_on_group_and_structure_level_ids(self) -> None:
        setup_data = [
            {"tall": [12, 15, 14], "small": [15]},
            {"thin": [22], "fat": [23, 24]},
            {"smart": [33], "dumb": [34]},
        ]
        data: dict[str, dict[str, Any]] = {
            f"meeting/{meeting_id}": {
                "structure_level_ids": list(
                    range((meeting_id - 1) * 2 + 1, meeting_id * 2)
                )
            }
            for meeting_id in range(1, 4)
        }
        structure_level_data: dict[str, dict[str, Any]] = {
            f"structure_level/{(s_level_id := (meeting_id - 1)*2 + s_level_index)}": {
                "id": s_level_id,
                "name": name,
                "meeting_user_ids": meeting_user_ids,
                "meeting_id": meeting_id,
            }
            for meeting_id, structure_levels in enumerate(setup_data, 1)
            for s_level_index, (name, meeting_user_ids) in enumerate(
                structure_levels.items(), 1
            )
        }
        data.update(structure_level_data)
        structure_level_ids_per_meeting_user = {
            meeting_user_id: [
                date["id"]
                for date in structure_level_data.values()
                if meeting_user_id in date["meeting_user_ids"]
            ]
            for meeting_user_id in [12, 14, 15, 22, 23, 24, 33, 34]
        }
        data.update(
            {
                f"meeting_user/{meeting_user_id}": {
                    "structure_level_ids": structure_level_ids
                }
                for meeting_user_id, structure_level_ids in structure_level_ids_per_meeting_user.items()
            }
        )
        self.set_models(data)

        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)

        self.assert_model_exists(
            "meeting_user/12", {"structure_level_ids": [1], "group_ids": [1, 2]}
        )
        self.assert_model_exists(
            "meeting_user/22", {"structure_level_ids": [3, 4], "group_ids": [4, 5]}
        )
        self.assert_model_exists(
            "meeting_user/46", {"structure_level_ids": [5, 6], "group_ids": [8, 9]}
        )

        self.assert_model_exists("structure_level/1", {"meeting_user_ids": [12, 15]})
        self.assert_model_exists("structure_level/2", {"meeting_user_ids": [15]})
        self.assert_model_exists("structure_level/3", {"meeting_user_ids": [22]})
        self.assert_model_exists("structure_level/4", {"meeting_user_ids": [22]})
        self.assert_model_exists("structure_level/5", {"meeting_user_ids": [46]})
        self.assert_model_exists("structure_level/6", {"meeting_user_ids": [46]})

        self.assert_model_exists("group/1", {"meeting_user_ids": [12]})
        self.assert_model_exists("group/2", {"meeting_user_ids": [12, 15]})
        self.assert_model_exists("group/4", {"meeting_user_ids": [22]})
        self.assert_model_exists("group/5", {"meeting_user_ids": [22]})
        self.assert_model_exists("group/8", {"meeting_user_ids": [46]})
        self.assert_model_exists("group/9", {"meeting_user_ids": [46]})

    def create_speakers_for_test(
        self, allow_multiple_speakers: bool = False
    ) -> dict[str, Any]:
        # TODO: shorter
        data: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "motion_block_ids": [],
                "list_of_speakers_ids": [],
                "point_of_order_category_ids": [1, 2],
                "speaker_ids": [],
                "structure_level_list_of_speakers_ids": [],
                "structure_level_ids": [1, 2],
                "list_of_speakers_enable_pro_contra_speech": True,
                "list_of_speakers_enable_interposed_question": True,
                "list_of_speakers_intervention_time": 30,
            },
            "meeting/3": {
                "motion_block_ids": [],
                "list_of_speakers_ids": [],
                "point_of_order_category_ids": [3, 4],
                "speaker_ids": [],
                "structure_level_list_of_speakers_ids": [],
                "structure_level_ids": [3, 4],
                "list_of_speakers_enable_point_of_order_speakers": True,
                "list_of_speakers_enable_point_of_order_categories": True,
            },
            "structure_level/1": {
                "name": "A",
                "structure_level_list_of_speakers_ids": [],
                "meeting_id": 1,
            },
            "structure_level/2": {
                "name": "B",
                "structure_level_list_of_speakers_ids": [],
                "meeting_id": 1,
            },
            "structure_level/3": {
                "name": "A",
                "structure_level_list_of_speakers_ids": [],
                "meeting_id": 3,
            },
            "structure_level/4": {
                "name": "B",
                "structure_level_list_of_speakers_ids": [],
                "meeting_id": 3,
            },
            "point_of_order_category/1": {
                "text": "A",
                "rank": 1,
                "meeting_id": 1,
                "speaker_ids": [],
            },
            "point_of_order_category/2": {
                "text": "B",
                "rank": 2,
                "meeting_id": 1,
                "speaker_ids": [],
            },
            "point_of_order_category/3": {
                "text": "A",
                "rank": 1,
                "meeting_id": 3,
                "speaker_ids": [],
            },
            "point_of_order_category/4": {
                "text": "B",
                "rank": 2,
                "meeting_id": 3,
                "speaker_ids": [],
            },
            **{
                f"meeting_user/{id_}": {"speaker_ids": []}
                for id_ in [12, 14, 15, 33, 34]
            },
        }
        if allow_multiple_speakers:
            for id_ in [1, 3]:
                data[f"meeting/{id_}"][
                    "list_of_speakers_allow_multiple_speakers"
                ] = True

        def add_list_of_speakers(
            base_id: int,
            meeting_id: int,
            speakers: list[
                tuple[
                    int,
                    int,
                    SpeechState | None,
                    bool | None,
                    int | None,
                    int | None,
                    dict[str, Any],
                ]
            ],
            next_speaker_id: int = 1,
        ) -> int:
            block_fqid = f"motion_block/{base_id}"
            data[f"meeting/{meeting_id}"]["motion_block_ids"].append(base_id)
            data[f"meeting/{meeting_id}"]["list_of_speakers_ids"].append(base_id)
            data[f"structure_level/{meeting_id}"][
                "structure_level_list_of_speakers_ids"
            ].append(base_id * 2 - 1)
            data[f"structure_level/{meeting_id+1}"][
                "structure_level_list_of_speakers_ids"
            ].append(base_id * 2)
            data.update(
                {
                    block_fqid: {
                        "title": f"MB{base_id}",
                        "meeting_id": meeting_id,
                        "list_of_speakers_id": base_id,
                    },
                    f"list_of_speakers/{base_id}": {
                        "content_object_id": block_fqid,
                        "meeting_id": meeting_id,
                        "speaker_ids": list(
                            range(next_speaker_id, next_speaker_id + len(speakers))
                        ),
                        "structure_level_list_of_speakers_ids": [
                            base_id * 2 - 1,
                            base_id * 2,
                        ],
                    },
                    f"structure_level_list_of_speakers/{base_id*2-1}": {
                        "structure_level_id": meeting_id,
                        "list_of_speakers_id": base_id,
                        "speaker_ids": [],
                        "initial_time": 5,
                        "remaining_time": 5,
                        "meeting_id": 1,
                    },
                    f"structure_level_list_of_speakers/{base_id*2}": {
                        "structure_level_id": meeting_id + 1,
                        "list_of_speakers_id": base_id,
                        "speaker_ids": [],
                        "initial_time": 5,
                        "remaining_time": 5,
                        "meeting_id": 1,
                    },
                }
            )
            for speaker in speakers:
                (
                    meeting_user_id,
                    weight,
                    speech_state,
                    point_of_order,
                    point_of_order_category_id,
                    structure_level_id,
                    additional,
                ) = speaker
                data[f"meeting/{meeting_id}"]["speaker_ids"].append(next_speaker_id)
                data[f"meeting_user/{meeting_user_id}"]["speaker_ids"].append(
                    next_speaker_id
                )
                speaker_data: dict[str, Any] = {
                    "meeting_id": meeting_id,
                    "list_of_speakers_id": base_id,
                    "meeting_user_id": meeting_user_id,
                    "weight": weight,
                    **additional,
                }
                if speech_state:
                    speaker_data["speech_state"] = speech_state
                if point_of_order is not None:
                    speaker_data["point_of_order"] = point_of_order
                if point_of_order_category_id:
                    speaker_data["point_of_order_category_id"] = (
                        point_of_order_category_id
                    )
                    data[f"point_of_order_category/{point_of_order_category_id}"][
                        "speaker_ids"
                    ].append(next_speaker_id)
                if structure_level_id:
                    structure_level_list_of_speakers_id = base_id * 2 - (
                        structure_level_id % 2
                    )
                    speaker_data["structure_level_list_of_speakers_id"] = (
                        structure_level_list_of_speakers_id
                    )
                    data[
                        f"structure_level_list_of_speakers/{structure_level_list_of_speakers_id}"
                    ]["speaker_ids"].append(next_speaker_id)
                data[f"speaker/{next_speaker_id}"] = speaker_data
                next_speaker_id += 1
            return next_speaker_id

        # meeting_user_id, weight, speech_state, point_of_order, point_of_order_category_id, structure_level_id
        finished_data = {"begin_time": 1, "end_time": 5}
        finished_with_pause_data = {**finished_data, "total_pause": 2}
        next_id = add_list_of_speakers(
            1,
            1,
            [
                (12, 1, None, None, None, 1, {}),
                (14, 2, None, True, None, 2, {}),  # to merge
                (14, 5, None, None, None, 1, {}),  # to merge
                (15, 4, None, None, None, 2, {}),
                (12, 3, None, True, None, 2, {}),
            ],
        )
        next_id = add_list_of_speakers(
            2,
            1,
            [
                (14, 1, SpeechState.PRO, None, None, None, {}),  # to merge
                (12, 2, None, True, 2, None, {"note": "ASDF"}),
                (14, 3, None, True, 2, None, {"note": "ASDF"}),  # to merge
                (12, 4, SpeechState.PRO, None, None, None, {}),
            ],
            next_id,
        )
        next_id = add_list_of_speakers(
            3,
            1,
            [
                (14, 1, SpeechState.PRO, None, None, None, finished_data),  # replaced
                (12, 2, None, True, 1, None, finished_with_pause_data),
                (14, 3, None, True, 1, None, {}),  # replaced
                (12, 4, None, None, None, None, {}),
            ],
            next_id,
        )
        next_id = add_list_of_speakers(
            4,
            3,
            [
                (33, 2, SpeechState.CONTRA, None, None, None, {}),  # to merge into new
                (34, 1, SpeechState.CONTRA, None, None, None, {}),  # to merge into new
            ],
            next_id,
        )
        next_id = add_list_of_speakers(
            5,
            1,
            [
                (14, 1, SpeechState.INTERVENTION, None, None, None, {}),  # to merge
                (12, 2, SpeechState.INTERVENTION, None, None, None, {}),
            ],
            next_id,
        )
        next_id = add_list_of_speakers(
            6,
            1,
            [
                (12, 1, SpeechState.INTERPOSED_QUESTION, None, None, None, {}),
                (
                    14,
                    2,
                    SpeechState.INTERPOSED_QUESTION,
                    None,
                    None,
                    None,
                    {},
                ),  # to merge
            ],
            next_id,
        )
        next_id = add_list_of_speakers(
            7,
            1,
            [
                (12, 1, SpeechState.CONTRIBUTION, None, None, None, {}),
                (14, 2, SpeechState.CONTRIBUTION, None, None, None, {}),  # to merge
            ],
            next_id,
        )
        next_id = add_list_of_speakers(
            8,
            1,
            [
                (12, 1, SpeechState.CONTRIBUTION, None, None, None, {}),
                (14, 2, None, True, None, None, {}),
            ],
            next_id,
        )
        # 23 speakers on 8 lists
        self.set_models(data)
        return data

    def test_with_speakers_simple(self) -> None:
        data = self.create_speakers_for_test()
        data = {k: v.copy() for k, v in data.items()}
        for value in data.values():
            value.pop("id", 0)

        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)

        merged_away = [2, 3, 6, 8, 14, 16, 19, 21]
        replaced = [10, 12, 15, 23]
        deleted_ids = replaced + merged_away
        for id_ in deleted_ids:
            self.assert_model_deleted(f"speaker/{id_}")
        for id_ in [4, 11, 13, 22]:
            self.assert_model_exists(f"speaker/{id_}", data[f"speaker/{id_}"])
        for id_ in [1, 9, 17, 18, 20]:
            self.assert_model_exists(
                f"speaker/{id_}", {**data[f"speaker/{id_}"], "weight": 1}
            )
        for id_ in [5, 7]:
            self.assert_model_exists(
                f"speaker/{id_}", {**data[f"speaker/{id_}"], "weight": 2}
            )
        next_id = 24
        for m_user_id, speaker_ids in {12: [10, 12, 23], 46: [15]}.items():
            for speaker_id in speaker_ids:
                self.assert_model_exists(
                    f"speaker/{next_id}",
                    {**data[f"speaker/{speaker_id}"], "meeting_user_id": m_user_id},
                )
                next_id += 1

        self.assert_model_exists(
            "meeting_user/12",
            {"speaker_ids": [1, 5, 7, 9, 11, 13, 17, 18, 20, 22, 24, 25, 26]},
        )
        self.assert_model_exists("meeting_user/46", {"speaker_ids": [27]})

    def test_with_speakers_multiple_speakers_allowed(self) -> None:
        data = self.create_speakers_for_test(allow_multiple_speakers=True)
        data = {k: v.copy() for k, v in data.items()}
        for value in data.values():
            value.pop("id", 0)

        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)

        replaced_meeting_1 = [2, 3, 6, 8, 10, 12, 16, 19, 21, 23]
        replaced_meeting_3 = [14, 15]
        deleted_ids = replaced_meeting_1 + replaced_meeting_3
        for id_ in range(1, 24):
            if id_ in deleted_ids:
                self.assert_model_deleted(f"speaker/{id_}")
            else:
                self.assert_model_exists(f"speaker/{id_}", data[f"speaker/{id_}"])
        next_id = 24
        for m_user_id, speaker_ids in {
            12: replaced_meeting_1,
            46: replaced_meeting_3,
        }.items():
            for speaker_id in speaker_ids:
                self.assert_model_exists(
                    f"speaker/{next_id}",
                    {**data[f"speaker/{speaker_id}"], "meeting_user_id": m_user_id},
                )
                next_id += 1

        self.assert_model_exists(
            "meeting_user/12",
            {
                "speaker_ids": [
                    1,
                    5,
                    7,
                    9,
                    11,
                    13,
                    17,
                    18,
                    20,
                    22,
                    *range(24, 24 + len(replaced_meeting_1)),
                ]
            },
        )
        self.assert_model_exists(
            "meeting_user/46",
            {
                "speaker_ids": list(
                    range(24 + len(replaced_meeting_1), 26 + len(replaced_meeting_1))
                )
            },
        )

    def test_with_running_speaker(self) -> None:
        self.create_speakers_for_test()
        self.set_models({"speaker/5": {"begin_time": 1}})

        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Speaker(s) 5 are still running in meeting(s) 1",
            response.json["message"],
        )

    def test_with_speakers_different_point_of_order_category(self) -> None:
        self.create_speakers_for_test()
        self.set_models({"speaker/5": {"point_of_order_category_id": 1}})

        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Differing values in field point_of_order_category_id when merging into speaker/5",
            response.json["message"],
        )

    def test_with_speakers_different_note(self) -> None:
        self.create_speakers_for_test()
        self.set_models(
            {"speaker/5": {"note": "Tilt the picture frame a little to the left"}}
        )

        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Differing values in field note when merging into speaker/5",
            response.json["message"],
        )

    def test_with_speakers_different_speech_state(self) -> None:
        self.create_speakers_for_test()
        self.set_models({"speaker/3": {"speech_state": SpeechState.CONTRA}})

        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Differing values in field speech_state when merging into speaker/1",
            response.json["message"],
        )

    def test_with_speakers_different_sllos(self) -> None:
        self.create_speakers_for_test()
        self.set_models({"speaker/3": {"structure_level_list_of_speakers_id": 2}})

        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Differing values in field structure_level_list_of_speakers_id when merging into speaker/1",
            response.json["message"],
        )

    def archive_all_meetings(self) -> None:
        self.set_models(
            {
                ONE_ORGANIZATION_FQID: {
                    "active_meeting_ids": [],
                    "archived_meeting_ids": [1, 2, 3, 4],
                },
                **{
                    f"meeting/{id_}": {
                        "is_archived_in_organization_id": ONE_ORGANIZATION_ID,
                        "is_active_in_organization_id": None,
                    }
                    for id_ in [1, 2, 3, 4]
                },
            }
        )

    def test_merge_archived_with_user_fields(self) -> None:
        self.archive_all_meetings()
        self.test_merge_with_user_fields()

    def test_merge_archived_with_assignment_candidates(self) -> None:
        self.archive_all_meetings()
        self.test_merge_with_assignment_candidates()

    def test_merge_archived_on_chat_messages(self) -> None:
        self.archive_all_meetings()
        self.test_merge_on_chat_messages()

    def test_merge_archived_with_motion_editor(self) -> None:
        self.archive_all_meetings()
        self.test_merge_with_motion_editor()

    def test_merge_archived_with_motion_submitters_and_supporters(self) -> None:
        self.archive_all_meetings()
        self.test_merge_with_motion_submitters_and_supporters()

    def test_merge_archived_with_motion_working_group_speakers(self) -> None:
        self.archive_all_meetings()
        self.test_merge_with_motion_working_group_speakers()

    def test_merge_archived_with_personal_notes(self) -> None:
        self.archive_all_meetings()
        self.test_merge_with_personal_notes()

    def test_merge_archived_with_running_speaker(self) -> None:
        self.archive_all_meetings()
        self.test_with_running_speaker()

    def test_merge_archived_normal(self) -> None:
        self.archive_all_meetings()
        self.test_merge_normal()

    @pytest.mark.skipif(
        not isinstance("UserMergeTogether", BaseVoteTestCase),
        reason="set base class to BaseVoteTestCase, if auth isn't mocked for polls anymore. Subsequently remove the skipifs.",
    )
    def test_merge_archived_polls(self) -> None:
        password = self.assert_model_exists("user/2")["password"]
        self.create_polls_with_correct_votes()
        self.archive_all_meetings()
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)
        self.assert_merge_with_polls_correct(password)

    def test_merge_multi_request(self) -> None:
        response = self.request_multi(
            "user.merge_together",
            [{"id": 2, "user_ids": [3]}, {"id": 4, "user_ids": [5, 6]}],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"meeting_user_ids": [12, 22, 46]})
        self.assert_model_exists("user/4", {"meeting_user_ids": [14, 24, 34, 47]})
        self.assert_model_deleted("user/3")
        self.assert_model_deleted("user/5")
        self.assert_model_deleted("user/6")

        self.assert_model_exists("meeting_user/12", {"meeting_id": 1})
        self.assert_model_exists("meeting_user/22", {"meeting_id": 2})
        self.assert_model_exists("meeting_user/46", {"meeting_id": 3})
        self.assert_model_exists("meeting_user/14", {"meeting_id": 1})
        self.assert_model_exists("meeting_user/24", {"meeting_id": 2})
        self.assert_model_exists("meeting_user/34", {"meeting_id": 3})
        self.assert_model_exists("meeting_user/47", {"meeting_id": 4})
        for id_ in [23, 33, 15, 45]:
            self.assert_model_deleted(f"meeting_user/{id_}")

        self.assert_history_information(
            "user/2", ["Updated with data from {}", "user/3"]
        )
        self.assert_history_information("user/3", ["Merged into {}", "user/2"])

        self.assert_history_information(
            "user/4", ["Updated with data from {} and {}", "user/5", "user/6"]
        )
        self.assert_history_information("user/5", ["Merged into {}", "user/4"])
        self.assert_history_information("user/6", ["Merged into {}", "user/4"])

    def test_merge_multi_request_conflict(self) -> None:
        response = self.request_multi(
            "user.merge_together",
            [{"id": 2, "user_ids": [3]}, {"id": 4, "user_ids": [3, 5, 6]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Users cannot be part of different merges at the same time",
            response.json["message"],
        )

    def test_merge_multi_request_conflict_2(self) -> None:
        response = self.request_multi(
            "user.merge_together",
            [{"id": 2, "user_ids": [3]}, {"id": 4, "user_ids": [2, 5, 6]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Users cannot be part of different merges at the same time",
            response.json["message"],
        )

    def test_merge_no_meetings(self) -> None:
        self.create_user("user7")
        response = self.request("user.merge_together", {"id": 6, "user_ids": [7]})
        self.assert_status_code(response, 200)

    def test_merge_only_update_meeting_users(self) -> None:
        response = self.request("user.merge_together", {"id": 4, "user_ids": [3]})
        self.assert_status_code(response, 200)

    def test_merge_with_motion_submitter_transfer(
        self,
    ) -> None:
        data: dict[str, Any] = {}
        self.add_assignment_or_motion_models_for_meetings(
            data,
            "motion",
            "motion_submitter",
            "submitter_ids",
            {3: [[33]]},
        )
        self.set_models(data)
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3]})
        self.assert_status_code(response, 200)
        expected: dict[int, dict[int, tuple[int, int, int] | None]] = {
            # meeting_id:sub_model_id:(model_id, meeting_user_id, weight) | None if deleted
            3: {
                1: None,
                2: (1, 46, 1),
            },
        }
        self.assert_assignment_or_motion_model_test_was_correct(
            "motion", "motion_submitter", "submitter_ids", expected
        )

    def test_merge_with_legacy_vote_weight(self) -> None:
        self.set_models(
            {
                "meeting_user/14": {"vote_weight": "0.000000"},
                "meeting_user/22": {"vote_weight": "0.000000"},
                "meeting_user/34": {"vote_weight": "0.000000"},
                "user/2": {"default_vote_weight": "0.000000"},
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [4]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"default_vote_weight": "0.000000"})
        self.assert_model_exists("meeting_user/12", {"vote_weight": "1.000000"})
        self.assert_model_exists("meeting_user/22", {"vote_weight": "0.000001"})
        self.assert_model_exists("meeting_user/46", {"vote_weight": "0.000001"})

    def test_merge_with_presence(self) -> None:
        self.set_models(
            {
                "user/3": {"is_present_in_meeting_ids": [2, 3]},
                "user/5": {"is_present_in_meeting_ids": [4]},
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4, 5]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"is_present_in_meeting_ids": [3, 4]})

    def test_merge_with_locked_out(self) -> None:
        self.set_models(
            {
                "meeting_user/12": {"locked_out": True, "group_ids": [2]},
                "meeting_user/14": {"group_ids": [2]},
                "meeting_user/15": {"group_ids": [2]},
                "meeting_user/22": {"group_ids": [5]},
                "meeting_user/23": {"locked_out": True, "group_ids": [5]},
                "meeting_user/24": {"group_ids": [5]},
                "meeting_user/33": {"group_ids": [8]},
                "meeting_user/34": {"locked_out": True, "group_ids": [8]},
                "meeting_user/45": {"locked_out": True, "group_ids": [11]},
                "group/2": {"meeting_user_ids": [12, 14, 15]},
                "group/5": {"meeting_user_ids": [22, 23, 24]},
                "group/8": {"meeting_user_ids": [33, 34]},
                "group/11": {"meeting_user_ids": [45]},
                **{
                    f"group/{id_}": {"meeting_user_ids": None}
                    for id_ in [1, 3, 4, 6, 7, 9, 10, 12]
                },
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4, 5]})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "meeting_user/12", {"user_id": 2, "meeting_id": 1, "locked_out": True}
        )
        self.assert_model_exists(
            "meeting_user/22", {"user_id": 2, "meeting_id": 2, "locked_out": None}
        )
        self.assert_model_exists(
            "meeting_user/46", {"user_id": 2, "meeting_id": 3, "locked_out": None}
        )
        self.assert_model_exists(
            "meeting_user/47", {"user_id": 2, "meeting_id": 4, "locked_out": True}
        )

    def test_merge_with_locked_out_meetingadmin_error(self) -> None:
        self.set_models(
            {
                "meeting_user/12": {"locked_out": True, "group_ids": [2]},
                "meeting_user/14": {"group_ids": [2]},
                "meeting_user/15": {"group_ids": [2]},
                "meeting_user/22": {"group_ids": [5]},
                "meeting_user/23": {"locked_out": True, "group_ids": [5]},
                "meeting_user/24": {"group_ids": [4]},
                "meeting_user/33": {"group_ids": [8]},
                "meeting_user/34": {"locked_out": True, "group_ids": [8]},
                "meeting_user/45": {"locked_out": True, "group_ids": [10]},
                "group/2": {"meeting_user_ids": [12, 14, 15]},
                "group/4": {"meeting_user_ids": [24]},
                "group/5": {"meeting_user_ids": [22, 23]},
                "group/8": {"meeting_user_ids": [33, 34]},
                "group/10": {"meeting_user_ids": [45]},
                **{
                    f"group/{id_}": {"meeting_user_ids": None}
                    for id_ in [1, 3, 6, 7, 9, 11, 12]
                },
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4, 5]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Group(s) 10 have user.can_manage permissions and may therefore not be used by users who are locked out",
            response.json["message"],
        )

    def test_merge_with_locked_out_super_admin_error(self) -> None:
        self.set_models(
            {
                "meeting_user/12": {"group_ids": [2]},
                "meeting_user/14": {"group_ids": [2]},
                "meeting_user/15": {"group_ids": [2]},
                "meeting_user/22": {"locked_out": True, "group_ids": [5]},
                "meeting_user/23": {"group_ids": [5]},
                "meeting_user/24": {"group_ids": [5]},
                "meeting_user/33": {"locked_out": True, "group_ids": [8]},
                "meeting_user/34": {"group_ids": [8]},
                "meeting_user/45": {"group_ids": [11]},
                "group/2": {"meeting_user_ids": [12, 14, 15]},
                "group/5": {"meeting_user_ids": [22, 23, 24]},
                "group/8": {"meeting_user_ids": [33, 34]},
                "group/11": {"meeting_user_ids": [45]},
                **{
                    f"group/{id_}": {"meeting_user_ids": None}
                    for id_ in [1, 3, 4, 6, 7, 9, 10, 12]
                },
            }
        )
        self.set_organization_management_level(
            OrganizationManagementLevel.SUPERADMIN, 5
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4, 5]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot give OrganizationManagementLevel superadmin to user 2 as he is locked out of meeting(s) 2, 3",
            response.json["message"],
        )

    def test_merge_with_locked_out_committee_admin_error(self) -> None:
        self.set_models(
            {
                "meeting_user/12": {"locked_out": True, "group_ids": [2]},
                "meeting_user/14": {"group_ids": [2]},
                "meeting_user/15": {"group_ids": [2]},
                "meeting_user/22": {"group_ids": [5]},
                "meeting_user/23": {"group_ids": [5]},
                "meeting_user/24": {"group_ids": [5]},
                "meeting_user/33": {"locked_out": True, "group_ids": [8]},
                "meeting_user/34": {"group_ids": [8]},
                "meeting_user/45": {"group_ids": [11]},
                "group/2": {"meeting_user_ids": [12, 14, 15]},
                "group/5": {"meeting_user_ids": [22, 23, 24]},
                "group/8": {"meeting_user_ids": [33, 34]},
                "group/11": {"meeting_user_ids": [45]},
                **{
                    f"group/{id_}": {"meeting_user_ids": None}
                    for id_ in [1, 3, 4, 6, 7, 9, 10, 12]
                },
            }
        )
        self.set_committee_management_level([1, 3], 5)
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4, 5]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot set user 2 as manager for committee(s) 1 due to being locked out of meeting(s) 1",
            response.json["message"],
        )
