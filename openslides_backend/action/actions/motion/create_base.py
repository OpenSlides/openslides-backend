import time
from typing import Any, Dict

from ....models.models import Motion
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...mixins.create_action_with_dependencies import CreateActionWithDependencies
from ..agenda_item.agenda_creation import CreateActionWithAgendaItemMixin
from ..agenda_item.create import AgendaItemCreate
from ..list_of_speakers.create import ListOfSpeakersCreate
from ..list_of_speakers.list_of_speakers_creation import (
    CreateActionWithListOfSpeakersMixin,
)
from ..motion_submitter.create import MotionSubmitterCreateAction
from .sequential_numbers_mixin import SequentialNumbersMixin
from .set_number_mixin import SetNumberMixin


class MotionCreateBase(
    CreateActionWithDependencies,
    CreateActionWithAgendaItemMixin,
    SequentialNumbersMixin,
    SetNumberMixin,
    CreateActionWithListOfSpeakersMixin,
):

    model = Motion()
    dependencies = [AgendaItemCreate, ListOfSpeakersCreate]

    def set_state_from_workflow(
        self, instance: Dict[str, Any], meeting: Dict[str, Any]
    ) -> None:
        workflow_id = instance.pop("workflow_id", None)
        if workflow_id is None:
            if instance.get("lead_motion_id"):
                workflow_id = meeting.get("motions_default_amendment_workflow_id")
            elif instance.get("statute_paragraph_id"):
                workflow_id = meeting.get(
                    "motions_default_statute_amendment_workflow_id"
                )
            else:
                workflow_id = meeting.get("motions_default_workflow_id")
        if workflow_id:
            workflow = self.datastore.get(
                FullQualifiedId(Collection("motion_workflow"), workflow_id),
                ["first_state_id"],
            )
            instance["state_id"] = workflow.get("first_state_id")
        else:
            raise ActionException(
                "No matching default workflow defined on this meeting"
            )

    def create_submitters(self, instance: Dict[str, Any]) -> None:
        submitter_ids = instance.pop("submitter_ids", None)
        if not submitter_ids:
            submitter_ids = [self.user_id]
        self.apply_instance(instance)
        action_data = []
        for user_id in submitter_ids:
            action_data.append({"motion_id": instance["id"], "user_id": user_id})
        self.execute_other_action(MotionSubmitterCreateAction, action_data)

    def set_sequential_number(self, instance: Dict[str, Any]) -> None:
        instance["sequential_number"] = self.get_sequential_number(
            instance["meeting_id"]
        )

    def set_created_last_modified_and_number(self, instance: Dict[str, Any]) -> None:
        timestamp = round(time.time())
        instance["created"] = timestamp
        instance["last_modified"] = timestamp
        self.set_number(
            instance,
            instance["meeting_id"],
            instance["state_id"],
            instance.get("lead_motion_id"),
            instance.get("category_id"),
        )
