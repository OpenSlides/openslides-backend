from decimal import Decimal
from typing import Any, Literal

from psycopg.types.json import Jsonb

from openslides_backend.action.util.crypto import get_random_string
from openslides_backend.migrations.migration_helper import MigrationState
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
        if "committee_id" not in extra_data[f"meeting/{base}"]:
            committee_id = base + 59
            extra_data[f"meeting/{base}"]["committee_id"] = committee_id
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
        pollmethod: Literal["Y", "YN", "YNA", "N"],
        onehundred_percent_base: Literal[
            "Y",
            "YN",
            "YNA",
            "N",
            "valid",
            "cast",
            "entitled",
            "entitled_present",
            "disabled",
        ],
        type_: Literal["analog", "named", "pseudoanonymous", "cryptographic"],
        content_object_id: str,
        state: Literal["created", "started", "finished", "published"],
        is_pseudoanonymized: bool,
        extra_data: PartialModel = {},
    ) -> dict[FullQualifiedId, PartialModel]:
        return {
            f"poll/{poll_id}": {
                "title": f"Poll {poll_id}",
                "meeting_id": meeting_id,
                "backend": "fast",
                "pollmethod": pollmethod,
                "onehundred_percent_base": onehundred_percent_base,
                "type": type_,
                "content_object_id": content_object_id,
                "state": state,
                "is_pseudoanonymized": is_pseudoanonymized,
                **extra_data,
            }
        }

    @staticmethod
    def _get_motion_data(
        base: int,
        meeting_id: int,
        motion_data: PartialModel = {},
    ) -> dict[FullQualifiedId, PartialModel]:
        return {
            f"motion/{base}": {
                "title": f"motion{base}",
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
        base: int,
        meeting_id: int,
        assignment_data: PartialModel = {},
    ) -> dict[FullQualifiedId, PartialModel]:
        return {
            f"assignment/{base}": {
                "title": f"assignment {base}",
                "meeting_id": meeting_id,
                **assignment_data,
            },
            f"list_of_speakers/{base + 200}": {
                "content_object_id": f"assignment/{base}",
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
        content_object_id: str,
        extra_data: PartialModel = {},
    ) -> dict[FullQualifiedId, PartialModel]:
        return {
            f"option/{base}": {
                "poll_id": poll_id,
                "meeting_id": meeting_id,
                "content_object_id": content_object_id,
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
        user_token: str | None = None,
    ) -> dict[FullQualifiedId, PartialModel]:
        result: dict[str, Any] = {
            f"vote/{base}": {
                "meeting_id": meeting_id,
                "option_id": option_id,
                "value": value,
                "weight": Decimal(base),
                "user_token": user_token or get_random_string(16),
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
                    # "assignment_poll_default_group_ids": [1],
                    # "motion_poll_default_group_ids": [3],
                    # "topic_poll_default_group_ids": [4],
                    "assignment_poll_default_method": "Y",
                    "motion_poll_default_method": "YNA",
                    "poll_default_method": "N",
                    "assignment_poll_default_type": "named",
                    "motion_poll_default_type": "open",
                    "poll_default_type": "analog",
                    "assignment_poll_default_onehundred_percent_base": "YNA",
                    "motion_poll_default_onehundred_percent_base": "valid",
                    "poll_default_onehundred_percent_base": "valid",
                    "assignment_poll_sort_poll_result_by_votes": False,
                    "assignment_poll_enable_max_votes_per_option": True,
                    "poll_sort_poll_result_by_votes": True,
                    "poll_default_live_voting_enabled": True,
                },
                "group/1": {"permissions": ["poll.can_manage"]},
                "group/2": {
                    "permissions": ["poll.can_manage", "motion.can_manage_polls"]
                },
                "group/3": {"permissions": ["motion.can_see", "mediafile.can_see"]},
                "group/4": {"meeting_id": 1, "name": "group4", "permissions": []},
            },
        )

        self.set_up_organization()
        self.create_entries(meeting_data)
        self._create_users_for_meeting(1, [1, 2], [1])
        self._create_users([21, 22])
        polls_data = {
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
                            }
                        ]
                    ),
                },
            ),
            **self._get_option_data(1, 1, 1, "motion/1", {"yes": 1, "no": 1}),
            **self._get_vote_data(1, 1, 1, "Y"),
            **self._get_vote_data(2, 1, 1, "N", 1, 2),
            #
            **self._get_assignment_data(1, 1),
            **self._get_poll_data(
                poll_id=2,
                meeting_id=1,
                pollmethod="YNA",
                onehundred_percent_base="YNA",
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
            **self._get_option_data(
                2, 2, 1, "poll_candidate_list/1", {"yes": 1, "no": 1}
            ),
            **self._get_vote_data(3, 1, 2, "Y"),
            **self._get_vote_data(4, 1, 2, "N", 1, 2),
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
