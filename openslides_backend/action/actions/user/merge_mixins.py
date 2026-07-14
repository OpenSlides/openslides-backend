from typing import Any

from openslides_backend.services.database.interface import PartialModel
from openslides_backend.shared.history_events import update_history_information

from ....models.models import (
    AssignmentCandidate,
    MeetingUser,
    MotionEditor,
    MotionSubmitter,
    MotionSupporter,
    MotionWorkingGroupSpeaker,
    PersonalNote,
    Poll,
    Speaker,
)
from ....services.database.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator, Or
from ....shared.patterns import Collection, fqid_from_collection_and_id
from ....shared.typing import HistoryInformation
from .base_merge_mixin import BaseMergeMixin, MergeModeDict


class SpeakerMergeMixin(BaseMergeMixin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            Speaker,
            {
                "ignore": [
                    "begin_time",
                    "end_time",
                    "pause_time",
                    "unpause_time",
                    "total_pause",
                    "meeting_user_id",
                    "meeting_id",
                    "point_of_order",
                    "list_of_speakers_id",
                    "answer",
                ],
                "lowest": [
                    "weight",
                ],
                "require_equality_absolute": [
                    "speech_state",
                    "point_of_order_category_id",
                    "structure_level_list_of_speakers_id",
                    "note",
                ],
            },
            "meeting_user_id",
        )

    def check_speakers(self, meeting_user_ids: list[int]) -> None:
        if len(meeting_user_ids):
            running_speakers = self.datastore.filter(
                "speaker",
                And(
                    FilterOperator("end_time", "=", None),
                    Or(
                        *[
                            FilterOperator("meeting_user_id", "=", id_)
                            for id_ in meeting_user_ids
                        ]
                    ),
                    FilterOperator("begin_time", "!=", None),
                ),
                ["id", "meeting_id"],
            )
            if len(running_speakers):
                meeting_ids = {
                    str(speaker["meeting_id"]) for speaker in running_speakers.values()
                }
                raise ActionException(
                    f"Speaker(s) {', '.join([str(key) for key in running_speakers.keys()])} are still running in meeting(s) {', '.join(meeting_ids)}"
                )


class AssignmentCandidateMergeMixin(BaseMergeMixin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            AssignmentCandidate,
            {
                "ignore": ["meeting_user_id", "meeting_id", "assignment_id"],
                "lowest": [
                    "weight",
                ],
            },
            "meeting_user_id",
        )

    def get_full_history_information(self) -> HistoryInformation | None:
        information = super().get_full_history_information() or {}
        assignment_ids: set[int] = set()
        for data, ids, is_transfer in self._history_replacement_groups[
            "assignment_candidate"
        ]:
            assignment_ids.add(data["assignment_id"])
        for assignment_id in assignment_ids:
            update_history_information(
                information,
                fqid_from_collection_and_id("assignment", assignment_id),
                ["Candidates merged"],
            )
        return information


motion_meeting_user_list_item_groups: MergeModeDict = {
    "ignore": ["meeting_user_id", "meeting_id", "motion_id"],
    "lowest": [
        "weight",
    ],
}


class MotionSubmitterMergeMixin(BaseMergeMixin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            MotionSubmitter, motion_meeting_user_list_item_groups, "meeting_user_id"
        )

    def get_full_history_information(self) -> HistoryInformation | None:
        information = super().get_full_history_information() or {}
        motion_ids: set[int] = set()
        for data, ids, is_transfer in self._history_replacement_groups[
            "motion_submitter"
        ]:
            motion_ids.add(data["motion_id"])
        for motion_id in motion_ids:
            update_history_information(
                information,
                fqid_from_collection_and_id("motion", motion_id),
                ["Submitters merged"],
            )
        return information


class MotionSupporterMergeMixin(BaseMergeMixin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            MotionSupporter,
            {
                "ignore": ["meeting_user_id", "meeting_id", "motion_id"],
            },
            "meeting_user_id",
        )

    def get_full_history_information(self) -> HistoryInformation | None:
        information = super().get_full_history_information() or {}
        motion_ids: set[int] = set()
        for data, ids, is_transfer in self._history_replacement_groups[
            "motion_supporter"
        ]:
            motion_ids.add(data["motion_id"])
        for motion_id in motion_ids:
            update_history_information(
                information,
                fqid_from_collection_and_id("motion", motion_id),
                ["Supporters merged"],
            )
        return information


class MotionEditorMergeMixin(BaseMergeMixin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            MotionEditor, motion_meeting_user_list_item_groups, "meeting_user_id"
        )


