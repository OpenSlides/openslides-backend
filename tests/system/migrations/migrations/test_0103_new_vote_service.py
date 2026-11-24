from collections import defaultdict
from decimal import Decimal
from json import dumps
from typing import Any, Literal

from psycopg.types.json import Jsonb

from openslides_backend.action.util.crypto import get_random_string
from openslides_backend.migrations.migration_helper import MigrationState
from openslides_backend.services.postgresql.db_connection_handling import os_conn_pool
from openslides_backend.shared.exceptions import BadCodingException
from openslides_backend.shared.filters import FilterOperator
from openslides_backend.shared.patterns import FullQualifiedId
from openslides_backend.shared.typing import ModelMap, PartialModel
from tests.system.migrations.base_migration_test import BaseMigrationTestCase


class TestMigration103(BaseMigrationTestCase):
    migration_number = 103

    @staticmethod
    def _get_meeting_data(
        base: int = 1, extra_data: dict[FullQualifiedId, PartialModel] | None = None
    ) -> dict[FullQualifiedId, PartialModel]:
        result: dict[FullQualifiedId, PartialModel] = {}
        extra_data = extra_data or {}
        result.update(
            {
                **({"committee/60": {"name": "Committee 60"}} if base == 1 else {}),
                f"meeting/{base}": {
                    "default_group_id": base,
                    "admin_group_id": base + 1,
                    "motions_default_workflow_id": base,
                    "motions_default_amendment_workflow_id": base,
                    "reference_projector_id": base,
                    "committee_id": 60,
                    "is_active_in_organization_id": 1,
                    "language": "en",
                },
                f"projector/{base}": {
                    "meeting_id": base,
                    "name": f"Projector {base}",
                    **{
                        f"used_as_default_projector_for_{option}_in_meeting_id": base
                        for option in (
                            "agenda_item_list",
                            "topic",
                            "list_of_speakers",
                            "current_los",
                            "motion",
                            "amendment",
                            "motion_block",
                            "assignment",
                            "mediafile",
                            "message",
                            "countdown",
                            "assignment_poll",
                            "motion_poll",
                            "poll",
                        )
                    },
                },
                f"group/{base}": {"meeting_id": base, "name": f"group{base}"},
                f"group/{base+1}": {"meeting_id": base, "name": f"group{base+1}"},
                f"group/{base+2}": {"meeting_id": base, "name": f"group{base+2}"},
                f"motion_workflow/{base}": {
                    "name": "flo",
                    "meeting_id": base,
                    "first_state_id": base,
                },
                f"motion_state/{base}": {
                    "name": "stasis",
                    "weight": 36,
                    "meeting_id": base,
                    "workflow_id": base,
                },
            }
        )
        for fqid, data in extra_data.items():
            if fqid in result:
                result[fqid].update(data)
            else:
                result[fqid] = data
        return result

    @staticmethod
    def _get_poll_data(
        poll_id: int,
        content_object_id: str,
        pollmethod: Literal["Y", "YN", "YNA", "N"] = "N",
        onehundred_percent_base: (
            Literal[
                "Y",
                "YN",
                "YNA",
                "N",
                "valid",
                "cast",
                "entitled",
                "entitled_present",
                "disabled",
            ]
            | None
        ) = None,
        type_: Literal["analog", "named", "pseudoanonymous", "cryptographic"] = "named",
        state: Literal["created", "started", "finished", "published"] = "published",
        is_pseudoanonymized: bool = False,
        extra_data: PartialModel = {},
    ) -> dict[FullQualifiedId, PartialModel]:
        return {
            f"poll/{poll_id}": {
                "title": f"Poll {poll_id}",
                "meeting_id": 1,
                "backend": "fast",
                "pollmethod": pollmethod,
                "onehundred_percent_base": onehundred_percent_base
                or ("Y" if content_object_id.startswith("topic/") else "valid"),
                "type": type_,
                "content_object_id": content_object_id,
                "state": state,
                "is_pseudoanonymized": is_pseudoanonymized,
                **extra_data,
            }
        }

    @staticmethod
    def _get_motion_data(
        base: int = 1,
        meeting_id: int = 1,
        motion_data: PartialModel = {},
    ) -> dict[FullQualifiedId, PartialModel]:
        return {
            f"motion/{base}": {
                "title": f"Motion {base}",
                "meeting_id": meeting_id,
                "state_id": meeting_id,
                **motion_data,
            },
            f"list_of_speakers/{base + 100}": {
                "content_object_id": f"motion/{base}",
                "meeting_id": meeting_id,
            },
        }

    @staticmethod
    def _get_assignment_data(
        base: int = 1,
        meeting_id: int = 1,
        assignment_data: PartialModel = {},
    ) -> dict[FullQualifiedId, PartialModel]:
        return {
            f"assignment/{base}": {
                "title": f"Assignment {base}",
                "meeting_id": meeting_id,
                **assignment_data,
            },
            f"list_of_speakers/{base + 200}": {
                "content_object_id": f"assignment/{base}",
                "meeting_id": meeting_id,
            },
        }

    @staticmethod
    def _get_topic_data(
        base: int = 1,
        meeting_id: int = 1,
        topic_data: PartialModel = {},
    ) -> dict[FullQualifiedId, PartialModel]:
        return {
            f"topic/{base}": {
                "title": f"Topic {base}",
                "meeting_id": meeting_id,
                **topic_data,
            },
            f"agenda_item/{base}": {
                "meeting_id": meeting_id,
                "content_object_id": f"topic/{base}",
            },
            f"list_of_speakers/{base + 300}": {
                "content_object_id": f"topic/{base}",
                "meeting_id": meeting_id,
            },
        }

    def _create_users(self, user_ids: list[int]) -> None:
        self.create_entries(
            {f"user/{user_id}": {"username": f"user-{user_id}"} for user_id in user_ids}
        )

    def _create_users_for_meeting(
        self,
        user_ids: list[int],
        group_ids: list[int],
        meeting_id: int = 1,
    ) -> None:
        self._create_users(user_ids)
        self.create_entries(
            {
                f"meeting_user/{meeting_id * 100 + user_id}": {
                    "user_id": user_id,
                    "meeting_id": meeting_id,
                }
                for user_id in user_ids
            },
            {
                "nm_group_meeting_user_ids_meeting_user_t": [
                    {
                        "meeting_user_id": meeting_id * 100 + user_id,
                        "group_id": group_id,
                    }
                    for user_id in user_ids
                    for group_id in group_ids
                ]
            },
        )

    @staticmethod
    def _get_option_data(
        base: int,
        poll_id: int,
        content_object_id: str | None = None,
        text: str | None = None,
        extra_data: PartialModel = {},
    ) -> dict[FullQualifiedId, PartialModel]:
        return {
            f"option/{base}": {
                "poll_id": poll_id,
                "meeting_id": 1,
                "content_object_id": content_object_id,
                "text": text,
                **extra_data,
            }
        }

    @staticmethod
    def _get_vote_data(
        base: int,
        option_id: int,
        value: Literal["Y", "N", "A"],
        user_id: int | None = None,
        delegated_user_id: int | None = None,
        weight: int = 1,
        user_token: str | None = None,
    ) -> dict[FullQualifiedId, PartialModel]:
        if not delegated_user_id:
            delegated_user_id = user_id
        result: dict[str, Any] = {
            f"vote/{base}": {
                "meeting_id": 1,
                "option_id": option_id,
                "value": Jsonb(value) if isinstance(value, dict) else value,
                "weight": Decimal(weight),
                "user_token": user_token
                or (
                    f"pseudo-token-for-{user_id}-{delegated_user_id}"
                    if user_id and delegated_user_id
                    else get_random_string(16)
                ),
            }
        }
        for field_name, field_value in (
            ("user_id", user_id),
            ("delegated_user_id", delegated_user_id),
        ):
            if field_value:
                result[f"vote/{base}"][field_name] = field_value
        return result

    def test_migration_correct(self) -> None:
        """
        Ensures the correct migration of:
            - All types of poll + the related collections
            - meeting_user/vote_delegated_to_id
            - group/permissions
            - meeting_poll_setting
            - renamed fields of meeting and projector
        """
        meeting_data: dict[FullQualifiedId, PartialModel] = self._get_meeting_data(
            1,
            {
                "meeting/1": {
                    "motion_poll_projection_name_order_first": "first_name",
                    "motion_poll_projection_max_columns": 8,
                    "assignment_poll_default_method": "yna",
                    "motion_poll_default_method": "YNA",
                    "poll_default_method": "N",
                    "assignment_poll_default_type": "named",
                    "motion_poll_default_type": "named",
                    "poll_default_type": "analog",
                    "assignment_poll_default_onehundred_percent_base": "YNA",
                    "motion_poll_default_onehundred_percent_base": "valid",
                    "poll_default_onehundred_percent_base": "valid",
                    "assignment_poll_sort_poll_result_by_votes": False,
                    "assignment_poll_enable_max_votes_per_option": True,
                    "poll_sort_poll_result_by_votes": False,
                    "poll_default_live_voting_enabled": True,
                },
                "group/1": {
                    "permissions": ["poll.can_manage"],
                    "used_as_assignment_poll_default_id": 1,
                },
                "group/2": {
                    "permissions": ["poll.can_manage", "motion.can_manage_polls"]
                },
                "group/3": {
                    "permissions": ["motion.can_see", "mediafile.can_see"],
                    "used_as_assignment_poll_default_id": 1,
                    "used_as_motion_poll_default_id": 1,
                    "used_as_topic_poll_default_id": 1,
                },
                "group/4": {"meeting_id": 1, "name": "group4", "permissions": []},
            },
        )

        self.set_up_organization()
        self.create_entries(meeting_data)
        self._create_users_for_meeting([1, 2, 3, 4], [1])
        self._create_users([21, 22, 23])
        self.update_entries(
            {
                "meeting_user/102": {"vote_delegated_to_id": 101},
                "meeting_user/104": {"vote_delegated_to_id": 101},
            }
        )
        polls_data = {
            # Motion
            **self._get_motion_data(1),
            **self._get_poll_data(
                poll_id=1,
                pollmethod="YNA",
                onehundred_percent_base="YNA",
                content_object_id="motion/1",
                extra_data={
                    "votescast": Decimal(2),
                    "votesvalid": Decimal(2),
                    "votesinvalid": Decimal(1),
                    "entitled_users_at_stop": Jsonb(
                        [
                            {
                                "user_id": 1,
                                "voted": True,
                                "present": True,
                                "vote_delegated_to_id": 2,
                            },
                            {
                                "user_id": 2,
                                "voted": True,
                                "present": True,
                            },
                            {
                                "user_id": 3,
                                "voted": False,
                                "present": True,
                            },
                        ]
                    ),
                },
            ),
            **self._get_option_data(1, 1, "motion/1", extra_data={"yes": 1, "no": 1}),
            **self._get_vote_data(1, 1, "Y"),
            **self._get_vote_data(2, 1, "N", 2, 1),
            # Assignment with poll_candidate_list
            **self._get_assignment_data(1),
            **self._get_poll_data(
                poll_id=2,
                pollmethod="YN",
                onehundred_percent_base="YN",
                content_object_id="assignment/1",
                extra_data={
                    "votescast": Decimal(2),
                    "votesvalid": Decimal(2),
                    "entitled_users_at_stop": Jsonb(
                        [
                            {
                                "user_id": 1,
                                "voted": True,
                                "present": True,
                                "vote_delegated_to_id": 2,
                            },
                            {
                                "user_id": 2,
                                "voted": True,
                                "present": True,
                            },
                            {
                                "user_id": 3,
                                "voted": False,
                                "present": False,
                            },
                        ]
                    ),
                },
            ),
            "poll_candidate_list/1": {"meeting_id": 1},
            "poll_candidate/1": {
                "id": 1,
                "weight": 1,
                "user_id": 21,
                "meeting_id": 1,
                "poll_candidate_list_id": 1,
            },
            "poll_candidate/2": {
                "id": 2,
                "weight": 2,
                "user_id": 22,
                "meeting_id": 1,
                "poll_candidate_list_id": 1,
            },
            "poll_candidate/3": {
                "id": 3,
                "weight": 2,
                "user_id": 23,
                "meeting_id": 1,
                "poll_candidate_list_id": 1,
            },
            **self._get_option_data(
                2, 2, "poll_candidate_list/1", extra_data={"yes": 1, "no": 1}
            ),
            **self._get_vote_data(3, 2, "Y"),
            **self._get_vote_data(4, 2, "N", 2, 1),
            # Topic
            **self._get_topic_data(1),
            **self._get_poll_data(
                poll_id=3,
                pollmethod="N",
                onehundred_percent_base="N",
                content_object_id="topic/1",
                extra_data={
                    "min_votes_amount": 1,
                    "max_votes_amount": 3,
                    "global_option_id": 6,
                    "global_yes": True,
                    "votescast": Decimal(3),
                    "votesvalid": Decimal(3),
                    "votesinvalid": Decimal(1),
                    "entitled_users_at_stop": Jsonb(
                        [
                            {
                                "user_id": 1,
                                "voted": True,
                                "present": False,
                                "vote_delegated_to_id": 2,
                            },
                            {
                                "user_id": 2,
                                "voted": True,
                                "present": False,
                            },
                            {
                                "user_id": 3,
                                "voted": True,
                                "present": False,
                            },
                        ]
                    ),
                },
            ),
            **self._get_option_data(3, 3, text="Option 3/1", extra_data={"no": 1}),
            **self._get_option_data(4, 3, text="Option 3/2", extra_data={"no": 0}),
            **self._get_option_data(5, 3, text="Option 3/3", extra_data={"no": 2}),
            **self._get_option_data(6, 3, text="Nota-Option", extra_data={"yes": 1}),
            **self._get_vote_data(5, 3, "N", 2, 1),
            **self._get_vote_data(6, 5, "N", 2, 1),
            **self._get_vote_data(7, 5, "N", 1, 1),
            **self._get_vote_data(8, 6, "Y", 3, 3),
            # Assignment with max_votes_per_option > 1
            **self._get_assignment_data(2),
            **self._get_poll_data(
                poll_id=4,
                pollmethod="Y",
                onehundred_percent_base="cast",
                content_object_id="assignment/2",
                extra_data={
                    "min_votes_amount": 1,
                    "max_votes_amount": 4,
                    "max_votes_per_option": 2,
                    "votescast": Decimal(2),
                    "votesvalid": Decimal(2),
                    "entitled_users_at_stop": Jsonb(
                        [
                            {
                                "user_id": 1,
                                "voted": True,
                                "present": False,
                                "vote_delegated_to_id": 2,
                            },
                            {
                                "user_id": 2,
                                "voted": True,
                                "present": False,
                            },
                            {
                                "user_id": 3,
                                "voted": False,
                                "present": False,
                            },
                        ]
                    ),
                },
            ),
            **self._get_option_data(7, 4, "user/21", extra_data={"yes": 1}),
            **self._get_option_data(8, 4, "user/22", extra_data={"yes": 2}),
            **self._get_option_data(9, 4, "user/23", extra_data={"yes": 2}),
            **self._get_vote_data(9, 7, "Y", 2, 2),
            **self._get_vote_data(10, 8, "Y", 2, 2),
            **self._get_vote_data(11, 9, "Y", 2, 2, 2),
            **self._get_vote_data(12, 8, "Y", 1, 2, 1),
            # Assignment with 'Y'/'N'
            **self._get_assignment_data(3),
            **self._get_poll_data(
                poll_id=5,
                pollmethod="Y",
                onehundred_percent_base="Y",
                content_object_id="assignment/3",
                extra_data={
                    "min_votes_amount": 1,
                    "max_votes_amount": 4,
                    "max_votes_per_option": 1,
                    "global_option_id": 12,
                    "global_no": True,
                    "votescast": Decimal(3),
                    "votesvalid": Decimal(3),
                    "entitled_users_at_stop": Jsonb(
                        [
                            {
                                "user_id": 1,
                                "voted": True,
                                "present": False,
                                "vote_delegated_to_id": 2,
                            },
                            {
                                "user_id": 2,
                                "voted": False,
                                "present": False,
                            },
                            {
                                "user_id": 3,
                                "voted": True,
                            },
                        ]
                    ),
                },
            ),
            **self._get_option_data(10, 5, "user/21", extra_data={"yes": 1}),
            **self._get_option_data(11, 5, "user/22", extra_data={"yes": 2}),
            **self._get_option_data(12, 5, extra_data={"no": 1}),
            **self._get_vote_data(13, 10, "Y", 2, 2),
            **self._get_vote_data(14, 11, "Y", 2, 2),
            **self._get_vote_data(15, 11, "Y", 1, 1),
            **self._get_vote_data(16, 12, "N", 3, 3),
            # Assignment - other
            **self._get_assignment_data(4),
            **self._get_poll_data(
                poll_id=6,
                pollmethod="YNA",
                onehundred_percent_base="entitled",
                content_object_id="assignment/4",
                state="finished",
                extra_data={
                    "min_votes_amount": 1,
                    "max_votes_amount": 4,
                    "global_option_id": 16,
                    "global_abstain": True,
                    "votescast": Decimal(3),
                    "votesvalid": Decimal(3),
                    "entitled_users_at_stop": Jsonb(
                        [
                            {
                                "user_id": 1,
                                "voted": True,
                                "present": True,
                                "vote_delegated_to_id": 2,
                            },
                            {
                                "user_id": 2,
                                "voted": False,
                                "present": False,
                            },
                            {
                                "user_id": 3,
                                "voted": True,
                                "present": True,
                            },
                        ]
                    ),
                },
            ),
            **self._get_option_data(
                13,
                6,
                "user/21",
                extra_data={"yes": 2, "no": 2, "abstain": 0, "weight": Decimal(1)},
            ),
            **self._get_option_data(
                14,
                6,
                "user/22",
                extra_data={"yes": 0, "no": 2, "abstain": 1, "weight": Decimal(1)},
            ),
            **self._get_option_data(
                15,
                6,
                "user/23",
                extra_data={"yes": 0, "no": 0, "abstain": 2, "weight": Decimal(1)},
            ),
            **self._get_option_data(
                16, 6, "user/4", extra_data={"abstain": 1, "weight": Decimal(1)}
            ),
            **self._get_vote_data(17, 13, "Y", 2, 1),
            **self._get_vote_data(18, 14, "N", 2, 1),
            **self._get_vote_data(19, 15, "A", 2, 1),
            **self._get_vote_data(20, 13, "Y", 1, 1),
            **self._get_vote_data(21, 14, "A", 1, 1),
            **self._get_vote_data(22, 15, "A", 1, 1),
            **self._get_vote_data(23, 13, "N", 3, 3),
            **self._get_vote_data(24, 14, "N", 3, 3),
            **self._get_vote_data(25, 13, "N"),
            **self._get_vote_data(26, 16, "A"),
        }

        self.create_entries(polls_data)

        manager = self.create_migration_manager()

        intermediate_result = self.make_migration_request(manager)
        if intermediate_result["status"] == MigrationState.MIGRATION_FAILED:
            raise BadCodingException(
                f"Migration failed with message: {intermediate_result['exception']}."
            )
        self.assertEqual(
            intermediate_result["status"], MigrationState.MIGRATION_RUNNING
        )

        self.wait_for_migration_thread(self.MAX_WAIT)
        result = self.get_stats(manager)["stats"]
        if result["status"] == MigrationState.MIGRATION_FAILED:
            raise BadCodingException(
                f"Migration failed with message: {result['exception']}."
            )
        self.assert_migration_finalized()

        base_poll_fields = {
            "anonymized": False,
            "allow_empty": False,
            "allow_invalid": False,
            "allow_vote_split": False,
        }
        with os_conn_pool.connection() as conn:
            with conn.cursor() as cur:
                for collection, last_value in (
                    ("poll_ballot", 17),
                    ("poll_ballot_user", 26),
                    ("poll_config_approval", 2),
                    ("poll_config_rating_score", 4),
                    ("poll_config_selection", 5),
                    ("poll_config_rating_approval", 6),
                    ("poll_entitled_user", 18),
                    ("poll_option", 18),
                ):
                    self.assert_content_not_none(
                        cur,
                        f"SELECT last_value FROM {collection}_t_id_seq;",
                        {"last_value": last_value},
                    )
                for collection, count in (
                    ("poll_ballot", 17),
                    ("poll_ballot_user", 17),
                    ("poll_config_approval", 2),
                    ("poll_config_rating_score", 1),
                    ("poll_config_selection", 2),
                    ("poll_config_rating_approval", 1),
                    ("poll_entitled_user", 18),
                    ("poll_option", 14),
                ):
                    self.assert_entries_count(cur, collection, count)
        self.check_entries(
            {
                "group": {
                    1: {
                        "permissions": ["agenda_item.can_manage_polls"],
                        "used_in_meeting_poll_setting_ids": [1],
                    },
                    2: {
                        "permissions": [
                            "agenda_item.can_manage_polls",
                            "motion.can_manage_polls",
                        ],
                        "used_in_meeting_poll_setting_ids": [],
                    },
                    3: {
                        "permissions": ["motion.can_see", "mediafile.can_see"],
                        "used_in_meeting_poll_setting_ids": [1, 2, 3],
                    },
                    4: {"permissions": [], "used_in_meeting_poll_setting_ids": []},
                },
                "meeting_user": {
                    101: {
                        "vote_delegated_to_ids": [],
                        "vote_delegations_from_ids": [102, 104],
                    },
                    102: {
                        "vote_delegated_to_ids": [101],
                        "vote_delegations_from_ids": [],
                    },
                    103: {
                        "vote_delegated_to_ids": [],
                        "vote_delegations_from_ids": [],
                    },
                    104: {
                        "vote_delegated_to_ids": [101],
                        "vote_delegations_from_ids": [],
                    },
                },
                "projector": {
                    1: {"used_as_default_projector_for_topic_poll_in_meeting_id": 1}
                },
                "meeting": {
                    1: {
                        "poll_projection_name_order_first": "first_name",
                        "poll_projection_max_columns": 8,
                        "default_projector_topic_poll_ids": [1],
                        "poll_setting_ids": [1, 2, 3],
                        "assignment_poll_config_id": 1,
                        "motion_poll_config_id": 2,
                        "topic_poll_config_id": 3,
                    }
                },
                "meeting_poll_setting": {
                    1: {
                        "enable_live_voting": True,
                        "allow_live_voting": True,
                        "sort_result_by_votes": False,
                        "enable_cumulative_voting": True,
                        "method": "rating_approval.yes_no_abstain",
                        "visibility": "open",
                        "onehundred_percent_base": "yes_no_abstain",
                        "group_ids": [1, 3],
                        "used_as_assignment_poll_config_in_meeting_id": 1,
                        "used_as_motion_poll_config_in_meeting_id": None,
                        "used_as_topic_poll_config_in_meeting_id": None,
                        "meeting_id": 1,
                    },
                    2: {
                        "enable_live_voting": True,
                        "allow_live_voting": True,
                        "method": "approval.yes_no_abstain",
                        "visibility": "open",
                        "onehundred_percent_base": "valid",
                        "group_ids": [3],
                        "used_as_assignment_poll_config_in_meeting_id": None,
                        "used_as_motion_poll_config_in_meeting_id": 1,
                        "used_as_topic_poll_config_in_meeting_id": None,
                        "meeting_id": 1,
                    },
                    3: {
                        "enable_live_voting": True,
                        "allow_live_voting": True,
                        "sort_result_by_votes": False,
                        "method": "selection.yes",
                        "visibility": "manually",
                        "onehundred_percent_base": "valid",
                        "group_ids": [3],
                        "used_as_assignment_poll_config_in_meeting_id": None,
                        "used_as_motion_poll_config_in_meeting_id": None,
                        "used_as_topic_poll_config_in_meeting_id": 1,
                        "meeting_id": 1,
                    },
                },
                "poll": {
                    1: {
                        **base_poll_fields,
                        "config_id": "poll_config_approval/1",
                        "content_object_id": "motion/1",
                        "visibility": "open",
                        "state": "finished",
                        "published": True,
                        "result": dumps(
                            {
                                "no": "1.000000",
                                "yes": "1.000000",
                                "total_ballots": 2,
                                "entitled_users": 3,
                                "entitled_users_present": 3,
                            }
                        ),
                        "option_ids": [],
                        "ballot_ids": [14, 15],
                        "ballot_user_ids": [1, 2],
                        "entitled_user_ids": [1, 2, 3],
                    },
                    2: {
                        **base_poll_fields,
                        "config_id": "poll_config_approval/2",
                        "content_object_id": "assignment/1",
                        "visibility": "open",
                        "state": "finished",
                        "published": True,
                        "result": dumps(
                            {
                                "no": "1.000000",
                                "yes": "1.000000",
                                "total_ballots": 2,
                                "entitled_users": 3,
                                "entitled_users_present": 2,
                            }
                        ),
                        "option_ids": [16, 17, 18],
                        "ballot_ids": [16, 17],
                        "ballot_user_ids": [3, 4],
                        "entitled_user_ids": [4, 5, 6],
                    },
                    3: {
                        **base_poll_fields,
                        "config_id": "poll_config_selection/3",
                        "content_object_id": "topic/1",
                        "visibility": "open",
                        "state": "finished",
                        "published": True,
                        "result": dumps(
                            {
                                "nota": "1.000000",
                                "Option 3/1": "1.000000",
                                "Option 3/3": "2.000000",
                                "total_ballots": 3,
                                "entitled_users": 3,
                                "entitled_users_present": 0,
                            }
                        ),
                        "option_ids": [3, 4, 5],
                        "ballot_ids": [1, 2, 3],
                        "ballot_user_ids": [5, 7, 8],
                        "entitled_user_ids": [7, 8, 9],
                    },
                    4: {
                        **base_poll_fields,
                        "config_id": "poll_config_rating_score/4",
                        "content_object_id": "assignment/2",
                        "visibility": "open",
                        "state": "finished",
                        "published": True,
                        "result": dumps(
                            {
                                "7": "1.000000",
                                "8": "2.000000",
                                "9": "2.000000",
                                "total_ballots": 2,
                                "entitled_users": 3,
                                "entitled_users_present": 0,
                            }
                        ),
                        "option_ids": [7, 8, 9],
                        "ballot_ids": [4, 5],
                        "ballot_user_ids": [9, 12],
                        "entitled_user_ids": [10, 11, 12],
                    },
                    5: {
                        **base_poll_fields,
                        "config_id": "poll_config_selection/5",
                        "content_object_id": "assignment/3",
                        "visibility": "open",
                        "state": "finished",
                        "published": True,
                        "result": dumps(
                            {
                                "10": "1.000000",
                                "11": "2.000000",
                                "nota": "1.000000",
                                "total_ballots": 3,
                                "entitled_users": 3,
                                "entitled_users_present": 0,
                            }
                        ),
                        "option_ids": [10, 11],
                        "ballot_ids": [6, 7, 8],
                        "ballot_user_ids": [13, 15, 16],
                        "entitled_user_ids": [13, 14, 15],
                    },
                    6: {
                        **base_poll_fields,
                        "config_id": "poll_config_rating_approval/6",
                        "content_object_id": "assignment/4",
                        "visibility": "open",
                        "state": "finished",
                        "published": False,
                        "result": dumps(
                            {
                                "13": {"no": "2.000000", "yes": "2.000000"},
                                "14": {"no": "2.000000", "abstain": "1.000000"},
                                "15": {"abstain": "2.000000"},
                                "16": {"abstain": "1.000000"},
                                "total_ballots": 3,
                                "entitled_users": 3,
                                "entitled_users_present": 2,
                            }
                        ),
                        "option_ids": [13, 14, 15],
                        "ballot_ids": [9, 10, 11, 12, 13],
                        "ballot_user_ids": [17, 20, 23, 25, 26],
                        "entitled_user_ids": [16, 17, 18],
                    },
                },
                "poll_config_approval": {
                    1: {
                        "poll_id": 1,
                        "allow_abstain": True,
                        "onehundred_percent_base": "yes_no_abstain",
                        "required_majority": "no_majority",
                    },
                    2: {
                        "poll_id": 2,
                        "allow_abstain": False,
                        "onehundred_percent_base": "yes_no",
                        "required_majority": "no_majority",
                    },
                },
                "poll_config_selection": {
                    3: {
                        "poll_id": 3,
                        "min_options_amount": 1,
                        "max_options_amount": 3,
                        "allow_nota": True,
                        "strike_out": True,
                        "onehundred_percent_base": "no_general",
                        "required_majority": "no_majority",
                        "display_chart": "pie",
                    },
                    5: {
                        "poll_id": 5,
                        "min_options_amount": 1,
                        "max_options_amount": 4,
                        "allow_nota": True,
                        "strike_out": False,
                        "onehundred_percent_base": "no_general",
                        "required_majority": "no_majority",
                        "display_chart": None,
                    },
                },
                "poll_config_rating_score": {
                    4: {
                        "poll_id": 4,
                        "min_options_amount": 0,
                        "max_options_amount": 0,
                        "max_votes_per_option": 2,
                        "max_vote_sum": 1,
                        "min_vote_sum": 4,
                        "onehundred_percent_base": "cast",
                        "required_majority": "no_majority",
                    },
                },
                "poll_config_rating_approval": {
                    6: {
                        "poll_id": 6,
                        "min_options_amount": 1,
                        "max_options_amount": 4,
                        "max_yes_amount": None,
                        "allow_abstain": True,
                        "onehundred_percent_base": "entitled",
                        "required_majority": "no_majority",
                    },
                },
                "poll_entitled_user": {
                    1: {"poll_id": 1, "meeting_user_id": 101, "present": True},
                    2: {"poll_id": 1, "meeting_user_id": 102, "present": True},
                    3: {"poll_id": 1, "meeting_user_id": 103, "present": True},
                    4: {"poll_id": 2, "meeting_user_id": 101, "present": True},
                    5: {"poll_id": 2, "meeting_user_id": 102, "present": True},
                    6: {"poll_id": 2, "meeting_user_id": 103, "present": False},
                    7: {"poll_id": 3, "meeting_user_id": 101, "present": False},
                    8: {"poll_id": 3, "meeting_user_id": 102, "present": False},
                    9: {"poll_id": 3, "meeting_user_id": 103, "present": False},
                    10: {"poll_id": 4, "meeting_user_id": 101, "present": False},
                    11: {"poll_id": 4, "meeting_user_id": 102, "present": False},
                    12: {"poll_id": 4, "meeting_user_id": 103, "present": False},
                    13: {"poll_id": 5, "meeting_user_id": 101, "present": False},
                    14: {"poll_id": 5, "meeting_user_id": 102, "present": False},
                    15: {"poll_id": 5, "meeting_user_id": 103, "present": False},
                    16: {"poll_id": 6, "meeting_user_id": 101, "present": True},
                    17: {"poll_id": 6, "meeting_user_id": 102, "present": False},
                    18: {"poll_id": 6, "meeting_user_id": 103, "present": True},
                },
                "poll_option": {
                    16: {
                        "poll_id": 2,
                        "weight": 1,
                        "text": None,
                        "content_object_id": "user/21",
                    },
                    17: {
                        "poll_id": 2,
                        "weight": 2,
                        "text": None,
                        "content_object_id": "user/22",
                    },
                    18: {
                        "poll_id": 2,
                        "weight": 2,
                        "text": None,
                        "content_object_id": "user/23",
                    },
                    3: {
                        "poll_id": 3,
                        "weight": 10000,
                        "text": "Option 3/1",
                        "content_object_id": None,
                    },
                    4: {
                        "poll_id": 3,
                        "weight": 10000,
                        "text": "Option 3/2",
                        "content_object_id": None,
                    },
                    5: {
                        "poll_id": 3,
                        "weight": 10000,
                        "text": "Option 3/3",
                        "content_object_id": None,
                    },
                    7: {
                        "poll_id": 4,
                        "weight": 10000,
                        "text": None,
                        "content_object_id": "user/21",
                    },
                    8: {
                        "poll_id": 4,
                        "weight": 10000,
                        "text": None,
                        "content_object_id": "user/22",
                    },
                    9: {
                        "poll_id": 4,
                        "weight": 10000,
                        "text": None,
                        "content_object_id": "user/23",
                    },
                    10: {
                        "poll_id": 5,
                        "weight": 10000,
                        "text": None,
                        "content_object_id": "user/21",
                    },
                    11: {
                        "poll_id": 5,
                        "weight": 10000,
                        "text": None,
                        "content_object_id": "user/22",
                    },
                    13: {
                        "poll_id": 6,
                        "weight": 1,
                        "text": None,
                        "content_object_id": "user/21",
                    },
                    14: {
                        "poll_id": 6,
                        "weight": 1,
                        "text": None,
                        "content_object_id": "user/22",
                    },
                    15: {
                        "poll_id": 6,
                        "weight": 1,
                        "text": None,
                        "content_object_id": "user/23",
                    },
                },
                "poll_ballot_user": {
                    1: {
                        "poll_id": 1,
                        "poll_ballot_id": 15,
                        "represented_meeting_user_id": None,
                        "acting_meeting_user_id": None,
                    },
                    2: {
                        "poll_id": 1,
                        "poll_ballot_id": 14,
                        "represented_meeting_user_id": 102,
                        "acting_meeting_user_id": 101,
                    },
                    3: {
                        "poll_id": 2,
                        "poll_ballot_id": 17,
                        "represented_meeting_user_id": None,
                        "acting_meeting_user_id": None,
                    },
                    4: {
                        "poll_id": 2,
                        "poll_ballot_id": 16,
                        "represented_meeting_user_id": 102,
                        "acting_meeting_user_id": 101,
                    },
                    5: {
                        "poll_id": 3,
                        "poll_ballot_id": 1,
                        "represented_meeting_user_id": 102,
                        "acting_meeting_user_id": 101,
                    },
                    7: {
                        "poll_id": 3,
                        "poll_ballot_id": 2,
                        "represented_meeting_user_id": 101,
                        "acting_meeting_user_id": 101,
                    },
                    8: {
                        "poll_id": 3,
                        "poll_ballot_id": 3,
                        "represented_meeting_user_id": 103,
                        "acting_meeting_user_id": 103,
                    },
                    9: {
                        "poll_id": 4,
                        "poll_ballot_id": 4,
                        "represented_meeting_user_id": 102,
                        "acting_meeting_user_id": 102,
                    },
                    12: {
                        "poll_id": 4,
                        "poll_ballot_id": 5,
                        "represented_meeting_user_id": 101,
                        "acting_meeting_user_id": 102,
                    },
                    13: {
                        "poll_id": 5,
                        "poll_ballot_id": 6,
                        "represented_meeting_user_id": 102,
                        "acting_meeting_user_id": 102,
                    },
                    15: {
                        "poll_id": 5,
                        "poll_ballot_id": 7,
                        "represented_meeting_user_id": 101,
                        "acting_meeting_user_id": 101,
                    },
                    16: {
                        "poll_id": 5,
                        "poll_ballot_id": 8,
                        "represented_meeting_user_id": 103,
                        "acting_meeting_user_id": 103,
                    },
                    17: {
                        "poll_id": 6,
                        "poll_ballot_id": 12,
                        "represented_meeting_user_id": 102,
                        "acting_meeting_user_id": 101,
                    },
                    20: {
                        "poll_id": 6,
                        "poll_ballot_id": 11,
                        "represented_meeting_user_id": 101,
                        "acting_meeting_user_id": 101,
                    },
                    23: {
                        "poll_id": 6,
                        "poll_ballot_id": 10,
                        "represented_meeting_user_id": 103,
                        "acting_meeting_user_id": 103,
                    },
                    25: {
                        "poll_id": 6,
                        "poll_ballot_id": 9,
                        "represented_meeting_user_id": None,
                        "acting_meeting_user_id": None,
                    },
                    26: {
                        "poll_id": 6,
                        "poll_ballot_id": 13,
                        "represented_meeting_user_id": None,
                        "acting_meeting_user_id": None,
                    },
                },
                "poll_ballot": {
                    15: {
                        "poll_id": 1,
                        "value": "yes",
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 1,
                    },
                    14: {
                        "poll_id": 1,
                        "value": "no",
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 2,
                    },
                    17: {
                        "poll_id": 2,
                        "value": "yes",
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 3,
                    },
                    16: {
                        "poll_id": 2,
                        "value": "no",
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 4,
                    },
                    1: {
                        "poll_id": 3,
                        "value": "3, 5",
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 5,
                    },
                    2: {
                        "poll_id": 3,
                        "value": "5",
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 7,
                    },
                    3: {
                        "poll_id": 3,
                        "value": "nota",
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 8,
                    },
                    4: {
                        "poll_id": 4,
                        "value": dumps(
                            {
                                "7": "1.000000",
                                "8": "1.000000",
                                "9": "2.000000",
                            }
                        ),
                        "weight": Decimal(4),
                        "split": False,
                        "poll_ballot_user_id": 9,
                    },
                    5: {
                        "poll_id": 4,
                        "value": dumps({"8": "1.000000"}),
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 12,
                    },
                    6: {
                        "poll_id": 5,
                        "value": "10, 11",
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 13,
                    },
                    7: {
                        "poll_id": 5,
                        "value": "11",
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 15,
                    },
                    8: {
                        "poll_id": 5,
                        "value": "nota",
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 16,
                    },
                    9: {
                        "poll_id": 6,
                        "value": dumps(
                            {
                                "13": "no",
                            }
                        ),
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 25,
                    },
                    10: {
                        "poll_id": 6,
                        "value": dumps(
                            {
                                "13": "no",
                                "14": "no",
                            }
                        ),
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 23,
                    },
                    11: {
                        "poll_id": 6,
                        "value": dumps(
                            {
                                "13": "yes",
                                "14": "abstain",
                                "15": "abstain",
                            }
                        ),
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 20,
                    },
                    12: {
                        "poll_id": 6,
                        "value": dumps(
                            {
                                "13": "yes",
                                "14": "no",
                                "15": "abstain",
                            }
                        ),
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 17,
                    },
                    13: {
                        "poll_id": 6,
                        "value": dumps(
                            {
                                "16": "abstain",
                            }
                        ),
                        "weight": Decimal(1),
                        "split": False,
                        "poll_ballot_user_id": 26,
                    },
                },
            },
            {"group": ["permissions"]},
        )

    def test_result_and_ballots(self) -> None:
        """
        Ensures the correct migration by migrating and checking 2 polls
        for each special case:
            motion - as single option poll
            topic - as multiple options poll
        Cases:
            1. is_pseudoanonymized: True -> no link between ballot and ballot_user
            2. type: analog -> no ballots, no ballot users, invalid votes in poll/result
            3. state: created -> no poll/result
        """

        self.set_up_organization()
        self.create_entries(self._get_meeting_data())
        self._create_users_for_meeting([1], [1])

        test_data: dict[FullQualifiedId, PartialModel] = {}
        extra_data_dicts: tuple[dict[str, Any], ...] = (
            {"is_pseudoanonymized": True},
            {"type": "analog"},
            {"state": "created"},
        )
        for base, extra_data in enumerate(extra_data_dicts):
            has_votes = base < 2
            # Single option poll
            motion_id = base + 1
            motion_poll_id = base * 2 + 1
            motion_option_id = base * 3 + 1
            test_data.update(
                {
                    **self._get_motion_data(motion_id),
                    **self._get_poll_data(
                        poll_id=motion_poll_id,
                        content_object_id=f"motion/{motion_id}",
                        extra_data={
                            "votesinvalid": Decimal(3),
                            "votescast": Decimal(2),
                            **extra_data,
                        },
                    ),
                    **self._get_option_data(
                        motion_option_id,
                        motion_poll_id,
                        f"motion/{motion_id}",
                        extra_data=({"yes": 1, "no": 1} if has_votes else {}),
                    ),
                }
            )
            if has_votes:
                test_data.update(
                    {
                        **self._get_vote_data(
                            base * 5 + 1, motion_option_id, "Y", 1, 1
                        ),
                        **self._get_vote_data(base * 5 + 2, motion_option_id, "N"),
                    }
                )
            # Multiple options poll
            topic_id = base + 1
            topic_poll_id = base * 2 + 2
            topic_option_id_1 = base * 3 + 2
            topic_option_id_2 = base * 3 + 3
            test_data.update(
                {
                    **self._get_topic_data(topic_id),
                    **self._get_poll_data(
                        poll_id=topic_poll_id,
                        onehundred_percent_base="Y",
                        pollmethod="Y",
                        content_object_id=f"topic/{topic_id}",
                        extra_data={
                            "votesinvalid": Decimal(2),
                            "votescast": Decimal(2),
                            **extra_data,
                        },
                    ),
                    **self._get_option_data(
                        topic_option_id_1,
                        topic_poll_id,
                        text="Option 1",
                        extra_data=({"yes": 1} if has_votes else {}),
                    ),
                    **self._get_option_data(
                        topic_option_id_2,
                        topic_poll_id,
                        text="Option 2",
                        extra_data=({"yes": 2} if has_votes else {}),
                    ),
                }
            )
            if has_votes:
                test_data.update(
                    {
                        **self._get_vote_data(
                            base * 5 + 3, topic_option_id_1, "Y", 1, 1
                        ),
                        **self._get_vote_data(
                            base * 5 + 4, topic_option_id_2, "Y", 1, 1
                        ),
                        **self._get_vote_data(
                            base * 5 + 5,
                            topic_option_id_2,
                            "Y",
                        ),
                    }
                )

        self.create_entries(test_data)

        manager = self.create_migration_manager()
        intermediate_result = self.make_migration_request(manager)
        if intermediate_result["status"] == MigrationState.MIGRATION_FAILED:
            raise BadCodingException(
                f"Migration failed with message: {intermediate_result['exception']}."
            )
        self.wait_for_migration_thread(self.MAX_WAIT)
        self.assert_migration_finalized()

        expected_data: ModelMap = defaultdict(dict)
        for base in range(2):
            poll_data = (
                {}
                if base
                else {
                    "anonymized": True,
                    "visibility": "open" if base == 0 else "secret",
                }
            )
            expected_data["poll"][base * 2 + 1] = {
                **poll_data,
                "option_ids": [],
                "ballot_ids": [] if base else [3, 4],
                "ballot_user_ids": [] if base else [1, 2],
                "result": dumps(
                    {
                        "no": "1.000000",
                        "yes": "1.000000",
                        **({"invalid": 3} if base else {}),
                        "total_ballots": 2,
                        "entitled_users": 0,
                        "entitled_users_present": 0,
                    }
                ),
            }
            expected_data["poll"][base * 2 + 2] = {
                **poll_data,
                "option_ids": [base * 3 + 2, base * 3 + 3],
                "ballot_ids": [] if base else [1, 2],
                "ballot_user_ids": [] if base else [3, 5],
                "result": dumps(
                    {
                        **({"invalid": 2} if base else {}),
                        "Option 1": "1.000000",
                        "Option 2": "2.000000",
                        "total_ballots": 2,
                        "entitled_users": 0,
                        "entitled_users_present": 0,
                    }
                ),
            }
        expected_data["poll"][5] = {
            "option_ids": [],
            "ballot_ids": [],
            "ballot_user_ids": [],
            "result": None,
        }
        expected_data["poll"][6] = {
            "option_ids": [8, 9],
            "ballot_ids": [],
            "ballot_user_ids": [],
            "result": None,
        }
        expected_data["poll_ballot"] = {
            ballot_id: {
                "poll_id": poll_id,
                "value": value,
                "poll_ballot_user_id": None,
            }
            for poll_id, ballot_ids in {
                1: [(3, "no"), (4, "yes")],
                2: [(1, "2, 3"), (2, "3")],
            }.items()
            for ballot_id, value in ballot_ids
        }
        expected_data["poll_ballot_user"] = {
            ballot_user_id: {
                "poll_id": poll_id,
                "acting_meeting_user_id": meeting_user_id,
                "represented_meeting_user_id": meeting_user_id,
                "poll_ballot_id": None,
            }
            for poll_id, ballot_user_ids in {
                1: [(1, 101), (2, None)],
                2: [(3, 101), (5, None)],
            }.items()
            for ballot_user_id, meeting_user_id in ballot_user_ids
        }
        for collection in ["poll_ballot", "poll_ballot_user"]:
            self.assert_entries_not_exist(
                collection, FilterOperator("poll_id", "in", list(range(3, 7)))
            )

        self.check_entries(expected_data)

    def test_poll_meeting_setting(self) -> None:
        """
        Checks that:
            - defaults are set for empty fields
            - defaults are set for fields with incorrect values
            - values are transformed correctly
        """
        methods = (
            (None, None, None),
            ("nya", "Y", "YNA"),
            ("YN", "YN", None),
            ("YNA", "YNA", None),
            ("yna", None, None),
            ("Y", None, None),
            ("N", None, None),
        )
        types = (None, "analog", "named", "pseudoanonymous", "cryptographic")
        onehundred_percent_bases = (None, "Y", "N", "YN", "YNA")

        meetings_data = {}
        for i, method in enumerate(methods):
            extra_data = {
                "assignment_poll_default_method": method[0],
                "motion_poll_default_method": method[1],
                "poll_default_method": method[2],
            }
            if i <= 4:
                for poll_type in ("assignment_", "motion_", ""):
                    extra_data.update(
                        {
                            f"{poll_type}poll_default_type": types[i],
                            f"{poll_type}poll_default_onehundred_percent_base": onehundred_percent_bases[
                                i
                            ],
                        }
                    )
            meetings_data.update(
                self._get_meeting_data(i + 1, {f"meeting/{i + 1}": extra_data})
            )
        self.set_up_organization()
        self.create_entries(meetings_data)
        manager = self.create_migration_manager()
        intermediate_result = self.make_migration_request(manager)
        if intermediate_result["status"] == MigrationState.MIGRATION_FAILED:
            raise BadCodingException(
                f"Migration failed with message: {intermediate_result['exception']}."
            )
        self.wait_for_migration_thread(self.MAX_WAIT)
        self.assert_migration_finalized()

        expected_data = {}
        for i, data in enumerate(
            (
                {},
                {
                    "all": {
                        "visibility": "manually",
                        "onehundred_percent_base": "no_general",
                    }
                },
                {
                    "all": {
                        "visibility": "open",
                        "onehundred_percent_base": "no_general",
                    },
                    "assignment": {"method": "rating_approval.yes_no"},
                    "motion": {"method": "approval.yes_no"},
                },
                {
                    "all": {"onehundred_percent_base": "yes_no"},
                    "assignment": {"method": "rating_approval.yes_no_abstain"},
                    "motion": {"method": "approval.yes_no_abstain"},
                    "topic": {"visibility": "secret"},
                },
                {
                    "all": {"onehundred_percent_base": "yes_no_abstain"},
                    "assignment": {"method": "rating_approval.yes_no_abstain"},
                    "topic": {"visibility": "secret"},
                },
                {},
                {"assignment": {"method": "selection.no"}},
            )
        ):
            expected_data[i + 1] = {
                "meeting_id": i + 1,
                "used_as_assignment_poll_config_in_meeting_id": i + 1,
                "method": "selection.yes",
                "visibility": "secret",
                "onehundred_percent_base": "valid",
                **data.get("assignment", {}),
                **data.get("all", {}),
            }
            expected_data[i + 8] = {
                "meeting_id": i + 1,
                "used_as_motion_poll_config_in_meeting_id": i + 1,
                "method": "approval.yes_no_abstain",
                "visibility": "secret",
                "onehundred_percent_base": "yes_no_abstain",
                **data.get("motion", {}),
                **data.get("all", {}),
            }
            expected_data[i + 15] = {
                "meeting_id": i + 1,
                "used_as_topic_poll_config_in_meeting_id": i + 1,
                "method": "selection.yes",
                "visibility": "manually",
                "onehundred_percent_base": "yes_no_abstain",
                **data.get("topic", {}),
                **data.get("all", {}),
            }
        self.check_entries(
            {
                "meeting_poll_setting": expected_data,
                "meeting": {
                    id_: {
                        "poll_setting_ids": [i * 7 + id_ for i in [0, 1, 2]],
                        "assignment_poll_config_id": id_,
                        "motion_poll_config_id": id_ + 7,
                        "topic_poll_config_id": id_ + 14,
                    }
                    for id_ in range(1, 8)
                },
            }
        )

    def test_check_prerequisites(self) -> None:
        meeting_data: dict[FullQualifiedId, PartialModel] = self._get_meeting_data()

        self.set_up_organization()
        self.create_entries(meeting_data)
        self._create_users_for_meeting([1, 2, 3], [1])
        self._create_users([21, 22, 23])
        polls_data = {
            # # --------- Running poll
            # **self._get_motion_data(),
            # **self._get_poll_data(
            #     poll_id=1, content_object_id="motion/1", state="started"
            # ),
            # ----------- Incorrect onehundred_percent_base + (for selection polls) pollmethod
            # # Motion
            **self._get_motion_data(2),
            **self._get_poll_data(
                poll_id=2,
                content_object_id="motion/2",
                onehundred_percent_base="Y",
            ),
            # # Assignment with poll_candidate_list
            **self._get_assignment_data(),
            **self._get_poll_data(
                poll_id=3,
                content_object_id="assignment/1",
                onehundred_percent_base="Y",
            ),
            "poll_candidate_list/1": {"meeting_id": 1},
            **self._get_option_data(1, 3, "poll_candidate_list/1"),
            # # Topic
            **self._get_topic_data(),
            **self._get_poll_data(
                poll_id=4,
                content_object_id="topic/1",
                pollmethod="YN",
                onehundred_percent_base="YN",
            ),
            # # Assignment with max_votes_per_option > 1
            **self._get_assignment_data(2),
            **self._get_poll_data(
                poll_id=5,
                content_object_id="assignment/2",
                pollmethod="YNA",
                onehundred_percent_base="YNA",
                extra_data={"max_votes_per_option": 2},
            ),
            **self._get_option_data(3, 5, "user/1"),
            # # Assignment with global options
            **self._get_assignment_data(3),
            **self._get_poll_data(
                poll_id=6,
                content_object_id="assignment/3",
                pollmethod="YNA",
                onehundred_percent_base="YNA",
                extra_data={"global_option_id": 4, "global_no": True},
            ),
            **self._get_option_data(4, 6, "user/1"),
            # # Assignment - other
            **self._get_assignment_data(4),
            **self._get_poll_data(
                poll_id=7,
                content_object_id="assignment/4",
                onehundred_percent_base="Y",
            ),
            **self._get_option_data(5, 7, "user/1"),
            # # ------------- options
            # # Invalid option/content_object_id
            # # # Motion
            # **self._get_motion_data(),
            # **self._get_poll_data(
            #     poll_id=1,
            #     content_object_id="motion/1",
            # ),
            # **self._get_option_data(10, 1, "user/1"),
            # # # Assignment
            # **self._get_assignment_data(),
            # **self._get_poll_data(
            #     poll_id=2,
            #     content_object_id="assignment/1",
            # ),
            # **self._get_option_data(20, 2, "motion/1"),
            # **self._get_assignment_data(2),
            # **self._get_poll_data(
            #     poll_id=3,
            #     content_object_id="assignment/2",
            # ),
            # # Invalid option/text
            # # # Topic
            # **self._get_topic_data(),
            # **self._get_poll_data(
            #     poll_id=4,
            #     content_object_id="topic/1",
            # ),
            # **self._get_option_data(30, 4, "motion/1"),
            # # ----------------- global_option
            # # Missing global option on global_yes/global_no = True
            # **self._get_motion_data(),
            # **self._get_poll_data(
            #     poll_id=1,
            #     content_object_id="motion/1",
            #     extra_data={"global_yes": True},
            # ),
            # # option/poll_id != option/used_as_global_option_in_poll_id
            # **self._get_motion_data(2),
            # **self._get_poll_data(
            #     poll_id=2,
            #     content_object_id="motion/2",
            #     extra_data={"global_option_id": 20},
            # ),
            # **self._get_option_data(20, 1, "motion/1"),
            # # (split-)vote for regular and global option
            # **self._get_assignment_data(),
            # **self._get_poll_data(
            #     poll_id=3,
            #     content_object_id="assignment/1",
            #     extra_data={
            #         "global_yes": True,
            #         "global_option_id": 32,
            #         "max_votes_amount": 3,
            #         "max_votes_per_option": 2,
            #     },
            # ),
            # **self._get_option_data(30, 3, "user/1"),
            # **self._get_option_data(31, 3, "user/2"),
            # **self._get_option_data(32, 3, text="Nota-Oprion"),
            # **self._get_vote_data(50, 30, "Y", 1),
            # **self._get_vote_data(51, 31, "Y", 1),
            # **self._get_vote_data(52, 30, "Y", 2),
            # **self._get_vote_data(53, 32, "Y", 2),
            # # ----------------- single option polls
            # # Multiple options
            # **self._get_motion_data(),
            # **self._get_motion_data(2),
            # **self._get_poll_data(
            #     poll_id=1,
            #     content_object_id="motion/1",
            # ),
            # **self._get_option_data(10, 1, "motion/1"),
            # **self._get_option_data(20, 1, "motion/2"),
            # # Multiple votes
            # **self._get_assignment_data(),
            # **self._get_poll_data(
            #     poll_id=2,
            #     content_object_id="assignment/1",
            # ),
            # "poll_candidate_list/1": {"meeting_id": 1},
            # **self._get_option_data(30, 2, "poll_candidate_list/1"),
            # **self._get_vote_data(1, 30, "Y", 1, 1),
            # **self._get_vote_data(2, 30, "N", 1, 1),
            # **self._get_vote_data(3, 30, "N", 2, 1),
            # # ----------------- vote/value
            # **self._get_motion_data(),
            # **self._get_poll_data(
            #     poll_id=1,
            #     content_object_id="motion/1",
            # ),
            # **self._get_option_data(10, 1, "motion/1"),
            # **self._get_vote_data(38, 10, "no"),
            # # ----------------- split_vote_same_weight
            # **self._get_topic_data(),
            # **self._get_poll_data(
            #     poll_id=1,
            #     content_object_id="topic/1",
            # ),
            # **self._get_option_data(10, 1,  text="Option 10"),
            # **self._get_option_data(20, 1,  text="Option 20"),
            # **self._get_vote_data(38, 10, "Y", 1, 1, 1),
            # **self._get_vote_data(39, 20, "N", 1, 2, 1),
            # **self._get_vote_data(40, 10, "Y", 2),
            # **self._get_vote_data(41, 20, "N", 2),
            # **self._get_vote_data(42, 10, "Y", 3, 3, 2),
            # **self._get_vote_data(43, 20, "N", 3, 3, 2),
            # **self._get_vote_data(44, 20, "A", 3, 3, 3),
            # # ----------------- split_vote_same_users
            # **self._get_topic_data(),
            # **self._get_poll_data(
            #     poll_id=1,
            #     content_object_id="topic/1",
            # ),
            # **self._get_option_data(10, 1, text="Option 10"),
            # **self._get_vote_data(38, 10, "Y", 1, 1, user_token="pseudo-token-10-1"),
            # **self._get_vote_data(39, 10, "N", 1, 2, user_token="pseudo-token-10-1"),
            # **self._get_vote_data(40, 10, "Y", 2, 1, user_token="pseudo-token-10-2"),
            # **self._get_vote_data(41, 10, "N", 3, 1, user_token="pseudo-token-10-2"),
            # **self._get_vote_data(42, 10, "Y", 2, 1, user_token="pseudo-token-10-3"),
            # **self._get_vote_data(43, 10, "N", 3, 1, user_token="pseudo-token-10-3"),
            # **self._get_vote_data(44, 10, "A", 3, 2, user_token="pseudo-token-10-3"),
        }

        self.create_entries(polls_data)

        manager = self.create_migration_manager()

        self.run_pre_checks(manager)
        result = self.get_stats(manager)["stats"]
        if result["status"] == MigrationState.MIGRATION_FAILED:
            raise BadCodingException(
                f"Migration failed with message: {result['exception']}."
            )

    # @patch("openslides_backend.migrations.migration_helper.MigrationHelper.write_line")
    # def test_migration_route(self, method_mock: Mock) -> None:
    #     """Uses migrate http route."""
    #     wait_lock = Lock()
    #     wait_lock.acquire()
    #     indicator_lock = Lock()
    #     indicator_lock.acquire()
    #     method_mock.side_effect = self.wait_for_lock(wait_lock, indicator_lock)
    #     # 5) Call data_manipulation of module
    #     # Future migrations do not need to test all commands. Calling MigrationManager or MigrationHandler directly should be sufficient.
    #     # TODO do response checks in test_migration_route.py if possible

    #     response = self.request("stats")
    #     assert response.json == {
    #         "success": True,
    #         "stats": {
    #             "status": MigrationState.MIGRATION_REQUIRED,
    #             "output": "",
    #             "current_migration_index": MIN_NON_REL_MIGRATION,
    #             "target_migration_index": 100,
    #             "migratable_models": {
    #                 "agenda_item": 15,
    #                 "assignment": 2,
    #                 "assignment_candidate": 5,
    #                 "chat_group": 2,
    #                 "committee": 1,
    #                 "gender": 4,
    #                 "group": 5,
    #                 "list_of_speakers": 16,
    #                 "mediafile": 1,
    #                 "meeting": 1,
    #                 "meeting_mediafile": 1,
    #                 "meeting_user": 3,
    #                 "motion": 4,
    #                 "motion_block": 1,
    #                 "motion_category": 2,
    #                 "motion_change_recommendation": 2,
    #                 "motion_comment": 1,
    #                 "motion_comment_section": 1,
    #                 "motion_state": 15,
    #                 "motion_submitter": 4,
    #                 "motion_supporter": 1,
    #                 "motion_workflow": 2,
    #                 "option": 13,
    #                 "organization": 1,
    #                 "organization_tag": 1,
    #                 "personal_note": 1,
    #                 "poll": 5,
    #                 "projection": 4,
    #                 "projector": 2,
    #                 "projector_countdown": 2,
    #                 "projector_message": 1,
    #                 "speaker": 13,
    #                 "structure_level": 3,
    #                 "tag": 3,
    #                 "theme": 3,
    #                 "topic": 8,
    #                 "user": 3,
    #                 "vote": 9,
    #             },
    #         },
    #     }

    #     response = self.request("migrate")
    #     assert response.json == {
    #         "success": True,
    #         "status": MigrationState.MIGRATION_RUNNING,
    #         "output": self.EXPECTED_INTRODUCTION
    #         + "For setting organization and meeting time zones using 'Europe/Berlin'.\nmigration started\n",
    #     }

    #     indicator_lock.acquire()
    #     response = self.request("stats")
    #     assert response.json == {
    #         "success": True,
    #         "stats": {
    #             "status": MigrationState.MIGRATION_RUNNING,
    #             "output": self.EXPECTED_INTRODUCTION
    #             + "For setting organization and meeting time zones using 'Europe/Berlin'.\nmigration started\n",
    #             "current_migration_index": MIN_NON_REL_MIGRATION,
    #             "target_migration_index": 100,
    #             "migratable_models": response.json["stats"]["migratable_models"],
    #         },
    #     }
    #     assert self.request("migrate").json == {
    #         "success": False,
    #         "message": "Migration is running, only 'stats' or 'progress' commands are allowed.",
    #     }
    #     wait_lock.release()
    #     self.wait_for_migration_thread(self.MAX_WAIT)

    #     assert self.request("progress").json == {
    #         "success": True,
    #         "status": MigrationState.FINALIZED,
    #         "output": "100 of 161 models written to tables.\n161 of 161 models written to tables.\nmigration finished\n",
    #     }

    #     self.assert_indices_state(MigrationState.FINALIZED)
    #     self.check_data()
