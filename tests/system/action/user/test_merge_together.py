from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, cast
from zoneinfo import ZoneInfo

import pytest

from openslides_backend.action.actions.speaker.speech_state import SpeechState
from openslides_backend.action.relations.relation_manager import RelationManager
from openslides_backend.action.util.actions_map import actions_map
from openslides_backend.permissions.management_levels import OrganizationManagementLevel
from openslides_backend.shared.patterns import (
    CollectionField,
    fqid_from_collection_and_id,
)
from openslides_backend.shared.util import ONE_ORGANIZATION_ID
from tests.system.action.base import BaseActionTestCase
from tests.system.action.poll.test_vote import BaseVoteTestCase
from tests.util import Response


class UserMergeTogether(BaseActionTestCase):
    """committee/63 is created but remains unused in all of the tests as 60 is used for meeting/1 and 4"""

    def setUp(self) -> None:
        super().setUp()
        for meeting_id in range(1, 11, 3):
            self.create_meeting(meeting_id)
        models: dict[str, dict[str, Any]] = {
            "user/2": {
                "username": "user2",
                "is_active": True,
                "default_password": "user2",
                "password": self.auth.hash("user2"),
                "meeting_user_ids": [12, 42],
                "committee_ids": [60],
                "organization_id": 1,
            },
            "user/3": {
                "username": "user3",
                "is_active": True,
                "default_password": "user3",
                "password": self.auth.hash("user3"),
                "meeting_user_ids": [43, 73],
                "committee_ids": [60, 66],
                "organization_id": 1,
            },
            "user/4": {
                "username": "user4",
                "is_active": True,
                "default_password": "user4",
                "password": self.auth.hash("user4"),
                "meeting_user_ids": [14, 44, 74],
                "committee_ids": [60, 66],
                "organization_id": 1,
            },
            "user/5": {
                "username": "user5",
                "is_active": True,
                "default_password": "user5",
                "password": self.auth.hash("user5"),
                "meeting_user_ids": [15, 105],
                "committee_ids": [60, 69],
                "organization_id": 1,
            },
            "user/6": {
                "username": "user6",
                "is_active": True,
                "default_password": "user6",
                "password": self.auth.hash("user6"),
                "meeting_user_ids": [],
                "committee_ids": [],
                "organization_id": 1,
            },
            "organization/1": {
                "limit_of_meetings": 0,
                "enable_electronic_voting": True,
                "user_ids": [2, 3, 4, 5, 6],
                "gender_ids": [1, 2, 3, 4],
            },
            "gender/1": {
                "name": "male",
                "organization_id": 1,
            },
            "gender/2": {
                "name": "female",
                "organization_id": 1,
            },
            "gender/3": {
                "name": "diverse",
                "organization_id": 1,
            },
            "gender/4": {
                "name": "non-binary",
                "organization_id": 1,
            },
            "meeting/1": {
                "name": "Meeting 1",
                "users_enable_vote_delegations": True,
                "admin_group_id": 1,
                "default_group_id": 3,
                "meeting_user_ids": [12, 14, 15],
            },
            "group/1": {
                "name": "Group 1",
                "meeting_user_ids": [12],
            },
            "group/2": {
                "name": "Group 2",
                "meeting_user_ids": [12, 14, 15],
            },
            "group/3": {
                "name": "Group 3",
                "meeting_user_ids": [],
            },
            "meeting_user/12": {
                "user_id": 2,
                "meeting_id": 1,
                "group_ids": [1, 2],
                "vote_weight": Decimal("1"),
            },
            "meeting_user/14": {
                "user_id": 4,
                "meeting_id": 1,
                "group_ids": [2],
                "vote_weight": Decimal("1"),
            },
            "meeting_user/15": {
                "user_id": 5,
                "meeting_id": 1,
                "group_ids": [2],
                "vote_weight": Decimal("1"),
            },
            "meeting/4": {
                "name": "Meeting 2",
                "users_enable_vote_delegations": True,
                "committee_id": 60,  # same as in meeting/1
                "admin_group_id": 4,
                "default_group_id": 6,
                "meeting_user_ids": [42, 43, 44],
            },
            "group/4": {
                "name": "Group 4",
                "meeting_user_ids": [44],
            },
            "group/5": {
                "name": "Group 5",
                "meeting_user_ids": [42, 43],
            },
            "group/6": {
                "name": "Group 6",
                "meeting_user_ids": [],
            },
            "meeting_user/42": {
                "user_id": 2,
                "meeting_id": 4,
                "group_ids": [5],
                "vote_weight": Decimal("1"),
            },
            "meeting_user/43": {
                "user_id": 3,
                "meeting_id": 4,
                "group_ids": [5],
                "vote_weight": Decimal("1"),
            },
            "meeting_user/44": {
                "user_id": 4,
                "meeting_id": 4,
                "group_ids": [4],
                "vote_weight": Decimal("1"),
            },
            "meeting/7": {
                "name": "Meeting 3",
                "users_enable_vote_delegations": True,
                "admin_group_id": 7,
                "default_group_id": 9,
                "meeting_user_ids": [73, 74],
            },
            "group/7": {
                "name": "Group 7",
                "meeting_user_ids": [],
            },
            "group/8": {
                "name": "Group 8",
                "meeting_user_ids": [73],
            },
            "group/9": {
                "name": "Group 9",
                "meeting_user_ids": [74],
            },
            "meeting_user/73": {
                "user_id": 3,
                "meeting_id": 7,
                "group_ids": [8],
                "vote_weight": Decimal("1"),
            },
            "meeting_user/74": {
                "user_id": 4,
                "meeting_id": 7,
                "group_ids": [9],
                "vote_weight": Decimal("1"),
            },
            "meeting/10": {
                "name": "Meeting 4",
                "users_enable_vote_delegations": True,
                "admin_group_id": 10,
                "default_group_id": 12,
                "meeting_user_ids": [105],
            },
            "group/10": {
                "name": "Group 10",
                "meeting_user_ids": [105],
            },
            "group/11": {
                "name": "Group 11",
                "meeting_user_ids": [],
            },
            "group/12": {
                "name": "Group 12",
                "meeting_user_ids": [],
            },
            "meeting_user/105": {
                "user_id": 5,
                "meeting_id": 10,
                "group_ids": [10],
                "vote_weight": Decimal("1"),
            },
        }
        self.set_models(models)

    def create_assignment(
        self, base: int, meeting_id: int, assignment_data: dict[str, Any] = {}
    ) -> None:
        self.set_models(
            {
                f"assignment/{base}": {
                    "title": "just do it",
                    "sequential_number": base,
                    "meeting_id": meeting_id,
                    **assignment_data,
                },
                f"list_of_speakers/{base + 100}": {
                    "content_object_id": f"assignment/{base}",
                    "sequential_number": base + 100,
                    "meeting_id": meeting_id,
                },
            }
        )

    def test_merge_configuration_up_to_date(self) -> None:
        """
        This test checks, if the merge_together function has been properly
        updated to be able to handle the current data structure.
        If this test fails, it is likely because new fields have been added
        to the collections listed in the AssertionError without considering
        the necessary changes to the user merge.
        This can be fixed by editing the _collection_field_groups in the
        action class if it is the 'user' collection,
        or else in the corresponding merge mixin class in merge_mixins.py.
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
            {
                "meeting_ids": [1, 4],
                "meeting_user_ids": [106, 107],
                "committee_ids": [60],
            },
        )
        self.assert_model_not_exists("user/2")

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
                "meeting_ids": [1, 4, 7],
                "committee_ids": [60, 66],
                "organization_id": 1,
                "default_password": "user2",
                "meeting_user_ids": [12, 42, 106],
                "password": password,
            },
        )
        self.assert_model_not_exists("user/3")

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
                "meeting_ids": [1, 4, 7],
                "committee_ids": [60, 66],
                "organization_id": 1,
                "default_password": "user2",
                "meeting_user_ids": [12, 42, 106],
                "password": None,
                "saml_id": "user2",
            },
        )
        self.assert_model_not_exists("user/3")
        self.assert_model_not_exists("user/4")

    def test_merge_with_saml_id_with_password_change_rights(self) -> None:
        self.set_models(
            {
                "user/2": {
                    "password": None,
                    "saml_id": "user2",
                },
                "user/3": {"can_change_own_password": True},
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/2",
            {
                "is_active": True,
                "username": "user2",
                "meeting_ids": [1, 4, 7],
                "committee_ids": [60, 66],
                "organization_id": 1,
                "default_password": "user2",
                "meeting_user_ids": [12, 42, 106],
                "password": None,
                "saml_id": "user2",
            },
        )
        self.assert_model_not_exists("user/3")
        self.assert_model_not_exists("user/4")

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
                "committee/60": {"manager_ids": [2, 5]},
                "committee/69": {"manager_ids": [5]},
                "meeting/4": {"present_user_ids": [4], "locked_from_inside": True},
                "meeting/7": {"present_user_ids": [3, 4]},
                "meeting/10": {"present_user_ids": [5]},
                "user/2": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
                    "pronoun": "he",
                    "first_name": "Nick",
                    "is_active": False,
                    "can_change_own_password": True,
                    "gender_id": 1,
                    "email": "nick.everything@rob.banks",
                    "last_email_sent": datetime.fromtimestamp(
                        123456789, ZoneInfo("UTC")
                    ),
                    "committee_management_ids": [60],
                    "home_committee_id": 60,
                },
                "user/3": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                    "pronoun": "she",
                    "title": "Dr.",
                    "first_name": "Rob",
                    "last_name": "Banks",
                    "is_physical_person": True,
                    "default_vote_weight": Decimal("1.234567"),
                    "last_login": datetime.fromtimestamp(987654321, ZoneInfo("UTC")),
                    "is_present_in_meeting_ids": [7],
                    "external": True,
                },
                "user/4": {
                    "organization_management_level": OrganizationManagementLevel.SUPERADMIN,
                    "is_active": True,
                    "is_physical_person": False,
                    "gender_id": 2,
                    "last_email_sent": datetime.fromtimestamp(
                        234567890, ZoneInfo("UTC")
                    ),
                    "is_present_in_meeting_ids": [4, 7],
                    "member_number": "souperadmin",
                    "external": False,
                },
                "user/5": {
                    "organization_management_level": OrganizationManagementLevel.CAN_MANAGE_USERS,
                    "pronoun": "it",
                    "title": "Prof. Dr. Dr.",
                    "last_name": "Everything",
                    "can_change_own_password": False,
                    "is_present_in_meeting_ids": [10],
                    "committee_management_ids": [60, 69],
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
                "meeting_user/42": {
                    "number": "num?",
                    "vote_weight": "2.000000",
                },
                "meeting_user/43": {
                    "comment": "Comment 1",
                    "vote_weight": "3.000000",
                },
                "meeting_user/44": {
                    "number": "NOM!",
                    "comment": "Comment 2: Electric Boogaloo",
                },
                "meeting_user/73": {
                    "about_me": "I have a long beard",
                    "vote_weight": "1.234567",
                },
                "meeting_user/74": {
                    "about_me": "I am hairy",
                    "vote_weight": "1.000001",
                },
                "meeting_user/105": {
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
                "meeting_ids": [1, 4, 7, 10],
                "committee_ids": [60, 66, 69],
                "organization_id": 1,
                "default_password": "user2",
                "meeting_user_ids": [12, 42, 106, 107],
                "password": password,
                "pronoun": "he",
                "first_name": "Nick",
                "is_active": False,
                "can_change_own_password": True,
                "gender_id": 1,
                "email": "nick.everything@rob.banks",
                "is_present_in_meeting_ids": [7, 10],
                "committee_management_ids": [60, 69],
                "last_email_sent": datetime.fromtimestamp(123456789, ZoneInfo("UTC")),
                "home_committee_id": 60,
                "title": None,
                "last_name": None,
                "default_vote_weight": Decimal(1),
                "member_number": None,
                "is_physical_person": True,
                "external": None,
            },
        )
        for id_ in range(3, 7):
            self.assert_model_not_exists(f"user/{id_}")
        for id_ in [43, 73, 14, 44, 74, 15, 105]:
            self.assert_model_not_exists(f"meeting_user/{id_}")

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
            "meeting_user/42",
            {
                "user_id": 2,
                "meeting_id": 4,
                "number": "num?",
                "vote_weight": Decimal("2"),
                "comment": "Comment 1",
            },
        )
        self.assert_model_exists(
            "meeting_user/106",
            {
                "user_id": 2,
                "meeting_id": 7,
                "about_me": "I have a long beard",
                "vote_weight": Decimal("1.234567"),
            },
        )
        self.assert_model_exists(
            "meeting_user/107",
            {
                "user_id": 2,
                "meeting_id": 10,
                "comment": "This is a comment",
            },
        )

        self.assert_model_exists(
            "meeting/1", {"meeting_user_ids": [12], "user_ids": [2]}
        )
        self.assert_model_exists(
            "meeting/4",
            {"meeting_user_ids": [42], "user_ids": [2]},
        )
        self.assert_model_exists(
            "meeting/7",
            {"meeting_user_ids": [106], "user_ids": [2], "present_user_ids": [2]},
        )
        self.assert_model_exists(
            "meeting/10",
            {"meeting_user_ids": [107], "user_ids": [2], "present_user_ids": [2]},
        )
        self.assert_model_exists("committee/60", {"user_ids": [2], "manager_ids": [2]})
        self.assert_model_exists("committee/66", {"user_ids": [2]})
        self.assert_model_exists("committee/69", {"user_ids": [2], "manager_ids": [2]})

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
                "gender_id": 2,
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
                "gender_id": 2,
                "email": "user.in@this.organization",
                "is_active": False,
                "is_physical_person": None,
                "default_vote_weight": Decimal("0.424242"),
            },
        )
        self.assert_model_exists(
            "gender/2",
            {"id": 2, "name": "female", "user_ids": [2], "organization_id": 1},
        )

    def test_gender_not_changed(self) -> None:
        self.setup_complex_user_fields()
        response = self.request(
            "user.merge_together",
            {
                "id": 3,
                "user_ids": [2, 4, 5, 6],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "user/3",
            {"gender_id": None, "external": True, "home_committee_id": None},
        )
        self.assert_model_exists(
            "gender/1",
            {
                "user_ids": None,
            },
        )
        self.assert_model_exists("committee/60", {"native_user_ids": None})

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
                "gender_id": 2,
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
                "gender_id": 2,
                "email": "user.in@this.organization",
                "is_active": False,
                "is_physical_person": True,
                "default_vote_weight": Decimal("0.424242"),
            },
        )

    def test_with_multiple_delegations(self) -> None:
        self.set_models(
            {
                "meeting_user/15": {"vote_delegated_to_id": 14},
                "meeting_user/14": {"vote_delegations_from_ids": [15]},
                "meeting_user/43": {"vote_delegated_to_id": 44},
                "meeting_user/44": {"vote_delegations_from_ids": [43]},
                "meeting_user/73": {"vote_delegations_from_ids": [74]},
                "meeting_user/74": {"vote_delegated_to_id": 73},
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [4]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("meeting_user/12", {"vote_delegations_from_ids": [15]})
        self.assert_model_exists("meeting_user/42", {"vote_delegations_from_ids": [43]})
        self.assert_model_exists("meeting_user/106", {"vote_delegated_to_id": 73})

    def set_up_polls_for_merge(self) -> None:
        self.set_models(
            {
                "meeting/1": {"present_user_ids": [2, 4]},
                "meeting/4": {"present_user_ids": [3, 4]},
                "meeting/7": {"present_user_ids": [2, 3, 4]},
                "meeting/10": {"present_user_ids": [5]},
                "meeting_user/15": {"vote_delegated_to_id": 14},
                "meeting_user/43": {"motion_submitter_ids": [1]},
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
                    "meeting_id": 4,
                },
                "motion_submitter/1": {
                    "id": 1,
                    "weight": 1,
                    "motion_id": 1,
                    "meeting_id": 4,
                    "meeting_user_id": 43,
                },
                "topic/1": {
                    "id": 1,
                    "title": "Topic 1",
                    "meeting_id": 7,
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
                    "meeting_id": 4,
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
                    "meeting_id": 7,
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
                "meeting_ids": [1, 4, 7],
                "committee_ids": [60, 66],
                "organization_id": 1,
                "default_password": "user2",
                "meeting_user_ids": [12, 42, 106 + add_to_creatable_ids],
                "password": password,
                "poll_candidate_ids": [2, 3],
                "option_ids": [1, 8],
                "poll_voted_ids": [1, 2, 5, 6],
                "vote_ids": [1, 3, 4],
                "delegated_vote_ids": [1, 2, 3, 4],
            },
        )
        self.assert_model_exists("committee/60", {"user_ids": [2, 5]})
        self.assert_model_exists("committee/66", {"user_ids": [2]})
        for id_ in range(3, 5):
            self.assert_model_not_exists(f"user/{id_}")
        for id_ in [43, 73, 14, 44, 74, *range(106, 106 + add_to_creatable_ids)]:
            self.assert_model_not_exists(f"meeting_user/{id_}")
        for meeting_id, id_ in {1: 12, 2: 42, 3: 106 + add_to_creatable_ids}.items():
            self.assert_model_exists(
                f"meeting_user/{id_}", {"user_id": 2, "meeting_id": meeting_id}
            )
        self.assert_model_exists(
            "meeting_user/42",
            {"user_id": 2, "meeting_id": 4, "motion_submitter_ids": [2]},
        )
        self.assert_model_not_exists("motion_submitter/1")
        self.assert_model_exists(
            "motion_submitter/2",
            {"motion_id": 1, "meeting_user_id": 42, "meeting_id": 4, "weight": 1},
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
            ],
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
                    "voted_ids": None,
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

    def create_assignment_or_motion_models_for_meetings(
        self,
        data: dict[str, Any],
        collection: Literal["assignment", "motion"],
        sub_collection: str,
        meeting_user_id_lists_per_meeting_id: dict[int, list[list[int]]],
    ) -> None:
        """
        For each meeting_user_ids list creates an instance of the given `collection`
        and a list_of_speakers for it.
        Then for each meeting_user updates `data` with an instance of `sub_collection`.
        """
        next_model_id = 1
        next_sub_model_id = 1
        for (
            meeting_id,
            meeting_user_id_lists,
        ) in meeting_user_id_lists_per_meeting_id.items():
            for meeting_user_id_list in meeting_user_id_lists:
                if collection == "motion":
                    self.create_motion(meeting_id, next_model_id)
                else:
                    self.create_assignment(next_model_id, meeting_id)
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
                    next_sub_model_id += 1
                    weight += 1
                next_model_id += 1

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
        supposed to have been deleted
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
                    self.assert_model_not_exists(sub_model_fqid)
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
        self.create_assignment_or_motion_models_for_meetings(
            data,
            collection,
            sub_collection,
            {
                1: [
                    [12, 15],
                    [15, 14],
                    [14, 12],
                    [12, 14, 15],
                    [14, 12, 15],
                    [15, 14, 12],
                ],
                4: [[44, 42, 43]],
                7: [[74, 73], [73]],
                10: [[105]],
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
            4: {
                16: None,
                17: (7, 42, 1),
                18: None,
            },
            7: {
                19: None,
                20: (8, 106, 1),
                21: (9, 106, 1),
            },
            10: {
                22: (10, 105, 1),
            },
        }
        self.assert_assignment_or_motion_model_test_was_correct(
            collection, sub_collection, back_relation, expected
        )

    def base_deep_copy_create_motion_test(
        self, sub_collection: str, back_relation: CollectionField
    ) -> None:
        self.set_models(self.get_deep_create_base_data(sub_collection))
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_deep_create_base_test(response, sub_collection, back_relation)

    def get_deep_create_base_data(self, sub_collection: str) -> dict[str, Any]:
        data: dict[str, Any] = {}
        self.create_assignment_or_motion_models_for_meetings(
            data,
            "motion",
            sub_collection,
            {
                1: [
                    [12, 15],
                    [15, 14],
                    [14, 12],
                    [12, 14, 15],
                    [14, 12, 15],
                    [15, 14, 12],
                ],
                4: [[44, 42, 43]],
                7: [[74], [73]],
                10: [[105]],
            },
        )
        return data

    def assert_deep_create_base_test(
        self,
        response: Response,
        sub_collection: str,
        back_relation: CollectionField,
    ) -> None:
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
            4: {
                16: None,
                17: (7, 42, 1),
                18: None,
            },
            7: {
                19: None,
                20: None,
                23: (9, 106, 1),  # created to replace 20
                24: (8, 106, 1),  # created to replace 19
            },
            10: {
                21: (10, 105, 1),
            },
        }
        self.assert_assignment_or_motion_model_test_was_correct(
            "motion", sub_collection, back_relation, expected
        )

    def test_merge_with_assignment_candidates(self) -> None:
        self.base_assignment_or_motion_model_test("assignment", "assignment_candidate")
        self.assert_history_information(
            "user/2", ["Updated with data from {} and {}", "user/3", "user/4"]
        )
        for id_ in range(2, 10):
            self.assert_history_information(f"assignment/{id_}", ["Candidates merged"])

    def test_merge_with_assignment_candidates_in_finished_assignment(self) -> None:
        self.create_assignment(11, 1, {"phase": "finished"})
        self.set_models(
            {
                "assignment_candidate/112": {
                    "meeting_id": 1,
                    "assignment_id": 11,
                    "meeting_user_id": 12,
                },
                "assignment_candidate/114": {
                    "meeting_id": 1,
                    "assignment_id": 11,
                    "meeting_user_id": 14,
                },
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [4]})
        self.assert_status_code(response, 200)

    def test_merge_with_motion_working_group_speakers(self) -> None:
        self.base_deep_copy_create_motion_test(
            "motion_working_group_speaker", "working_group_speaker_ids"
        )

    def test_merge_with_motion_editor(self) -> None:
        self.base_deep_copy_create_motion_test("motion_editor", "editor_ids")

    def test_merge_with_motion_submitters_and_supporters(
        self,
    ) -> None:
        self.set_models(self.get_deep_create_base_data("motion_submitter"))
        supporter_ids_per_motion: dict[int, list[int]] = {
            # meeting/1
            1: [14],
            2: [12],
            3: [15],
            4: [12, 14],
            5: [14, 15],
            # meeting/4
            7: [43, 44],
            # meeting/7
            8: [73],
            9: [74],
            # meeting/10
            10: [105],
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
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_deep_create_base_test(response, "motion_submitter", "submitter_ids")

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
            42: get_motions(42, 43, 44),
            106: get_motions(73, 74),
            105: motion_ids_per_supporter[105],
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
        self.assert_model_exists("motion/5", {"supporter_meeting_user_ids": [12, 15]})
        self.assert_model_exists("motion/7", {"supporter_meeting_user_ids": [42]})
        for motion_id in [8, 9]:
            self.assert_model_exists(
                f"motion/{motion_id}", {"supporter_meeting_user_ids": [106]}
            )
        self.assert_model_exists("motion/10", {"supporter_meeting_user_ids": [105]})
        for id_ in range(2, 10):
            self.assert_history_information(f"motion/{id_}", ["Submitters merged"])

    def test_merge_with_personal_notes(self) -> None:
        # create personal notes, motions, and meetings
        meeting_ids = list(range(1, 8, 3))
        for meeting_id in meeting_ids:
            self.create_meeting(meeting_id)

        map_motion_id_to_meeting_id = {
            motion_id: meeting_id
            for meeting_id in meeting_ids
            for motion_id in list(
                range(
                    int((meeting_id - 1) / 3) * 2 + 1, int((meeting_id - 1) / 3) * 2 + 3
                )
            )
        }
        for motion_id, meeting_id in map_motion_id_to_meeting_id.items():
            self.create_motion(meeting_id, motion_id)

        def add_personal_note(
            id_: int,
            motion_id: int,
            meeting_user_id: int,
            note: str | None = None,
            star: bool | None = None,
        ) -> None:
            motion_fqid = f"motion/{motion_id}"
            meeting_id = map_motion_id_to_meeting_id[motion_id]
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

        data: dict[str, dict[str, Any]] = {}

        add_personal_note(1, 1, 12, "User 2's note")
        add_personal_note(2, 1, 14, "User 4's note", True)
        add_personal_note(3, 1, 15, "User 5's note")

        add_personal_note(4, 2, 14, star=True)

        add_personal_note(5, 3, 44, star=True)
        add_personal_note(6, 3, 42, "", star=False)
        add_personal_note(7, 3, 43, "User 3's note")

        add_personal_note(8, 4, 43, star=False)
        add_personal_note(9, 4, 44, star=True)

        add_personal_note(10, 5, 43, "User 3's note")

        add_personal_note(11, 6, 44, "User 4's note", star=False)
        add_personal_note(12, 6, 43, "User 3's other note")
        self.set_models(data)

        # merge users 3 and 4 into 2
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4]})
        self.assert_status_code(response, 200)

        # check results
        for note_id in [2, 5, 7, 8, 9, 10, 11, 12]:
            self.assert_model_not_exists(f"personal_note/{note_id}")
        self.assert_model_exists("personal_note/3")

        meeting_user_by_meeting_id = {1: 12, 4: 42, 7: 106}
        note_base_data_by_motion_id = {
            motion_id: {
                "meeting_id": meeting_id,
                "meeting_user_id": meeting_user_by_meeting_id[meeting_id],
                "content_object_id": f"motion/{motion_id}",
            }
            for motion_id, meeting_id in map_motion_id_to_meeting_id.items()
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
                }
                for meeting_user_id, message in messages:
                    data[f"chat_message/{next_message_id}"] = {
                        "content": message,
                        "created": datetime.fromtimestamp(
                            next_message_id - first_message_id, ZoneInfo("UTC")
                        ),
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
            7,
            {
                3: (
                    "Serious conversation",
                    [
                        (74, "Could someone change the current projection?"),
                        (73, "I'll do it!"),
                        (74, "Thanks."),
                    ],
                )
            },
            next_id,
        )
        create_chat_messages(
            data,
            4,
            {
                4: (
                    "Announcements",
                    [(43, "Lunch will be served soon."), (44, "Lunch is served.")],
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
            "meeting_user/42",
            {"chat_message_ids": [14, 15], "user_id": 2, "meeting_id": 4},
        )
        self.assert_model_exists(
            "meeting_user/106",
            {"chat_message_ids": [11, 12, 13], "user_id": 2, "meeting_id": 7},
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
            (14, 42, "Lunch will be served soon."),
            (15, 42, "Lunch is served."),
            # meeting 3
            (11, 106, "Could someone change the current projection?"),
            (12, 106, "I'll do it!"),
            (13, 106, "Thanks."),
        ]:
            fqid = f"chat_message/{message_id}"
            assert (date := data[fqid])["content"] == message
            self.assert_model_exists(fqid, {**date, "meeting_user_id": meeting_user_id})

    def test_merge_on_group_and_structure_level_ids(self) -> None:
        setup_data = [
            {"tall": [12, 15, 14], "small": [15]},
            {"thin": [42], "fat": [43, 44]},
            {"smart": [73], "dumb": [74]},
        ]
        meeting_id = 1
        structure_level_id = 1
        data: dict[str, dict[str, Any]] = dict()
        structure_level_ids_per_meeting_user = defaultdict(list)
        for structure_levels in setup_data:
            structure_level_ids = []
            for name, meeting_user_ids in structure_levels.items():
                structure_level_ids.append(structure_level_id)
                for meeting_user_id in meeting_user_ids:
                    structure_level_ids_per_meeting_user[meeting_user_id].append(
                        structure_level_id
                    )
                data[f"structure_level/{structure_level_id}"] = {
                    "id": structure_level_id,
                    "name": name,
                    "meeting_id": meeting_id,
                }
                structure_level_id += 1
            meeting_id += 3
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
            "meeting_user/42", {"structure_level_ids": [3, 4], "group_ids": [4, 5]}
        )
        self.assert_model_exists(
            "meeting_user/106", {"structure_level_ids": [5, 6], "group_ids": [8, 9]}
        )

        self.assert_model_exists("structure_level/1", {"meeting_user_ids": [12, 15]})
        self.assert_model_exists("structure_level/2", {"meeting_user_ids": [15]})
        self.assert_model_exists("structure_level/3", {"meeting_user_ids": [42]})
        self.assert_model_exists("structure_level/4", {"meeting_user_ids": [42]})
        self.assert_model_exists("structure_level/5", {"meeting_user_ids": [106]})
        self.assert_model_exists("structure_level/6", {"meeting_user_ids": [106]})

        self.assert_model_exists("group/1", {"meeting_user_ids": [12]})
        self.assert_model_exists("group/2", {"meeting_user_ids": [12, 15]})
        self.assert_model_exists("group/4", {"meeting_user_ids": [42]})
        self.assert_model_exists("group/5", {"meeting_user_ids": [42]})
        self.assert_model_exists("group/8", {"meeting_user_ids": [106]})
        self.assert_model_exists("group/9", {"meeting_user_ids": [106]})

    def create_speakers_for_test(
        self, allow_multiple_speakers: bool = False
    ) -> dict[str, Any]:
        data: dict[str, dict[str, Any]] = {
            "meeting/1": {
                "list_of_speakers_enable_pro_contra_speech": True,
                "list_of_speakers_enable_interposed_question": True,
                "list_of_speakers_intervention_time": 30,
            },
            "meeting/7": {
                "list_of_speakers_enable_point_of_order_speakers": True,
                "list_of_speakers_enable_point_of_order_categories": True,
            },
            "structure_level/1": {"name": "A", "meeting_id": 1},
            "structure_level/4": {"name": "B", "meeting_id": 1},
            "structure_level/7": {"name": "A", "meeting_id": 7},
            "structure_level/10": {"name": "B", "meeting_id": 7},
            "point_of_order_category/1": {
                "text": "A",
                "rank": 1,
                "meeting_id": 1,
            },
            "point_of_order_category/2": {
                "text": "B",
                "rank": 2,
                "meeting_id": 1,
            },
            "point_of_order_category/3": {
                "text": "A",
                "rank": 1,
                "meeting_id": 7,
            },
            "point_of_order_category/4": {
                "text": "B",
                "rank": 2,
                "meeting_id": 7,
            },
        }
        if allow_multiple_speakers:
            for id_ in [1, 7]:
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
            data.update(
                {
                    block_fqid: {
                        "title": f"MB{base_id}",
                        "meeting_id": meeting_id,
                        "list_of_speakers_id": base_id,
                        "sequential_number": base_id,
                    },
                    f"list_of_speakers/{base_id}": {
                        "content_object_id": block_fqid,
                        "meeting_id": meeting_id,
                        "sequential_number": base_id,
                    },
                    f"structure_level_list_of_speakers/{base_id * 2 - 1}": {
                        "structure_level_id": meeting_id,
                        "list_of_speakers_id": base_id,
                        "initial_time": 5,
                        "remaining_time": 5,
                        "meeting_id": 1,
                    },
                    f"structure_level_list_of_speakers/{base_id * 2}": {
                        "structure_level_id": meeting_id + 3,
                        "list_of_speakers_id": base_id,
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
                if structure_level_id:
                    structure_level_list_of_speakers_id = base_id * 2 - (
                        structure_level_id % 2
                    )
                    speaker_data["structure_level_list_of_speakers_id"] = (
                        structure_level_list_of_speakers_id
                    )
                data[f"speaker/{next_speaker_id}"] = speaker_data
                next_speaker_id += 1
            return next_speaker_id

        # meeting_user_id, weight, speech_state, point_of_order, point_of_order_category_id, structure_level_id
        finished_data = {
            "begin_time": datetime.fromtimestamp(1, ZoneInfo("UTC")),
            "end_time": datetime.fromtimestamp(5, ZoneInfo("UTC")),
        }
        finished_with_pause_data = {**finished_data, "total_pause": 2}
        next_id = add_list_of_speakers(
            1,
            1,
            [
                (12, 1, None, None, None, 1, {}),
                (14, 2, None, True, None, 4, {}),  # to merge
                (14, 5, None, None, None, 1, {}),  # to merge
                (15, 4, None, None, None, 4, {}),
                (12, 3, None, True, None, 4, {}),
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
            7,
            [
                (73, 2, SpeechState.CONTRA, None, None, None, {}),  # to merge into new
                (74, 1, SpeechState.CONTRA, None, None, None, {}),  # to merge into new
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
            self.assert_model_not_exists(f"speaker/{id_}")
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
        for m_user_id, speaker_ids in {12: [10, 12, 23], 106: [15]}.items():
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
        self.assert_model_exists("meeting_user/106", {"speaker_ids": [27]})

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
                self.assert_model_not_exists(f"speaker/{id_}")
            else:
                self.assert_model_exists(f"speaker/{id_}", data[f"speaker/{id_}"])
        next_id = 24
        for m_user_id, speaker_ids in {
            12: replaced_meeting_1,
            106: replaced_meeting_3,
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
            "meeting_user/106",
            {
                "speaker_ids": list(
                    range(24 + len(replaced_meeting_1), 26 + len(replaced_meeting_1))
                )
            },
        )

    def test_with_running_speaker(self) -> None:
        self.create_speakers_for_test()
        self.set_models(
            {"speaker/5": {"begin_time": datetime.fromtimestamp(1, ZoneInfo("UTC"))}}
        )

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
                **{
                    f"meeting/{id_}": {
                        "is_archived_in_organization_id": ONE_ORGANIZATION_ID,
                        "is_active_in_organization_id": None,
                    }
                    for id_ in range(1, 11, 3)
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
        self.assert_model_exists("user/2", {"meeting_user_ids": [12, 42, 106]})
        self.assert_model_exists("user/4", {"meeting_user_ids": [14, 44, 74, 107]})
        self.assert_model_not_exists("user/3")
        self.assert_model_not_exists("user/5")
        self.assert_model_not_exists("user/6")

        self.assert_model_exists("meeting_user/12", {"meeting_id": 1})
        self.assert_model_exists("meeting_user/42", {"meeting_id": 4})
        self.assert_model_exists("meeting_user/106", {"meeting_id": 7})
        self.assert_model_exists("meeting_user/14", {"meeting_id": 1})
        self.assert_model_exists("meeting_user/44", {"meeting_id": 4})
        self.assert_model_exists("meeting_user/74", {"meeting_id": 7})
        self.assert_model_exists("meeting_user/107", {"meeting_id": 10})
        for id_ in [43, 73, 15, 105]:
            self.assert_model_not_exists(f"meeting_user/{id_}")

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
        self.set_models({"user/7": {"can_change_own_password": True}})
        response = self.request("user.merge_together", {"id": 6, "user_ids": [7]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/6", {"can_change_own_password": True})
        self.assert_model_not_exists("user/7")

    def test_merge_only_update_meeting_users(self) -> None:
        response = self.request("user.merge_together", {"id": 4, "user_ids": [3]})
        self.assert_status_code(response, 200)

    def test_merge_with_motion_submitter_transfer(
        self,
    ) -> None:
        data: dict[str, Any] = {}
        self.create_assignment_or_motion_models_for_meetings(
            data,
            "motion",
            "motion_submitter",
            {7: [[73]]},
        )
        self.set_models(data)
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3]})
        self.assert_status_code(response, 200)
        expected: dict[int, dict[int, tuple[int, int, int] | None]] = {
            # meeting_id:sub_model_id:(model_id, meeting_user_id, weight) | None if deleted
            7: {
                1: None,
                2: (1, 106, 1),
            },
        }
        self.assert_assignment_or_motion_model_test_was_correct(
            "motion", "motion_submitter", "submitter_ids", expected
        )

    def test_merge_with_presence(self) -> None:
        self.set_models(
            {
                "meeting/4": {"present_user_ids": [3]},
                "meeting/7": {"present_user_ids": [3]},
                "meeting/10": {"present_user_ids": [5]},
            }
        )
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4, 5]})
        self.assert_status_code(response, 200)
        self.assert_model_exists("user/2", {"is_present_in_meeting_ids": [7, 10]})

    def test_merge_with_locked_out(self) -> None:
        self.set_models(
            {
                "meeting_user/12": {"locked_out": True, "group_ids": [2]},
                "meeting_user/14": {"group_ids": [2]},
                "meeting_user/15": {"group_ids": [2]},
                "meeting_user/42": {"group_ids": [5]},
                "meeting_user/43": {"locked_out": True, "group_ids": [5]},
                "meeting_user/44": {"group_ids": [5]},
                "meeting_user/73": {"group_ids": [8]},
                "meeting_user/74": {"locked_out": True, "group_ids": [8]},
                "meeting_user/105": {"locked_out": True, "group_ids": [11]},
                "group/2": {"meeting_user_ids": [12, 14, 15]},
                "group/5": {"meeting_user_ids": [42, 43, 44]},
                "group/8": {"meeting_user_ids": [73, 74]},
                "group/11": {"meeting_user_ids": [105]},
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
            "meeting_user/42", {"user_id": 2, "meeting_id": 4, "locked_out": None}
        )
        self.assert_model_exists(
            "meeting_user/106", {"user_id": 2, "meeting_id": 7, "locked_out": None}
        )
        self.assert_model_exists(
            "meeting_user/107", {"user_id": 2, "meeting_id": 10, "locked_out": True}
        )

    def test_merge_with_locked_out_meetingadmin_error(self) -> None:
        self.set_models(
            {
                "meeting_user/12": {"locked_out": True, "group_ids": [2]},
                "meeting_user/14": {"group_ids": [2]},
                "meeting_user/15": {"group_ids": [2]},
                "meeting_user/42": {"group_ids": [5]},
                "meeting_user/43": {"locked_out": True, "group_ids": [5]},
                "meeting_user/44": {"group_ids": [4]},
                "meeting_user/73": {"group_ids": [8]},
                "meeting_user/74": {"locked_out": True, "group_ids": [8]},
                "meeting_user/105": {"locked_out": True, "group_ids": [10]},
                "group/2": {"meeting_user_ids": [12, 14, 15]},
                "group/4": {"meeting_user_ids": [44]},
                "group/5": {"meeting_user_ids": [42, 43]},
                "group/8": {"meeting_user_ids": [73, 74]},
                "group/10": {"meeting_user_ids": [105]},
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
                "meeting_user/42": {"locked_out": True, "group_ids": [5]},
                "meeting_user/43": {"group_ids": [5]},
                "meeting_user/44": {"group_ids": [5]},
                "meeting_user/73": {"locked_out": True, "group_ids": [8]},
                "meeting_user/74": {"group_ids": [8]},
                "meeting_user/105": {"group_ids": [11]},
                "group/2": {"meeting_user_ids": [12, 14, 15]},
                "group/5": {"meeting_user_ids": [42, 43, 44]},
                "group/8": {"meeting_user_ids": [73, 74]},
                "group/11": {"meeting_user_ids": [105]},
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
            "Cannot give OrganizationManagementLevel superadmin to user 2 as he is locked out of meeting(s) 4, 7",
            response.json["message"],
        )

    def test_merge_with_locked_out_committee_admin_error(self) -> None:
        self.set_models(
            {
                "meeting_user/12": {"locked_out": True, "group_ids": [2]},
                "meeting_user/14": {"group_ids": [2]},
                "meeting_user/15": {"group_ids": [2]},
                "meeting_user/42": {"group_ids": [5]},
                "meeting_user/43": {"group_ids": [5]},
                "meeting_user/44": {"group_ids": [5]},
                "meeting_user/73": {"locked_out": True, "group_ids": [8]},
                "meeting_user/74": {"group_ids": [8]},
                "meeting_user/105": {"group_ids": [11]},
                "group/2": {"meeting_user_ids": [12, 14, 15]},
                "group/5": {"meeting_user_ids": [42, 43, 44]},
                "group/8": {"meeting_user_ids": [73, 74]},
                "group/11": {"meeting_user_ids": [105]},
                **{
                    f"group/{id_}": {"meeting_user_ids": None}
                    for id_ in [1, 3, 4, 6, 7, 9, 10, 12]
                },
            }
        )
        self.set_committee_management_level([60, 69], 5)
        response = self.request("user.merge_together", {"id": 2, "user_ids": [3, 4, 5]})
        self.assert_status_code(response, 400)
        self.assertIn(
            "Cannot set user 2 as manager for committee(s) 60 due to being locked out of meeting(s) 1",
            response.json["message"],
        )
