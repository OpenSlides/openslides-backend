from typing import Any

from openslides_backend.action.mixins.singular_action_mixin import SingularActionMixin
from openslides_backend.services.database.commands import GetManyRequest

from ....models.models import Speaker
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.filters import And, Filter, FilterOperator, Or
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...mixins.create_action_with_inferred_meeting import (
    CreateActionWithInferredMeeting,
)
from ...mixins.delegation_based_restriction_mixin import DelegationBasedRestrictionMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .mixins import CheckSpeechState, PointOfOrderPermissionMixin, StructureLevelMixin
from .sort import SpeakerSort
from .speech_state import SpeechState


@register_action("speaker.create")
class SpeakerCreateAction(
    SingularActionMixin,
    DelegationBasedRestrictionMixin,
    CheckSpeechState,
    CreateActionWithInferredMeeting,
    StructureLevelMixin,
    PointOfOrderPermissionMixin,
):
    model = Speaker()
    relation_field_for_meeting = "list_of_speakers_id"
    schema = DefaultSchema(Speaker()).get_create_schema(
        required_properties=["list_of_speakers_id"],
        optional_properties=[
            "meeting_user_id",
            "point_of_order",
            "note",
            "speech_state",
            "point_of_order_category_id",
        ],
        additional_optional_fields={"structure_level_id": required_id_schema},
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)

        self.handle_structure_level(instance)
        self.check_speech_state({}, instance)

        is_interposed_question = (
            instance.get("speech_state") == SpeechState.INTERPOSED_QUESTION
        )
        list_of_speakers_id = instance["list_of_speakers_id"]
        max_weight = self._get_max_weight(list_of_speakers_id, instance["meeting_id"])
        if max_weight is None:
            instance["weight"] = 1
            return instance

        if not instance.get("point_of_order") and not is_interposed_question:
            instance["weight"] = max_weight + 1
            return instance

        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", instance["meeting_id"]),
            [
                "list_of_speakers_enable_point_of_order_categories",
                "point_of_order_category_ids",
            ],
        )
        if is_interposed_question:
            min_weight = self._get_no_interposed_question_min(
                list_of_speakers_id, instance["meeting_id"]
            )
            if min_weight is None:
                instance["weight"] = max_weight + 1
                return instance

            instance["weight"] = min_weight
            speaker_ids = self._insert_before_weight(
                instance["id"],
                min_weight,
                list_of_speakers_id,
                instance["meeting_id"],
            )
        elif meeting.get("list_of_speakers_enable_point_of_order_categories"):
            # fetch point of order categories
            result = self.datastore.get_many(
                [
                    GetManyRequest(
                        "point_of_order_category",
                        meeting["point_of_order_category_ids"],
                        ["rank"],
                    )
                ]
            )
            categories = result.get("point_of_order_category", {})

            filter = And(
                FilterOperator("list_of_speakers_id", "=", list_of_speakers_id),
                FilterOperator("begin_time", "=", None),
                FilterOperator("meeting_id", "=", instance["meeting_id"]),
            )
            speakers = self.datastore.filter(
                self.model.collection,
                filter=filter,
                mapped_fields=[
                    "id",
                    "weight",
                    "point_of_order",
                    "point_of_order_category_id",
                ],
            )
            los = sorted(speakers.values(), key=lambda k: k["weight"])
            index = len(los) - 1
            new_speaker_rank = categories[instance["point_of_order_category_id"]][
                "rank"
            ]
            while index >= 0:
                speaker = los[index]
                if (
                    speaker.get("point_of_order")
                    and speaker.get("point_of_order_category_id")
                    and categories[speaker["point_of_order_category_id"]]["rank"]
                    <= new_speaker_rank
                ):
                    break
                index -= 1
            los.insert(index + 1, {"id": instance["id"]})
            speaker_ids = [speaker["id"] for speaker in los]
        else:
            weight_no_poos_min = self._get_no_poo_min(
                list_of_speakers_id, instance["meeting_id"]
            )
            if weight_no_poos_min is None:
                instance["weight"] = max_weight + 1
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
    ) -> list[int]:
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

    def _get_max_weight(self, list_of_speakers_id: int, meeting_id: int) -> int | None:
        return self.datastore.max(
            collection="speaker",
            filter=And(
                FilterOperator("list_of_speakers_id", "=", list_of_speakers_id),
                FilterOperator("begin_time", "=", None),
                FilterOperator("meeting_id", "=", meeting_id),
            ),
            field="weight",
        )

    def _get_no_poo_min(self, list_of_speakers_id: int, meeting_id: int) -> int | None:
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

    def _get_no_interposed_question_min(
        self, list_of_speakers_id: int, meeting_id: int
    ) -> int | None:
        return self.datastore.min(
            collection="speaker",
            filter=And(
                FilterOperator("list_of_speakers_id", "=", list_of_speakers_id),
                Or(
                    FilterOperator("speech_state", "=", None),
                    FilterOperator(
                        "speech_state", "!=", SpeechState.INTERPOSED_QUESTION
                    ),
                ),
                FilterOperator("begin_time", "=", None),
                FilterOperator("meeting_id", "=", meeting_id),
            ),
            field="weight",
        )

    def validate_fields(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Checks
        - that only the requesting user can file a point-of-order
        - that a new speaker does not already exist on the list of speaker as
        waiting speaker (with begin_time == None), but allows one additional with point_of_order speaker per user
        - that points_of_order are used in this meeting
        - that user has to be present to be added to the list of speakers
        - that request-user cannot create a speaker without being point_of_order, a not closed los is closed and no list_of_speakers.can_manage permission
        """
        if "meeting_user_id" in instance:
            meeting_user = self.datastore.get(
                fqid_from_collection_and_id(
                    "meeting_user", instance["meeting_user_id"]
                ),
                ["user_id"],
            )
            user_id = meeting_user["user_id"]
        else:
            if instance.get("speech_state") != SpeechState.INTERPOSED_QUESTION:
                raise ActionException("meeting_user_id is required.")
            user_id = None

        if instance.get("speech_state") and instance.get("point_of_order"):
            raise ActionException(
                "Speaker can't be point of order and another speech state at the same time."
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
                "list_of_speakers_can_create_point_of_order_for_others",
                "list_of_speakers_enable_point_of_order_categories",
                "list_of_speakers_present_users_only",
                "list_of_speakers_closing_disables_point_of_order",
                "list_of_speakers_allow_multiple_speakers",
            ],
        )
        self.check_point_of_order_fields(instance, meeting, user_id)

        if (
            (
                not instance.get("point_of_order")
                or meeting.get("list_of_speakers_closing_disables_point_of_order")
            )
            and los.get("closed")
            and user_id in (self.user_id, None)
            and not has_perm(
                self.datastore,
                self.user_id,
                Permissions.ListOfSpeakers.CAN_MANAGE,
                meeting_id,
            )
        ):
            raise ActionException("The list of speakers is closed.")

        if "meeting_user_id" in instance:
            if meeting.get("list_of_speakers_present_users_only"):
                user_fqid = fqid_from_collection_and_id("user", user_id)
                user = self.datastore.get(user_fqid, ["is_present_in_meeting_ids"])
                if meeting_id not in user.get("is_present_in_meeting_ids", ()):
                    raise ActionException(
                        "Only present users can be on the lists of speakers."
                    )

            if not meeting.get("list_of_speakers_allow_multiple_speakers"):
                # Results are necessary, because of getting a lock_result
                if instance.get("point_of_order"):
                    poo_filter: Filter = FilterOperator("point_of_order", "=", True)
                else:
                    poo_filter = Or(
                        FilterOperator("point_of_order", "=", False),
                        FilterOperator("point_of_order", "=", None),
                    )
                filter_obj = And(
                    FilterOperator(
                        "list_of_speakers_id", "=", instance["list_of_speakers_id"]
                    ),
                    FilterOperator("begin_time", "=", None),
                    FilterOperator("meeting_id", "=", meeting_id),
                    FilterOperator("meeting_user_id", "=", instance["meeting_user_id"]),
                    poo_filter,
                )
                if self.datastore.exists("speaker", filter_obj):
                    raise ActionException(
                        f"User {user_id} is already on the list of speakers."
                    )
        return super().validate_fields(instance)

    def check_permissions(self, instance: dict[str, Any]) -> None:
        meeting_id = self.get_meeting_id(instance)
        permission = Permissions.ListOfSpeakers.CAN_MANAGE
        if "meeting_user_id" in instance:
            meeting_user = self.datastore.get(
                fqid_from_collection_and_id(
                    "meeting_user", instance["meeting_user_id"]
                ),
                ["user_id"],
            )
            restricted = self.check_delegator_restriction(
                "users_forbid_delegator_in_list_of_speakers", [meeting_id]
            )
            if meeting_user.get("user_id") == self.user_id and not len(restricted):
                permission = Permissions.ListOfSpeakers.CAN_BE_SPEAKER

        if has_perm(self.datastore, self.user_id, permission, meeting_id):
            return
        raise MissingPermission(permission)