class MotionWorkingGroupSpeakerMergeMixin(BaseMergeMixin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            MotionWorkingGroupSpeaker,
            motion_meeting_user_list_item_groups,
            "meeting_user_id",
        )


class PersonalNoteMergeMixin(BaseMergeMixin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            PersonalNote,
            {
                "ignore": ["meeting_user_id", "content_object_id", "meeting_id"],
                "priority": ["note"],
                "highest": ["star"],
            },
            "meeting_user_id",
        )


class MeetingUserMergeMixin(
    PersonalNoteMergeMixin,
    MotionWorkingGroupSpeakerMergeMixin,
    MotionEditorMergeMixin,
    MotionSubmitterMergeMixin,
    MotionSupporterMergeMixin,
    AssignmentCandidateMergeMixin,
    SpeakerMergeMixin,
):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            MeetingUser,
            {
                "ignore": [
                    "user_id",
                    "locked_out",
                ],
                "priority": [
                    "comment",
                    "number",
                    "about_me",
                    "vote_weight",
                    "vote_delegated_to_id",
                    "meeting_id",
                ],
                "merge": [
                    "vote_delegations_from_ids",
                    "chat_message_ids",
                    "group_ids",
                    "structure_level_ids",
                    "history_entry_ids",
                    "poll_voted_ids",  # throw error if conflict on same poll
                    "poll_option_ids",  # throw error if conflict on same poll
                    "acting_ballot_ids",  # throw error if conflict on same poll
                    "represented_ballot_ids",  # throw error if conflict on same poll
                ],
                "deep_merge": {
                    "assignment_candidate_ids": "assignment_candidate",
                    "motion_supporter_ids": "motion_supporter",
                    "motion_editor_ids": "motion_editor",
                    "motion_submitter_ids": "motion_submitter",
                    "motion_working_group_speaker_ids": "motion_working_group_speaker",
                },
                "deep_create_merge": {
                    "personal_note_ids": "personal_note",
                    "speaker_ids": "speaker",
                },
            },
            "user_id",
        )

    def get_merge_comparison_hash(
        self, collection: Collection, model: PartialModel
    ) -> int | str | tuple[int | str, ...]:
        match collection:
            case "motion_submitter":
                return model["motion_id"]
            case "assignment_candidate":
                return model["assignment_id"]
            case "personal_note":
                return model["content_object_id"]
            case "motion_editor":
                return model["motion_id"]
            case "motion_supporter":
                return model["motion_id"]
            case "motion_working_group_speaker":
                return model["motion_id"]
            case "speaker":
                meeting = self.datastore.get(
                    fqid_from_collection_and_id("meeting", model["meeting_id"]),
                    ["list_of_speakers_allow_multiple_speakers"],
                )
                if (
                    meeting.get("list_of_speakers_allow_multiple_speakers")
                    or model.get("end_time") is not None
                    or model.get("answer")
                ):
                    return model["id"]
                return (
                    model["list_of_speakers_id"],
                    model.get("point_of_order", False),
                )
            case _:
                return super().get_merge_comparison_hash(collection, model)

    def check_polls(self, into: PartialModel, other_models: list[PartialModel]) -> None:
        messages: list[str] = []
        group_ids: set[int] = set()
        meeting_ids: set[int] = set()
        meeting_id_by_group_ids: dict[int, int] = {}

        meeting_user_ids = [
            mu_id
            for user in [into, *other_models]
            for mu_id in user.get("meeting_user_ids", [])
        ]
        meeting_users = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting_user",
                    meeting_user_ids,
                    [
                        "user_id",
                        "meeting_id",
                        "group_ids",
                        "vote_delegations_from_ids",
                        "vote_delegated_to_id",
                        "poll_voted_ids",
                        "poll_option_ids",
                        "acting_ballot_ids",
                        "represented_ballot_ids",
                    ],
                )
            ]
        )["meeting_user"]

        for m_user in meeting_users.values():
            if len(g_ids := m_user.get("group_ids", [])):
                meeting_id_by_group_ids.update(
                    {g_id: m_user["meeting_id"] for g_id in g_ids}
                )
                group_ids.update(g_ids)
                meeting_ids.add(m_user["meeting_id"])
        if meeting_ids:
            polls = self.datastore.filter(
                "poll",
                And(
                    FilterOperator("state", "=", Poll.STATE_STARTED),
                    Or(
                        FilterOperator("meeting_id", "=", meeting_id)
                        for meeting_id in meeting_ids
                    ),
                ),
                ["entitled_group_ids"],
            )
            poll_group_ids: set[int] = {
                group_id
                for poll in polls.values()
                for group_id in poll.get("entitled_group_ids", [])
            }
            common = group_ids.intersection(poll_group_ids)
            if len(common):
                forbidden_meeting_ids = {
                    str(meeting_id_by_group_ids[g_id]) for g_id in common
                }
                messages.append(
                    f"some of the users are entitled to vote in currently running polls in meeting(s) {', '.join(forbidden_meeting_ids)}"
                )

        delegator_meeting_user_ids = {
            meeting_user_id
            for meeting_user in meeting_users.values()
            for meeting_user_id in meeting_user.get("vote_delegations_from_ids", [])
        }
        proxy_meeting_user_ids = {
            meeting_user_id
            for meeting_user in meeting_users.values()
            if (meeting_user_id := meeting_user.get("vote_delegated_to_id"))
        }
        is_delegator_by_meeting: dict[int, bool] = {}
        delegation_conflicts: set[str] = set()
        for meeting_user in meeting_users.values():
            meeting_id = meeting_user["meeting_id"]
            for field in ["vote_delegated_to_id", "vote_delegations_from_ids"]:
                if meeting_user.get(field):
                    if is_delegator_by_meeting.get(meeting_id) == (
                        field != "vote_delegated_to_id"
                    ):
                        delegation_conflicts.add(str(meeting_id))
                    else:
                        is_delegator_by_meeting[meeting_id] = (
                            field == "vote_delegated_to_id"
                        )
        if len(delegation_conflicts):
            messages.append(
                f"some of the selected users have different delegations roles in meeting(s) {', '.join(delegation_conflicts)}"
            )
        if len(
            bad_users := [
                id_
                for id_ in list(meeting_users.keys())
                if id_ in {*delegator_meeting_user_ids, *proxy_meeting_user_ids}
            ]
        ):
            bad_meetings = {
                str(meeting_id)
                for id_ in bad_users
                if (meeting_id := meeting_users.get(id_, {}).get("meeting_id"))
            }
            messages.append(
                f"some of the selected users are delegating votes to each other in meeting(s) {', '.join(bad_meetings)}"
            )

        ballot_poll_ids_per_user_id: dict[int, set[int]] = {}
        option_poll_ids_per_user_id: dict[int, set[int]] = {}
        for meeting_user in meeting_users.values():
            if poll_voted_ids := meeting_user.get("poll_voted_ids"):
                ballot_poll_ids_per_user_id.setdefault(
                    meeting_user["user_id"], set()
                ).update(set(poll_voted_ids))
            if len(
                (o_ids := meeting_user.get("poll_option_ids", []))
                + (
                    b_ids := list(
                        {
                            id_
                            for id_ in [
                                *meeting_user.get("acting_ballot_ids", []),
                                *meeting_user.get("represented_ballot_ids", []),
                            ]
                        }
                    )
                )
            ):
                many_models = self.datastore.get_many(
                    [
                        GetManyRequest("poll_option", o_ids, ["poll_id"]),
                        GetManyRequest("poll_ballot", b_ids, ["poll_id"]),
                    ]
                )
                if o_ids:
                    option_poll_ids_per_user_id.setdefault(
                        meeting_user["user_id"], set()
                    ).update(
                        {
                            option["poll_id"]
                            for option in many_models["poll_option"].values()
                        }
                    )
                ballot_data = many_models["poll_ballot"]
                ballot_poll_ids_per_user_id.setdefault(
                    meeting_user["user_id"], set()
                ).update({ballot["poll_id"] for ballot in ballot_data.values()})
        ballot_conflicts = self._get_conflicts_between_users(
            ballot_poll_ids_per_user_id
        )
        option_conflicts = self._get_conflicts_between_users(
            option_poll_ids_per_user_id
        )
        if len(ballot_conflicts):
            messages.append(
                f"among the selected users multiple voted in poll(s) {', '.join([str(id_) for id_ in ballot_conflicts])}"
            )
        if len(option_conflicts):
            messages.append(
                f"multiple of the selected users are among the options in poll(s) {', '.join([str(id_) for id_ in option_conflicts])}"
            )

        if len(messages):
            raise ActionException(
                f"Cannot carry out merge into user/{into['id']}, because {' and '.join(messages)}"
            )

    def _get_conflicts_between_users(self, ids_map: dict[int, set[int]]) -> set[int]:
        seen_ids = set()
        duplicates = set()
        for ids in ids_map.values():
            for id_ in ids:
                if id_ in seen_ids:
                    duplicates.add(id_)
                else:
                    seen_ids.add(id_)
        return duplicates
