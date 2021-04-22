import time
from typing import Any, Dict

from ....models.models import Motion
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ...mixins.create_action_with_dependencies import CreateActionWithDependencies
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..agenda_item.agenda_creation import CreateActionWithAgendaItemMixin
from ..agenda_item.create import AgendaItemCreate
from ..list_of_speakers.create import ListOfSpeakersCreate
from ..list_of_speakers.list_of_speakers_creation import (
    CreateActionWithListOfSpeakersMixin,
)
from ..motion_submitter.create import MotionSubmitterCreateAction
from .sequential_numbers_mixin import SequentialNumbersMixin
from .set_number_mixin import SetNumberMixin


@register_action("motion.create_forwarded")
class MotionCreateForwarded(
    CreateActionWithDependencies,
    CreateActionWithAgendaItemMixin,
    SequentialNumbersMixin,
    SetNumberMixin,
    CreateActionWithListOfSpeakersMixin,
):
    """
    Create action for forwarded motions.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_create_schema(
        optional_properties=[
            "reason",
        ],
        required_properties=["meeting_id", "title", "text", "origin_id"],
    )
    dependencies = [AgendaItemCreate, ListOfSpeakersCreate]

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
            [
                "motions_default_workflow_id",
            ],
        )

        # calculate state_id from workflow_id
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

        # check for origin_id
        if instance.get("origin_id"):
            meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
                ["committee_id"],
            )
            forwarded_from = self.datastore.get(
                FullQualifiedId(Collection("motion"), instance["origin_id"]),
                ["meeting_id"],
            )
            forwarded_from_meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), forwarded_from["meeting_id"]),
                ["committee_id"],
            )
            committee = self.datastore.get(
                FullQualifiedId(
                    Collection("committee"), forwarded_from_meeting["committee_id"]
                ),
                ["forward_to_committee_ids"],
            )
            if meeting["committee_id"] not in committee.get(
                "forward_to_committee_ids", []
            ):
                raise ActionException(
                    f"Committee id {meeting['committee_id']} not in {committee.get('forward_to_committee_ids', [])}"
                )

        # create submitters
        submitter_ids = [self.user_id]
        self.apply_instance(instance)
        action_data = []
        for user_id in submitter_ids:
            action_data.append({"motion_id": instance["id"], "user_id": user_id})
        self.execute_other_action(MotionSubmitterCreateAction, action_data)

        instance["sequential_number"] = self.get_sequential_number(
            instance["meeting_id"]
        )
        # set created and last_modified
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

        return instance
