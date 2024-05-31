from typing import Any

from openslides_backend.services.datastore.interface import PartialModel

from ....models.models import (
    AssignmentCandidate,
    MeetingUser,
    MotionEditor,
    MotionSubmitter,
    MotionWorkingGroupSpeaker,
    PersonalNote,
)
from ....services.datastore.commands import GetManyRequest
from ....shared.patterns import Collection, CollectionField
from .base_merge_mixin import BaseMergeMixin, MergeModeDict


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
        )


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
            MotionSubmitter,
            {
                "ignore": ["meeting_user_id"],
                "lowest": [
                    "weight",
                ],
                "priority": ["meeting_id", "motion_id"],
            },
        )


class MotionEditorMergeMixin(BaseMergeMixin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            MotionEditor,
            motion_meeting_user_list_item_groups,
        )


class MotionWorkingGroupSpeakerMergeMixin(BaseMergeMixin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            MotionWorkingGroupSpeaker,
            motion_meeting_user_list_item_groups,
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
        )


class MeetingUserMergeMixin(
    PersonalNoteMergeMixin,
    MotionWorkingGroupSpeakerMergeMixin,
    MotionEditorMergeMixin,
    MotionSubmitterMergeMixin,
    AssignmentCandidateMergeMixin,
):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            MeetingUser,
            {
                "ignore": [
                    "user_id",
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
                    "supported_motion_ids",
                    "vote_delegations_from_ids",
                    "chat_message_ids",
                    "group_ids",
                    "structure_level_ids",
                ],
                "deep_merge": {
                    "assignment_candidate_ids": "assignment_candidate",
                    "personal_note_ids": "personal_note",
                    "motion_editor_ids": "motion_editor",
                    "motion_working_group_speaker_ids": "motion_working_group_speaker",
                },
                "deep_create_merge": {
                    "motion_submitter_ids": "motion_submitter",
                },
                "special_function": [
                    "speaker_ids",  # TODO: what should happen here?
                ],
            },
        )

    def handle_special_field(
        self,
        collection: Collection,
        field: CollectionField,
        into_: PartialModel,
        ranked_others: list[PartialModel],
    ) -> Any | None:
        if collection == "meeting_user" and field == "speaker_ids":
            pass  # TODO: Do smth here
            # Deep merge speakers but only of the same type?
        return super().handle_special_field(collection, field, into_, ranked_others)

    def get_merge_comparison_hash(
        self, collection: Collection, model: PartialModel
    ) -> int | str:
        match collection:
            case "motion_submitter":
                return model["motion_id"]
            case "assignment_candidate":
                return model["assignment_id"]
            case "personal_note":
                return model["content_object_id"]
            case "motion_editor":
                return model["motion_id"]
            case "motion_working_group_speaker":
                return model["motion_id"]
            case _:
                return super().get_merge_comparison_hash(collection, model)

    def check_polls_helper(self, meeting_user_ids: list[int]) -> list[str]:
        meeting_users = self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting_user",
                    meeting_user_ids,
                    ["vote_delegations_from_ids", "vote_delegated_to_id", "meeting_id"],
                )
            ]
        ).get("meeting_user", {})
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
        messages: list[str] = []
        if len(delegation_conflicts):
            messages.append(
                f"some of the selected users have different delegations roles in meeting(s) {', '.join(delegation_conflicts)}"
            )
        if len(
            bad_users := [
                id_
                for id_ in meeting_user_ids
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
        if len(
            circular_ids := delegator_meeting_user_ids.intersection(
                proxy_meeting_user_ids
            )
        ):
            bad_meeting_users = self.datastore.get_many(
                [GetManyRequest("meeting_user", list(circular_ids), ["meeting_id"])]
            ).get("meeting_user", {})
            bad_meetings = {
                str(meeting_id)
                for meeting_user in bad_meeting_users.values()
                if (meeting_id := meeting_user.get("meeting_id"))
            }
            messages.append(
                f"it would create circular delegations in meeting(s) {', '.join(bad_meetings)}"
            )
        return messages
