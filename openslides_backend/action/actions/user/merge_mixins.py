from openslides_backend.services.datastore.interface import PartialModel

from ....models.models import MeetingUser
from ....shared.patterns import Collection
from ..meeting_user.create import MeetingUserCreate
from ..meeting_user.delete import MeetingUserDelete
from ..meeting_user.update import MeetingUserUpdate
from .base_merge_mixin import BaseMergeMixin


class MeetingUserMergeMixin(BaseMergeMixin):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            MeetingUser,
            {
                "create": MeetingUserCreate,
                "update": MeetingUserUpdate,
                "delete": MeetingUserDelete,
            },
            {
                "ignore": [
                    "user_id",  # will be overwritten from user-side
                    "meeting_id",
                    "motion_editor_ids",
                    "motion_working_group_speaker_ids",
                ],
                "priority": [
                    "comment",
                    "number",
                    "about_me",
                    "vote_weight",
                    "vote_delegated_to_id",
                ],
                "merge": [
                    "supported_motion_ids",
                    "vote_delegations_from_ids",
                    "chat_message_ids",
                    "group_ids",
                    "structure_level_ids",
                ],
                "deep_merge": {
                    "motion_submitter_ids": "motion_submitter",
                    "assignment_candidate_ids": "assignment_candidate",
                    "personal_note_ids": "personal_note",
                },
                "special_function": [
                    "speaker_ids",
                ],
            },
        )

    def get_merge_comparison_hash(
        self, collection: Collection, model: PartialModel
    ) -> int | str:
        return super().get_merge_comparison_hash(collection, model)
