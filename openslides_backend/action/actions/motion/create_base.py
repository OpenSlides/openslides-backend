import time
from typing import Any

from ....models.models import Motion
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id
from ...mixins.create_action_with_dependencies import CreateActionWithDependencies
from ...mixins.sequential_numbers_mixin import SequentialNumbersMixin
from ..agenda_item.agenda_creation import CreateActionWithAgendaItemMixin
from ..agenda_item.create import AgendaItemCreate
from ..list_of_speakers.create import ListOfSpeakersCreate
from ..list_of_speakers.list_of_speakers_creation import (
    CreateActionWithListOfSpeakersMixin,
)
from ..meeting_user.helper_mixin import MeetingUserHelperMixin
from ..motion_submitter.create import MotionSubmitterCreateAction
from ..motion_supporter.create import MotionSupporterCreateAction
from .mixins import set_workflow_timestamp_helper
from .set_number_mixin import SetNumberMixin


class MotionCreateBase(
    MeetingUserHelperMixin,
    CreateActionWithDependencies,
    CreateActionWithAgendaItemMixin,
    SequentialNumbersMixin,
    SetNumberMixin,
    CreateActionWithListOfSpeakersMixin,
):
    model = Motion()
    dependencies = [AgendaItemCreate, ListOfSpeakersCreate]

    def set_state_from_workflow(
        self, instance: dict[str, Any], meeting: dict[str, Any]
    ) -> None:
        workflow_id = instance.pop("workflow_id", None)
        if workflow_id is None:
            if instance.get("lead_motion_id"):
                workflow_id = meeting.get("motions_default_amendment_workflow_id")
            else:
                workflow_id = meeting.get("motions_default_workflow_id")
        if workflow_id:
            workflow = self.datastore.get(
                fqid_from_collection_and_id("motion_workflow", workflow_id),
                ["first_state_id"],
            )
            instance["state_id"] = workflow.get("first_state_id")
        else:
            raise ActionException(
                "No matching default workflow defined on this meeting"
            )

    def create_submitters(self, instance: dict[str, Any]) -> None:
        submitter_ids = instance.pop("submitter_ids", [])
        if not submitter_ids and not instance.get("additional_submitter"):
            submitter_ids = [self.user_id]
        self.apply_instance(instance)
        weight = 1
        for user_id in submitter_ids:
            meeting_user_id = self.create_or_get_meeting_user(
                instance["meeting_id"], user_id
            )
            data = {
                "motion_id": instance["id"],
                "meeting_user_id": meeting_user_id,
                "weight": weight,
            }
            weight += 1
            self.execute_other_action(
                MotionSubmitterCreateAction, [data], skip_history=True
            )

    def create_supporters(self, instance: dict[str, Any]) -> None:
        supporter_ids = instance.pop("supporter_meeting_user_ids", [])
        if supporter_ids:
            self.apply_instance(instance)
            self.execute_other_action(
                MotionSupporterCreateAction,
                [
                    {
                        "motion_id": instance["id"],
                        "meeting_user_id": meeting_user_id,
                    }
                    for meeting_user_id in supporter_ids
                ],
                skip_history=True,
            )

    def set_sequential_number(self, instance: dict[str, Any]) -> None:
        instance["sequential_number"] = self.get_sequential_number(
            instance["meeting_id"]
        )

    def set_created_last_modified_and_number(self, instance: dict[str, Any]) -> None:
        self.set_created_last_modified(instance)
        self.set_number(
            instance,
            instance["meeting_id"],
            instance["state_id"],
            instance.get("lead_motion_id"),
            instance.get("category_id"),
        )

    def set_created_last_modified(self, instance: dict[str, Any]) -> None:
        timestamp = round(time.time())
        set_workflow_timestamp_helper(self.datastore, instance, timestamp)
        instance["last_modified"] = timestamp
        instance["created"] = timestamp
