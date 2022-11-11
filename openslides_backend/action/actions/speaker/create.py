from typing import Any, Dict, List, Optional

from ....models.models import Speaker
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.filters import And, FilterOperator, Or
from ....shared.patterns import fqid_from_collection_and_id
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .mixins import CheckSpeechState
from .sort import SpeakerSort


@register_action("speaker.create")
class SpeakerCreateAction(CheckSpeechState, CreateActionWithInferredMeeting):
    model = Speaker()
    relation_field_for_meeting = "list_of_speakers_id"
    schema = DefaultSchema(Speaker()).get_create_schema(
        required_properties=["list_of_speakers_id", "meeting_user_id"],
        optional_properties=["point_of_order", "note", "speech_state"],
    )

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        """
        Reason for this Exception: It's hard and specific doing the weight calculation
        of creating speakers with point of orders, because of the used max- and min-datastore methods.
        These should handle the still not generated speakers with specific filters.
        But we don't need this functionality
        """
        if len(action_data) > 1:  # type: ignore
            raise ActionException(
                "It is not permitted to create more than one speaker per request!"
            )
        yield from super().get_updated_instances(action_data)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)

        if "note" in instance and not instance.get("point_of_order"):
            raise ActionException("Not allowed to set note if not point of order.")

        self.check_speech_state({}, instance)
        weight_max = self._get_max_weight(
            instance["list_of_speakers_id"], instance["meeting_id"]
        )
        if weight_max is None:
            instance["weight"] = 1
            return instance

        if not instance.get("point_of_order"):
            instance["weight"] = weight_max + 1
            return instance

        list_of_speakers_id = instance["list_of_speakers_id"]
        weight_no_poos_min = self._get_no_poo_min(
            list_of_speakers_id, instance["meeting_id"]
        )
        if weight_no_poos_min is None:
            instance["weight"] = weight_max + 1
            return instance

        instance["weight"] = weight_no_poos_min
        speaker_ids = self._insert_before_weight(
            instance["id"],
            weight_no_poos_min,
            list_of_speakers_id,
            instance["meeting_id"],
        )
        self.apply_instance(instance)
        action_data = [
            {
                "list_of_speakers_id": list_of_speakers_id,
                "speaker_ids": speaker_ids,
            }
        ]
        self.execute_other_action(SpeakerSort, action_data)
        return instance

    def _insert_before_weight(
        self, new_id: int, weight: int, list_of_speakers_id: int, meeting_id: int
    ) -> List[int]:
        """
        We need to bild a list of speakers, sort them by weight and
        insert the new speaker before the entry with the weight from parameter
        """
        filter = And(
            FilterOperator("list_of_speakers_id", "=", list_of_speakers_id),
            FilterOperator("begin_time", "=", None),
            FilterOperator("meeting_id", "=", meeting_id),
        )
        speakers = self.datastore.filter(
            self.model.collection,
            filter=filter,
            mapped_fields=["id", "weight"],
        )
        los = sorted(speakers.values(), key=lambda k: k["weight"])
        list_to_sort = []
        for speaker in los:
            if speaker["weight"] == weight:
                list_to_sort.append(new_id)
            list_to_sort.append(speaker["id"])
        return list_to_sort

    def _get_max_weight(
        self, list_of_speakers_id: int, meeting_id: int
    ) -> Optional[int]:
        return self.datastore.max(
            collection="speaker",
            filter=And(
                FilterOperator("list_of_speakers_id", "=", list_of_speakers_id),
                FilterOperator("begin_time", "=", None),
                FilterOperator("meeting_id", "=", meeting_id),
            ),
            field="weight",
        )

    def _get_no_poo_min(
        self, list_of_speakers_id: int, meeting_id: int
    ) -> Optional[int]:
        return self.datastore.min(
            collection="speaker",
            filter=And(
                FilterOperator("list_of_speakers_id", "=", list_of_speakers_id),
                Or(
                    FilterOperator("point_of_order", "=", False),
                    FilterOperator("point_of_order", "=", None),
                ),
                FilterOperator("begin_time", "=", None),
                FilterOperator("meeting_id", "=", meeting_id),
            ),
            field="weight",
        )

    def validate_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks
        - that only the requesting user can file a point-of-order
        - that a new speaker does not already exist on the list of speaker as
        waiting speaker (with begin_time == None), but allows one additional with point_of_order speaker per user
        - that points_of_order are used in this meeting
        - that user has to be present to be added to the list of speakers
        - that request-user cannot create a speaker without being point_of_order, a not closed los is closed and no list_of_speakers.can_manage permission
        """
        meeting_user = self.datastore.get(
            fqid_from_collection_and_id("meeting_user", instance["meeting_user_id"]),
            ["user_id"],
        )
        if (
            instance.get("point_of_order")
            and meeting_user.get("user_id") != self.user_id
        ):
            raise ActionException(
                f"The requesting user {self.user_id} is not the user {meeting_user['user_id']} the point-of-order is filed for."
            )
        los_fqid = fqid_from_collection_and_id(
            "list_of_speakers", instance["list_of_speakers_id"]
        )
        los = self.datastore.get(los_fqid, ["meeting_id", "closed"])
        meeting_id = los["meeting_id"]
        meeting_fqid = fqid_from_collection_and_id("meeting", meeting_id)
        meeting = self.datastore.get(
            meeting_fqid,
            [
                "list_of_speakers_enable_point_of_order_speakers",
                "list_of_speakers_present_users_only",
            ],
        )
        if instance.get("point_of_order") and not meeting.get(
            "list_of_speakers_enable_point_of_order_speakers"
        ):
            raise ActionException(
                "Point of order speakers are not enabled for this meeting."
            )

        if (
            not instance.get("point_of_order")
            and los.get("closed")
            and meeting_user["user_id"] == self.user_id
            and not has_perm(
                self.datastore,
                self.user_id,
                Permissions.ListOfSpeakers.CAN_MANAGE,
                meeting_id,
            )
        ):
            raise ActionException("The list of speakers is closed.")
        if meeting.get("list_of_speakers_present_users_only"):
            user_fqid = fqid_from_collection_and_id("user", meeting_user["user_id"])
            user = self.datastore.get(user_fqid, ["is_present_in_meeting_ids"])
            if meeting_id not in user.get("is_present_in_meeting_ids", ()):
                raise ActionException(
                    "Only present users can be on the lists of speakers."
                )

        # Results are necessary, because of getting a lock_result
        filter_obj = And(
            FilterOperator("list_of_speakers_id", "=", instance["list_of_speakers_id"]),
            FilterOperator("begin_time", "=", None),
            FilterOperator("meeting_id", "=", meeting_id),
        )
        speakers = self.datastore.filter(
            collection="speaker",
            filter=filter_obj,
            mapped_fields=["meeting_user_id", "point_of_order"],
        )
        for speaker in speakers.values():
            if speaker["meeting_user_id"] == instance["meeting_user_id"] and bool(
                speaker.get("point_of_order")
            ) == bool(instance.get("point_of_order")):
                raise ActionException(
                    f"User {meeting_user['user_id']} is already on the list of speakers."
                )
        return super().validate_fields(instance)

    def check_permissions(self, instance: Dict[str, Any]) -> None:

        meeting_user = self.datastore.get(
            fqid_from_collection_and_id("meeting_user", instance["meeting_user_id"]),
            ["user_id"],
        )
        if meeting_user.get("user_id") == self.user_id:
            permission = Permissions.ListOfSpeakers.CAN_BE_SPEAKER
        else:
            permission = Permissions.ListOfSpeakers.CAN_MANAGE

        meeting_id = self.get_meeting_id(instance)
        if has_perm(self.datastore, self.user_id, permission, meeting_id):
            return
        raise MissingPermission(permission)
