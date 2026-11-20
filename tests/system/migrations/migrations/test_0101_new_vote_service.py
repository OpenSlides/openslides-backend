from decimal import Decimal
from json import dumps
from typing import Any, Literal

from psycopg.types.json import Jsonb

from openslides_backend.action.util.crypto import get_random_string
from openslides_backend.migrations.migration_helper import MigrationState
from openslides_backend.services.postgresql.db_connection_handling import os_conn_pool
from openslides_backend.shared.exceptions import BadCodingException
from openslides_backend.shared.patterns import FullQualifiedId
from openslides_backend.shared.typing import PartialModel
from tests.system.migrations.base_migration_test import BaseMigrationTestCase


class TestMigration101(BaseMigrationTestCase):
    migration_number = 101
    EXPECTED_INTRODUCTION = ""

    @staticmethod
    def _get_meeting_data(
        base: int = 1, extra_data: dict[FullQualifiedId, PartialModel] | None = None
    ) -> dict[FullQualifiedId, PartialModel]:
        result: dict[FullQualifiedId, PartialModel] = {}
        extra_data = extra_data or {}
        if "committee_id" not in (
            meeting_data := extra_data.get(f"meeting/{base}", {})
        ):
            committee_id = base + 59
            if meeting_data:
                extra_data[f"meeting/{base}"]["committee_id"] = committee_id
            else:
                extra_data[f"meeting/{base}"] = {"committee_id": committee_id}
            result[f"committee/{committee_id}"] = {"name": f"Committee {committee_id}"}
        else:
            committee_id = meeting_data["committee_id"]
        result.update(
            {
                f"meeting/{base}": {
                    "default_group_id": base,
                    "admin_group_id": base + 1,
                    "motions_default_workflow_id": base,
                    "motions_default_amendment_workflow_id": base,
                    "reference_projector_id": base,
                    "committee_id": committee_id,
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
            - All types of poll + of the related collections
            - meeting_user/vote_delegated_to_id
            - group/permissions
        """
        meeting_data: dict[FullQualifiedId, PartialModel] = self._get_meeting_data(
            1,
            {
                "meeting/1": {
                    "motion_poll_projection_name_order_first": "first_name",
                    "motion_poll_projection_max_columns": 8,
                    "assignment_poll_default_method": "yna",
                    "motion_poll_default_method": "votes",
                    "poll_default_method": "N",
                    "assignment_poll_default_type": "named",
                    "motion_poll_default_type": "named",
                    "poll_default_type": "analog",
                    "assignment_poll_default_onehundred_percent_base": "YNA",
                    "motion_poll_default_onehundred_percent_base": "valid",
                    "poll_default_onehundred_percent_base": "valid",
                    "assignment_poll_sort_poll_result_by_votes": False,
                    "assignment_poll_enable_max_votes_per_option": True,
                    "poll_sort_poll_result_by_votes": True,
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
            # Assignment with global options
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
            # Assignment - other (without option)
            **self._get_assignment_data(5),
            **self._get_poll_data(
                poll_id=7,
                content_object_id="assignment/5",
                state="created",
            ),
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
                    ("poll_config_rating_approval", 7),
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
                    ("poll_config_rating_approval", 2),
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
                    7: {
                        **base_poll_fields,
                        "config_id": "poll_config_rating_approval/7",
                        "content_object_id": "assignment/5",
                        "visibility": "open",
                        "state": "created",
                        "published": False,
                        "result": None,
                        "option_ids": [],
                        "ballot_ids": [],
                        "ballot_user_ids": [],
                        "entitled_user_ids": [],
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
                    7: {
                        "poll_id": 7,
                        "min_options_amount": 1,
                        "max_options_amount": 1,
                        "max_yes_amount": None,
                        "allow_abstain": False,
                        "onehundred_percent_base": "valid",
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
                    #
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
                    #
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
