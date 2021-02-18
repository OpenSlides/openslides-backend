from typing import Any, Dict, List, Optional

from ....models.models import Speaker
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator, Or
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.delete import DeleteAction
from ...generics.update import UpdateAction
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionPayload
from .sort import SpeakerSort


@register_action("speaker.create")
class SpeakerCreateAction(CreateActionWithInferredMeeting):
    model = Speaker()
    relation_field_for_meeting = "list_of_speakers_id"
    schema = DefaultSchema(Speaker()).get_create_schema(
        required_properties=["list_of_speakers_id", "user_id"],
        optional_properties=["marked", "point_of_order"],
    )

    def get_updated_instances(self, payload: ActionPayload) -> ActionPayload:
        """
        Reason for this Exception: It's hard and specific doing the weight calculation
        of creating speakers with point of orders, because of the used max- and min-datastore methods.
        These should handle the still not generated speakers with specific filters.
        But we don't need this functionality
        """
        if len(payload) > 1:  # type: ignore
            raise ActionException(
                "It is not permitted to create more than one speaker per request!"
            )
        yield from super().get_updated_instances(payload)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        weight_max = self._get_max_weight(instance["list_of_speakers_id"])
        if weight_max is None:
            instance["weight"] = 1
            return instance

        if not instance.get("point_of_order"):
            instance["weight"] = weight_max + 1
            return instance

        list_of_speakers_id = instance["list_of_speakers_id"]
        weight_no_poos_min = self._get_no_poo_min(list_of_speakers_id)
        if weight_no_poos_min is None:
            instance["weight"] = weight_max + 1
            return instance

        instance["weight"] = weight_no_poos_min
        speaker_ids = self._insert_before_weight(
            instance["id"], weight_no_poos_min, list_of_speakers_id
        )
        additional_relation_models = {
            FullQualifiedId(self.model.collection, instance["id"]): instance
        }
        payload = [
            {
                "list_of_speakers_id": list_of_speakers_id,
                "speaker_ids": speaker_ids,
            }
        ]
        self.execute_other_action(SpeakerSort, payload, additional_relation_models)
        return instance

    def _insert_before_weight(
        self, new_id: int, weight: int, list_of_speakers_id: int
    ) -> List[int]:
        """
        We need to bild a list of speakers, sort them by weight and
        insert the new speaker before the entry with the weight from parameter
        """
        filter = And(
            FilterOperator("list_of_speakers_id", "=", list_of_speakers_id),
            FilterOperator("begin_time", "=", None),
        )
        speakers = self.datastore.filter(
            self.model.collection,
            filter=filter,
            mapped_fields=["id", "weight"],
            lock_result=True,
        )
        los = sorted(speakers.values(), key=lambda k: k["weight"])
        list_to_sort = []
        for speaker in los:
            if speaker["weight"] == weight:
                list_to_sort.append(new_id)
            list_to_sort.append(speaker["id"])
        return list_to_sort

    def _get_max_weight(self, list_of_speakers_id: int) -> Optional[int]:
        return self.datastore.max(
            collection=Collection("speaker"),
            filter=And(
                FilterOperator("list_of_speakers_id", "=", list_of_speakers_id),
                FilterOperator("begin_time", "=", None),
            ),
            field="weight",
            lock_result=True,
        )

    def _get_no_poo_min(self, list_of_speakers_id: int) -> Optional[int]:
        return self.datastore.min(
            collection=Collection("speaker"),
            filter=And(
                FilterOperator("list_of_speakers_id", "=", list_of_speakers_id),
                Or(
                    FilterOperator("point_of_order", "=", False),
                    FilterOperator("point_of_order", "=", None),
                ),
                FilterOperator("begin_time", "=", None),
            ),
            field="weight",
            lock_result=True,
        )

    def validate_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks
        - that only the requesting user can file a point-of-order
        - that a new speaker does not already exist on the list of speaker as
        waiting speaker (with begin_time == None), but allows one additional with point_of_order speaker per user
        - that points_of_order are used in this meeting
        - that user has to be present to be added to the list of speakers
        """
        if instance.get("point_of_order") and instance.get("user_id") != self.user_id:
            raise ActionException(
                f"The requesting user {self.user_id} is not the user {instance.get('user_id')} the point-of-order is filed for."
            )
        los_fqid = FullQualifiedId(
            Collection("list_of_speakers"), instance["list_of_speakers_id"]
        )
        los = self.datastore.get(los_fqid, ["meeting_id"])
        meeting_id = los["meeting_id"]
        meeting_fqid = FullQualifiedId(Collection("meeting"), meeting_id)
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
        if meeting.get("list_of_speakers_present_users_only"):
            user_fqid = FullQualifiedId(Collection("user"), instance["user_id"])
            user = self.datastore.get(user_fqid, ["is_present_in_meeting_ids"])
            if meeting_id not in user.get("is_present_in_meeting_ids", ()):
                raise ActionException(
                    "Only present users can be on the lists of speakers."
                )

        # Results are necessary, because of getting a lock_result
        filter_obj = And(
            FilterOperator("list_of_speakers_id", "=", instance["list_of_speakers_id"]),
            FilterOperator("begin_time", "=", None),
        )
        speakers = self.datastore.filter(
            collection=Collection("speaker"),
            filter=filter_obj,
            mapped_fields=["user_id", "point_of_order"],
            lock_result=True,
        )
        for speaker in speakers.values():
            if speaker["user_id"] == instance["user_id"] and bool(
                speaker.get("point_of_order")
            ) == bool(instance.get("point_of_order")):
                raise ActionException(
                    f"User {instance['user_id']} is already on the list of speakers."
                )
        return super().validate_fields(instance)


@register_action("speaker.update")
class SpeakerUpdate(UpdateAction):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_update_schema(["marked"])


@register_action("speaker.delete")
class SpeakerDeleteAction(DeleteAction):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_delete_schema()
