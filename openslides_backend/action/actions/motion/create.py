import time
from typing import Any, Dict

from ....models.models import Motion
from ....permissions.permission_helper import has_perm
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException, PermissionDenied
from ....shared.patterns import POSITIVE_NUMBER_REGEX, Collection, FullQualifiedId
from ....shared.schema import id_list_schema, optional_id_schema
from ...mixins.create_action_with_dependencies import CreateActionWithDependencies
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..agenda_item.agenda_creation import (
    CreateActionWithAgendaItemMixin,
    agenda_creation_properties,
)
from ..agenda_item.create import AgendaItemCreate
from ..list_of_speakers.create import ListOfSpeakersCreate
from ..list_of_speakers.list_of_speakers_creation import (
    CreateActionWithListOfSpeakersMixin,
)
from ..motion_submitter.create import MotionSubmitterCreateAction
from .sequential_numbers_mixin import SequentialNumbersMixin
from .set_number_mixin import SetNumberMixin


@register_action("motion.create")
class MotionCreate(
    CreateActionWithDependencies,
    CreateActionWithAgendaItemMixin,
    SequentialNumbersMixin,
    SetNumberMixin,
    CreateActionWithListOfSpeakersMixin,
):
    """
    Create Action for motions.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_create_schema(
        optional_properties=[
            "title",
            "number",
            "state_extension",
            "sort_parent_id",
            "category_id",
            "block_id",
            "supporter_ids",
            "tag_ids",
            "attachment_ids",
            "origin_id",
            "text",
            "lead_motion_id",
            "statute_paragraph_id",
            "reason",
        ],
        required_properties=["meeting_id", "title"],
        additional_optional_fields={
            "workflow_id": optional_id_schema,
            "submitter_ids": id_list_schema,
            **Motion().get_property("amendment_paragraph_$", POSITIVE_NUMBER_REGEX),
            **agenda_creation_properties,
        },
    )
    dependencies = [AgendaItemCreate, ListOfSpeakersCreate]

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # special check logic
        if instance.get("lead_motion_id"):
            if instance.get("statute_paragraph_id"):
                raise ActionException(
                    "You can't give both of lead_motion_id and statute_paragraph_id."
                )
            if not instance.get("text") and not instance.get("amendment_paragraph_$"):
                raise ActionException(
                    "Text or amendment_paragraph_$ is required in this context."
                )
            if instance.get("text") and instance.get("amendment_paragraph_$"):
                raise ActionException(
                    "You can't give both of text and amendment_paragraph_$"
                )
            if instance.get("text") and "amendment_paragraph_$" in instance:
                del instance["amendment_paragraph_$"]
            if instance.get("amendment_paragraph_$") and "text" in instance:
                del instance["text"]
        else:
            if not instance.get("text"):
                raise ActionException("Text is required")
            if instance.get("amendment_paragraph_$"):
                raise ActionException(
                    "You can't give amendment_paragraph_$ in this context"
                )

        # fetch all needed settings and check reason
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
            [
                "motions_default_workflow_id",
                "motions_default_amendment_workflow_id",
                "motions_default_statute_amendment_workflow_id",
                "motions_reason_required",
            ],
        )
        if meeting.get("motions_reason_required") and not instance.get("reason"):
            raise ActionException("Reason is required")

        # calculate state_id from workflow_id
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
        submitter_ids = instance.pop("submitter_ids", None)
        if not submitter_ids:
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

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        # Check can create amendment if needed else check can_create
        if instance.get("lead_motion_id"):
            perm = Permissions.Motion.CAN_CREATE_AMENDMENTS
            if not has_perm(self.datastore, self.user_id, perm, instance["meeting_id"]):
                msg = f"You are not allowed to perform action {self.name}."
                msg += f" Missing permission: {perm}"
                raise PermissionDenied(msg)

        else:
            perm = Permissions.Motion.CAN_CREATE
            if not has_perm(self.datastore, self.user_id, perm, instance["meeting_id"]):
                msg = f"You are not allowed to perform action {self.name}."
                msg += f" Missing permission: {perm}"
                raise PermissionDenied(msg)

        # if not can manage whitelist the fields.
        perm = Permissions.Motion.CAN_MANAGE
        if not has_perm(self.datastore, self.user_id, perm, instance["meeting_id"]):
            whitelist = [
                "title",
                "text",
                "reason",
                "lead_motion_id",
                "amendment_paragraph_$",
                "category_id",
                "statute_paragraph_id",
                "workflow_id",
                "id",
                "meeting_id",
            ]
            if instance.get("lead_motion_id"):
                whitelist.append("motion_block_id")
            for field in instance:
                if field not in whitelist:
                    msg = f"You are not allowed to perform action {self.name}."
                    msg += f" Missing permission: {perm}"
                    raise PermissionDenied(msg)
