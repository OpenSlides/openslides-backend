from typing import Any, Dict, Optional

from openslides_backend.action.actions.structure_level_list_of_speakers.create import (
    StructureLevelListOfSpeakersCreateAction,
)
from openslides_backend.services.datastore.commands import GetManyRequest

from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...action import Action


class CheckSpeechState(Action):
    def check_speech_state(
        self,
        speaker: Dict[str, Any],
        instance: Dict[str, Any],
        meeting_id: Optional[int] = None,
    ) -> None:
        # check speech_state
        if meeting_id is None:
            meeting_id = instance["meeting_id"]
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            [
                "list_of_speakers_can_set_contribution_self",
                "list_of_speakers_enable_pro_contra_speech",
                "list_of_speakers_enable_interposed_question",
                "list_of_speakers_intervention_time",
            ],
            lock_result=False,
        )
        has_can_manage = has_perm(
            self.datastore,
            self.user_id,
            Permissions.ListOfSpeakers.CAN_MANAGE,
            meeting_id,
        )
        allowed_self_contribution = has_can_manage or meeting.get(
            "list_of_speakers_can_set_contribution_self"
        )
        allowed_pro_contra = meeting.get("list_of_speakers_enable_pro_contra_speech")
        if speaker.get("speech_state") == instance.get("speech_state"):
            pass
        elif instance.get("speech_state") == "contribution":
            if not allowed_self_contribution:
                raise ActionException("Self contribution is not allowed.")
        elif instance.get("speech_state") in ["pro", "contra"]:
            if not allowed_pro_contra:
                raise ActionException("Pro/Contra is not enabled.")
        elif (
            speaker.get("speech_state") == "contribution"
            and instance.get("speech_state") is None
        ):
            if not allowed_self_contribution:
                raise ActionException("Self contribution is not allowed.")
        elif (
            speaker.get("speech_state") in ["pro", "contra"]
            and instance.get("speech_state") is None
        ):
            if not allowed_pro_contra:
                raise ActionException("Pro/Contra is not enabled.")
        elif instance.get("speech_state") in ("intervention", "interposed_question"):
            if instance.get("point_of_order"):
                raise ActionException(
                    "Point of order is not allowed for this speech state."
                )
            if (
                instance.get("speech_state") == "intervention"
                and meeting.get("list_of_speakers_intervention_time", 0) <= 0
            ):
                raise ActionException("Interventions are not enabled.")
            elif instance.get(
                "speech_state"
            ) == "interposed_question" and not meeting.get(
                "list_of_speakers_enable_interposed_question"
            ):
                raise ActionException("Interposed questions are not enabled.")


class StructureLevelMixin(Action):
    def handle_structure_level(
        self, instance: Dict[str, Any], list_of_speakers_id: Optional[int] = None
    ) -> None:
        if list_of_speakers_id is None:
            list_of_speakers_id = instance["list_of_speakers_id"]
        if "structure_level_id" in instance:
            if structure_level_id := instance.pop("structure_level_id"):
                # find the structure_level_list_of_speakers_id for this list_of_speakers and
                # structure_level by checking the intersection of the two relations
                result = self.datastore.get_many(
                    [
                        GetManyRequest(
                            "list_of_speakers",
                            [list_of_speakers_id],
                            ["structure_level_list_of_speakers_ids"],
                        ),
                        GetManyRequest(
                            "structure_level",
                            [structure_level_id],
                            ["structure_level_list_of_speakers_ids"],
                        ),
                    ]
                )
                los_model = result["list_of_speakers"][list_of_speakers_id]
                structure_level = result["structure_level"][structure_level_id]
                los_set = set(los_model.get("structure_level_list_of_speakers_ids", []))
                structure_level_set = set(
                    structure_level.get("structure_level_list_of_speakers_ids", [])
                )
                intersection = los_set.intersection(structure_level_set)
                if len(intersection) == 0:
                    # structure_level_list_of_speakers does not exist yet
                    action_results = self.execute_other_action(
                        StructureLevelListOfSpeakersCreateAction,
                        [
                            {
                                "list_of_speakers_id": list_of_speakers_id,
                                "structure_level_id": structure_level_id,
                            }
                        ],
                    )
                    assert action_results and action_results[0]
                    sllos_id = action_results[0]["id"]
                else:
                    sllos_id = intersection.pop()
            else:
                sllos_id = None
            instance["structure_level_list_of_speakers_id"] = sllos_id
