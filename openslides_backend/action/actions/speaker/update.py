from typing import Any

from openslides_backend.services.datastore.commands import GetManyRequest
from openslides_backend.shared.exceptions import ActionException

from ....models.models import Speaker
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.schema import optional_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .create import ANSWERABLE_STATES
from .mixins import CheckSpeechState, PointOfOrderPermissionMixin, StructureLevelMixin
from .speech_state import SpeechState


@register_action("speaker.update")
class SpeakerUpdate(
    UpdateAction, CheckSpeechState, StructureLevelMixin, PointOfOrderPermissionMixin
):

    internal_fields = ["weight", "structure_level_list_of_speakers_id"]

    model = Speaker()
    schema = DefaultSchema(Speaker()).get_update_schema(
        optional_properties=[
            "speech_state",
            "meeting_user_id",
            "point_of_order",
            "point_of_order_category_id",
            "note",
            "answer",
            *internal_fields,
        ],
        additional_optional_fields={"structure_level_id": optional_id_schema},
    )
    permission = Permissions.ListOfSpeakers.CAN_MANAGE

    def validate_fields(self, instance: dict[str, Any]) -> dict[str, Any]:
        if (not self.internal) and len(
            forbidden := {field for field in self.internal_fields if field in instance}
        ):
            raise ActionException(f"data must not contain {forbidden} properties")
        return super().validate_fields(instance)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        if self.internal:
            return instance
        if instance.get("speech_state") == SpeechState.INTERPOSED_QUESTION:
            raise ActionException(
                "You cannot set the speech state to interposed_question."
            )
        speaker = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            [
                "speech_state",
                "point_of_order",
                "meeting_id",
                "meeting_user_id",
                "begin_time",
                "list_of_speakers_id",
                "structure_level_list_of_speakers_id",
                "answer",
            ],
        )
        if "speech_state" in instance:
            if (
                (speaker.get("answer") and "answer" not in instance)
                or instance.get("answer")
            ) and instance["speech_state"] not in ANSWERABLE_STATES:
                raise ActionException(
                    "Cannot set speech_state to anything except interventions and interposed questions for answers."
                )
            elif (
                speaker.get("speech_state") == SpeechState.INTERPOSED_QUESTION
                and instance["speech_state"] != SpeechState.INTERPOSED_QUESTION
            ):
                raise ActionException(
                    "You cannot change the speech state of an interposed_question."
                )
            elif (
                speaker.get("speech_state") == SpeechState.INTERVENTION
                and instance["speech_state"] != SpeechState.INTERVENTION
            ):
                if not (
                    (
                        speaker.get("meeting_user_id")
                        and "meeting_user_id" not in instance
                    )
                    or instance.get("meeting_user_id")
                ):
                    raise ActionException(
                        "Cannot set interventions to other speech states without meeting_user_id."
                    )
        if instance.get("answer") and not (
            speaker.get("speech_state") in ANSWERABLE_STATES
            or instance.get("speech_state")
        ):
            raise ActionException(
                "Answer can only be set for interventions and interposed questions."
            )

        if "meeting_user_id" in instance:
            if (
                instance["meeting_user_id"] is None
                or speaker.get("meeting_user_id")
                or speaker.get("speech_state")
                not in [
                    SpeechState.INTERPOSED_QUESTION,
                    SpeechState.INTERVENTION,
                ]
            ):
                raise ActionException("You cannot set the meeting_user_id.")
        elif "structure_level_id" in instance and speaker.get("begin_time"):
            raise ActionException(
                "You can only update the structure level on a waiting speaker."
            )
        new_speech_state = (
            instance["speech_state"]
            if "speech_state" in instance
            else speaker.get("speech_state")
        )
        new_point_of_order_value = (
            instance["point_of_order"]
            if "point_of_order" in instance
            else speaker.get("point_of_order")
        )
        if speaker.get("begin_time"):
            if (
                "speech_state" in instance
                and speaker.get("speech_state") == SpeechState.INTERVENTION
            ):
                raise ActionException(
                    "You can not change the speech_state of a started intervention."
                )
            if instance.get("structure_level_id") or (
                speaker.get("structure_level_list_of_speakers_id")
                and "structure_level_id" not in instance
            ):
                if instance.get("point_of_order"):
                    raise ActionException(
                        "You can not change a started speaker to point_of_order if there is a structure_level."
                    )
                elif instance.get("speech_state") and instance.get(
                    "speech_state"
                ) not in [
                    SpeechState.CONTRIBUTION,
                    SpeechState.PRO,
                    SpeechState.CONTRA,
                ]:
                    raise ActionException(
                        f"You can not change a started speaker to {instance.get('speech_state')} if there is a structure_level."
                    )
        if new_speech_state and new_point_of_order_value:
            raise ActionException(
                "Speaker can't be point of order and another speech state at the same time."
            )

        requests = [
            GetManyRequest(
                "meeting",
                [speaker["meeting_id"]],
                [
                    "list_of_speakers_enable_point_of_order_speakers",
                    "list_of_speakers_can_create_point_of_order_for_others",
                    "list_of_speakers_enable_point_of_order_categories",
                ],
            ),
        ]
        if meeting_user_id := speaker.get("meeting_user_id"):
            requests.append(
                GetManyRequest("meeting_user", [meeting_user_id], ["user_id"])
            )
        result = self.datastore.get_many(requests)
        meeting = result["meeting"][speaker["meeting_id"]]
        if meeting_user_id:
            user_id = (
                result.get("meeting_user", {}).get(meeting_user_id, {}).get("user_id")
            )
        else:
            user_id = None
        self.check_point_of_order_fields(
            instance, meeting, user_id, speaker.get("point_of_order")
        )
        if "point_of_order" in instance and not instance["point_of_order"]:
            instance["point_of_order_category_id"] = None
            instance["note"] = None
        self.handle_structure_level(instance, speaker["list_of_speakers_id"])
        self.check_speech_state(speaker, instance, meeting_id=speaker["meeting_id"])
        return instance

    def check_permissions(self, instance: dict[str, Any]) -> None:
        speaker = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["meeting_user_id", "meeting_id"],
            lock_result=False,
        )
        if speaker.get("meeting_user_id"):
            meeting_user = self.datastore.get(
                fqid_from_collection_and_id("meeting_user", speaker["meeting_user_id"]),
                ["user_id"],
                lock_result=False,
            )
            if meeting_user.get("user_id") == self.user_id and (
                has_perm(
                    self.datastore,
                    self.user_id,
                    Permissions.ListOfSpeakers.CAN_SEE,
                    speaker["meeting_id"],
                )
                or has_perm(
                    self.datastore,
                    self.user_id,
                    Permissions.ListOfSpeakers.CAN_BE_SPEAKER,
                    speaker["meeting_id"],
                )
            ):
                return
        super().check_permissions(instance)
