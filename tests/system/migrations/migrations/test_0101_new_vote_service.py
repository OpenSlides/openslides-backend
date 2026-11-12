from decimal import Decimal
from typing import Any, Literal

from psycopg.types.json import Jsonb

from openslides_backend.action.util.crypto import get_random_string
from openslides_backend.migrations.migration_helper import MigrationState
from openslides_backend.services.postgresql.db_connection_handling import os_conn_pool
from openslides_backend.shared.exceptions import BadCodingException
from openslides_backend.shared.patterns import FullQualifiedId
from openslides_backend.shared.typing import PartialModel
from tests.system.migrations.base_migration_test import BaseMigrationTestCase

DEFAULT_PROJECTOR_OPTIONS = (
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


class TestMigration101(BaseMigrationTestCase):
    migration_number = 101
    EXPECTED_INTRODUCTION = ""

    @staticmethod
    def _get_meeting_data(
        base: int = 1, extra_data: dict[FullQualifiedId, PartialModel] = {}
    ) -> dict[FullQualifiedId, PartialModel]:
        result: dict[FullQualifiedId, PartialModel] = {}
        if "committee_id" not in (
            meeting_data := extra_data.get(f"meeting/{base}", {})
        ):
            committee_id = base + 59
            if meeting_data:
                extra_data[f"meeting/{base}"]["committee_id"] = committee_id
            else:
                extra_data[f"meeting/{base}"] = {"committee_id": committee_id}
            result[f"committee/{committee_id}"] = {"name": f"Committee {committee_id}"}
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
                        for option in DEFAULT_PROJECTOR_OPTIONS
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
        meeting_id: int,
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
                "meeting_id": meeting_id,
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
        meeting_id: int,
        user_ids: list[int],
        group_ids: list[int],
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
        meeting_id: int,
        content_object_id: str | None = None,
        text: str | None = None,
        extra_data: PartialModel = {},
    ) -> dict[FullQualifiedId, PartialModel]:
        return {
            f"option/{base}": {
                "poll_id": poll_id,
                "meeting_id": meeting_id,
                "content_object_id": content_object_id,
                "text": text,
                **extra_data,
            }
        }

    @staticmethod
    def _get_vote_data(
        base: int,
        meeting_id: int,
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
                "meeting_id": meeting_id,
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

    def test_migration_manager(self) -> None:
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
                },
                "group/4": {"meeting_id": 1, "name": "group4", "permissions": []},
            },
        )

        self.set_up_organization()
        self.create_entries(meeting_data)
        self._create_users_for_meeting(1, [1, 2, 3], [1])
        self._create_users([21, 22, 23])
        self.update_entries({"meeting_user/102": {"vote_delegated_to_id": 101}})
        polls_data = {
            # Motion
            **self._get_motion_data(1, 1),
            **self._get_poll_data(
                poll_id=1,
                meeting_id=1,
                pollmethod="YNA",
                onehundred_percent_base="YNA",
                type_="named",
                content_object_id="motion/1",
                state="published",
                is_pseudoanonymized=False,
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
                                "present": False,
                            },
                            {
                                "user_id": 3,
                                "voted": False,
                                "present": True,
                            },
                        ]
                    ),
                },
                # {'votesinvalid': 1}
            ),
            **self._get_option_data(
                1, 1, 1, "motion/1", extra_data={"yes": 1, "no": 1}
            ),
            **self._get_vote_data(1, 1, 1, "Y"),
            **self._get_vote_data(2, 1, 1, "N", 1, 2),
            # Assignment with poll_candidate_list
            **self._get_assignment_data(1, 1),
            **self._get_poll_data(
                poll_id=2,
                meeting_id=1,
                pollmethod="YN",
                onehundred_percent_base="YN",
                type_="named",
                content_object_id="assignment/1",
                state="published",
                is_pseudoanonymized=True,
                extra_data={
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
                                "present": True,
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
                2, 2, 1, "poll_candidate_list/1", extra_data={"yes": 1, "no": 1}
            ),
            **self._get_vote_data(3, 1, 2, "Y"),
            **self._get_vote_data(4, 1, 2, "N", 1, 2),
            # Topic
            **self._get_topic_data(1, 1),
            **self._get_poll_data(
                poll_id=3,
                meeting_id=1,
                pollmethod="N",
                onehundred_percent_base="N",
                type_="named",
                content_object_id="topic/1",
                state="published",
                is_pseudoanonymized=False,
                extra_data={
                    "min_votes_amount": 1,
                    "max_votes_amount": 3,
                    "global_option_id": 6,
                    "global_yes": True,
                    "votescast": Decimal(4),
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
            **self._get_option_data(3, 3, 1, text="Option 3/1", extra_data={"no": 1}),
            **self._get_option_data(4, 3, 1, text="Option 3/2", extra_data={"no": 0}),
            **self._get_option_data(5, 3, 1, text="Option 3/3", extra_data={"no": 2}),
            **self._get_option_data(6, 3, 1, text="Nota-Option", extra_data={"yes": 1}),
            **self._get_vote_data(5, 1, 3, "N", 2, 1),
            **self._get_vote_data(6, 1, 5, "N", 2, 1),
            **self._get_vote_data(7, 1, 5, "N", 1, 1),
            **self._get_vote_data(8, 1, 6, "Y", 3, 3),
            # Assignment with max_votes_per_option > 1
            **self._get_assignment_data(2, 1),
            **self._get_poll_data(
                poll_id=4,
                meeting_id=1,
                pollmethod="Y",
                onehundred_percent_base="Y",
                type_="named",
                content_object_id="assignment/2",
                state="published",
                is_pseudoanonymized=False,
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
            **self._get_option_data(7, 4, 1, "user/21", extra_data={"yes": 1}),
            **self._get_option_data(8, 4, 1, "user/22", extra_data={"yes": 3}),
            **self._get_option_data(9, 4, 1, "user/23", extra_data={"yes": 4}),
            **self._get_vote_data(9, 1, 7, "Y", 2, 2),
            **self._get_vote_data(10, 1, 8, "Y", 2, 2),
            **self._get_vote_data(11, 1, 9, "Y", 2, 2, 2),
            **self._get_vote_data(12, 1, 8, "Y", 1, 1, 2),
            # Assignment with global options
            **self._get_assignment_data(3, 1),
            **self._get_poll_data(
                poll_id=5,
                meeting_id=1,
                pollmethod="Y",
                onehundred_percent_base="Y",
                type_="named",
                content_object_id="assignment/3",
                state="published",
                is_pseudoanonymized=False,
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
            **self._get_option_data(10, 5, 1, "user/21", extra_data={"yes": 1}),
            **self._get_option_data(11, 5, 1, "user/22", extra_data={"yes": 2}),
            **self._get_option_data(12, 5, 1, "user/23", extra_data={"no": 1}),
            **self._get_vote_data(13, 1, 10, "Y", 2, 2),
            **self._get_vote_data(14, 1, 11, "Y", 2, 2),
            **self._get_vote_data(15, 1, 11, "Y", 1, 1),
            **self._get_vote_data(16, 1, 12, "N", 3, 3),
            # Assignment - other
            **self._get_assignment_data(4, 1),
            **self._get_poll_data(
                poll_id=6,
                meeting_id=1,
                pollmethod="YNA",
                onehundred_percent_base="YNA",
                type_="named",
                content_object_id="assignment/4",
                state="published",
                is_pseudoanonymized=False,
                extra_data={
                    "min_votes_amount": 1,
                    "max_votes_amount": 4,
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
                                "present": False,
                            },
                        ]
                    ),
                },
            ),
            **self._get_option_data(
                13, 6, 1, "user/21", extra_data={"yes": 2, "no": 1, "abstain": 0}
            ),
            **self._get_option_data(
                14, 6, 1, "user/22", extra_data={"yes": 0, "no": 2, "abstain": 1}
            ),
            **self._get_option_data(
                15, 6, 1, "user/23", extra_data={"yes": 0, "no": 0, "abstain": 2}
            ),
            **self._get_vote_data(17, 1, 13, "Y", 2, 1),
            **self._get_vote_data(18, 1, 14, "N", 2, 1),
            **self._get_vote_data(19, 1, 15, "A", 2, 1),
            **self._get_vote_data(20, 1, 13, "Y", 1, 1),
            **self._get_vote_data(21, 1, 14, "A", 1, 1),
            **self._get_vote_data(22, 1, 15, "A", 1, 1),
            **self._get_vote_data(23, 1, 13, "N", 3, 3),
            **self._get_vote_data(24, 1, 14, "N", 3, 3),
            **self._get_vote_data(25, 1, 13, "N"),
            **self._get_vote_data(26, 1, 14, "N"),
            # Assignment - other without option
            **self._get_assignment_data(5, 1),
            **self._get_poll_data(
                poll_id=7,
                meeting_id=1,
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

    def test_check_prerequisites(self) -> None:
        meeting_data: dict[FullQualifiedId, PartialModel] = self._get_meeting_data()

        self.set_up_organization()
        self.create_entries(meeting_data)
        self._create_users_for_meeting(1, [1, 2, 3], [1])
        self._create_users([21, 22, 23])
        polls_data = {
            # # --------- Running poll
            # **self._get_motion_data(),
            # **self._get_poll_data(
            #     poll_id=1, meeting_id=1, content_object_id="motion/1", state="started"
            # ),
            # ----------- Incorrect onehundred_percent_base + (for selection polls) pollmethod
            # # Motion
            **self._get_motion_data(2, 1),
            **self._get_poll_data(
                poll_id=2,
                meeting_id=1,
                content_object_id="motion/2",
                onehundred_percent_base="Y",
            ),
            # # Assignment with poll_candidate_list
            **self._get_assignment_data(),
            **self._get_poll_data(
                poll_id=3,
                meeting_id=1,
                content_object_id="assignment/1",
                onehundred_percent_base="Y",
            ),
            "poll_candidate_list/1": {"meeting_id": 1},
            **self._get_option_data(1, 3, 1, "poll_candidate_list/1"),
            # # Topic
            **self._get_topic_data(),
            **self._get_poll_data(
                poll_id=4,
                meeting_id=1,
                content_object_id="topic/1",
                pollmethod="YN",
                onehundred_percent_base="YN",
            ),
            # # Assignment with max_votes_per_option > 1
            **self._get_assignment_data(2, 1),
            **self._get_poll_data(
                poll_id=5,
                meeting_id=1,
                content_object_id="assignment/2",
                pollmethod="YNA",
                onehundred_percent_base="YNA",
                extra_data={"max_votes_per_option": 2},
            ),
            **self._get_option_data(3, 5, 1, "user/1"),
            # # Assignment with global options
            **self._get_assignment_data(3, 1),
            **self._get_poll_data(
                poll_id=6,
                meeting_id=1,
                content_object_id="assignment/3",
                pollmethod="YNA",
                onehundred_percent_base="YNA",
                extra_data={"global_option_id": 4, "global_no": True},
            ),
            **self._get_option_data(4, 6, 1, "user/1"),
            # # Assignment - other
            **self._get_assignment_data(4, 1),
            **self._get_poll_data(
                poll_id=7,
                meeting_id=1,
                content_object_id="assignment/4",
                onehundred_percent_base="Y",
            ),
            **self._get_option_data(5, 7, 1, "user/1"),
            # # ------------- options
            # # Invalid option/content_object_id
            # # # Motion
            # **self._get_motion_data(),
            # **self._get_poll_data(
            #     poll_id=1,
            #     meeting_id=1,
            #     content_object_id="motion/1",
            # ),
            # **self._get_option_data(10, 1, 1, "user/1"),
            # # # Assignment
            # **self._get_assignment_data(),
            # **self._get_poll_data(
            #     poll_id=2,
            #     meeting_id=1,
            #     content_object_id="assignment/1",
            # ),
            # **self._get_option_data(20, 2, 1, "motion/1"),
            # **self._get_assignment_data(2),
            # **self._get_poll_data(
            #     poll_id=3,
            #     meeting_id=1,
            #     content_object_id="assignment/2",
            # ),
            # # Invalid option/text
            # # # Topic
            # **self._get_topic_data(),
            # **self._get_poll_data(
            #     poll_id=4,
            #     meeting_id=1,
            #     content_object_id="topic/1",
            # ),
            # **self._get_option_data(30, 4, 1, "motion/1"),
            # # ----------------- global_option
            # # Missing global option on global_yes/global_no = True
            # **self._get_motion_data(),
            # **self._get_poll_data(
            #     poll_id=1,
            #     meeting_id=1,
            #     content_object_id="motion/1",
            #     extra_data={"global_yes": True},
            # ),
            # # option/poll_id != option/used_as_global_option_in_poll_id
            # **self._get_motion_data(2),
            # **self._get_poll_data(
            #     poll_id=2,
            #     meeting_id=1,
            #     content_object_id="motion/2",
            #     extra_data={"global_option_id": 20},
            # ),
            # **self._get_option_data(20, 1, 1, "motion/1"),
            # # (split-)vote for regular and global option
            # **self._get_assignment_data(),
            # **self._get_poll_data(
            #     poll_id=3,
            #     meeting_id=1,
            #     content_object_id="assignment/1",
            #     extra_data={
            #         "global_yes": True,
            #         "global_option_id": 32,
            #         "max_votes_amount": 3,
            #         "max_votes_per_option": 2,
            #     },
            # ),
            # **self._get_option_data(30, 3, 1, "user/1"),
            # **self._get_option_data(31, 3, 1, "user/2"),
            # **self._get_option_data(32, 3, 1, text="Nota-Oprion"),
            # **self._get_vote_data(50, 1, 30, "Y", 1),
            # **self._get_vote_data(51, 1, 31, "Y", 1),
            # **self._get_vote_data(52, 1, 30, "Y", 2),
            # **self._get_vote_data(53, 1, 32, "Y", 2),
            # # ----------------- single option polls
            # # Multiple options
            # **self._get_motion_data(),
            # **self._get_motion_data(2, 1),
            # **self._get_poll_data(
            #     poll_id=1,
            #     meeting_id=1,
            #     content_object_id="motion/1",
            # ),
            # **self._get_option_data(10, 1, 1, "motion/1"),
            # **self._get_option_data(20, 1, 1, "motion/2"),
            # # Multiple votes
            # **self._get_assignment_data(),
            # **self._get_poll_data(
            #     poll_id=2,
            #     meeting_id=1,
            #     content_object_id="assignment/1",
            # ),
            # "poll_candidate_list/1": {"meeting_id": 1},
            # **self._get_option_data(30, 2, 1, "poll_candidate_list/1"),
            # **self._get_vote_data(1, 1, 30, "Y", 1, 1),
            # **self._get_vote_data(2, 1, 30, "N", 1, 1),
            # **self._get_vote_data(3, 1, 30, "N", 1, 2),
            # # ----------------- vote/value
            # **self._get_motion_data(),
            # **self._get_poll_data(
            #     poll_id=1,
            #     meeting_id=1,
            #     content_object_id="motion/1",
            # ),
            # **self._get_option_data(10, 1, 1, "motion/1"),
            # **self._get_vote_data(38, 1, 10, "no"),
            # # ----------------- split_vote_same_weight
            # **self._get_topic_data(),
            # **self._get_poll_data(
            #     poll_id=1,
            #     meeting_id=1,
            #     content_object_id="topic/1",
            # ),
            # **self._get_option_data(10, 1, 1, text="Option 10"),
            # **self._get_option_data(20, 1, 1, text="Option 20"),
            # **self._get_vote_data(38, 1, 10, "Y", 1, 1, 1),
            # **self._get_vote_data(39, 1, 20, "N", 1, 1, 2),
            # **self._get_vote_data(40, 1, 10, "Y", 2),
            # **self._get_vote_data(41, 1, 20, "N", 2),
            # **self._get_vote_data(42, 1, 10, "Y", 3, 3, 2),
            # **self._get_vote_data(43, 1, 20, "N", 3, 3, 2),
            # **self._get_vote_data(44, 1, 20, "A", 3, 3, 3),
            # # ----------------- split_vote_same_users
            # **self._get_topic_data(),
            # **self._get_poll_data(
            #     poll_id=1,
            #     meeting_id=1,
            #     content_object_id="topic/1",
            # ),
            # **self._get_option_data(10, 1, 1, text="Option 10"),
            # **self._get_vote_data(38, 1, 10, "Y", 1, 1, user_token="pseudo-token-10-1"),
            # **self._get_vote_data(39, 1, 10, "N", 1, 2, user_token="pseudo-token-10-1"),
            # **self._get_vote_data(40, 1, 10, "Y", 2, 1, user_token="pseudo-token-10-2"),
            # **self._get_vote_data(41, 1, 10, "N", 3, 1, user_token="pseudo-token-10-2"),
            # **self._get_vote_data(42, 1, 10, "Y", 2, 1, user_token="pseudo-token-10-3"),
            # **self._get_vote_data(43, 1, 10, "N", 3, 1, user_token="pseudo-token-10-3"),
            # **self._get_vote_data(44, 1, 10, "A", 3, 2, user_token="pseudo-token-10-3"),
        }

        self.create_entries(polls_data)

        manager = self.create_migration_manager()

        self.run_pre_checks(manager)
        result = self.get_stats(manager)["stats"]
        if result["status"] == MigrationState.MIGRATION_FAILED:
            raise BadCodingException(
                f"Migration failed with message: {result['exception']}."
            )
