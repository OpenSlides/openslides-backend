from typing import Any, Dict

from ...models.models import Motion
from ...shared.exceptions import ActionException
from ...shared.patterns import Collection, FullQualifiedId
from ..agenda_item.agenda_creation import (
    CreateActionWithAgendaItemMixin,
    agenda_creation_properties,
)
from ..agenda_item.create import AgendaItemCreate
from ..create_action_with_dependencies import CreateActionWithDependencies
from ..default_schema import DefaultSchema
from ..register import register_action


@register_action("motion.create")
class MotionCreate(CreateActionWithDependencies, CreateActionWithAgendaItemMixin):
    """
    Create Action for motions.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_create_schema(
        optional_properties=[
            "meeting_id",
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
    )
    schema["items"]["properties"].update({"workflow_id": {"type": ["integer", "null"]}})
    schema["items"]["properties"].update(agenda_creation_properties)
    dependencies = [AgendaItemCreate]

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        # calculate state_id from workflow_id
        workflow_id = instance.pop("workflow_id", None)
        if workflow_id is None:
            meeting = self.database.get(
                FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
                ["motions_default_workflow_id"],
            )
            workflow_id = meeting.get("motions_default_workflow_id")
        if workflow_id:
            workflow = self.database.get(
                FullQualifiedId(Collection("motion_workflow"), workflow_id),
                ["first_state_id"],
            )
            instance["state_id"] = workflow.get("first_state_id")
        else:
            raise ActionException("Cannot calculate state_id.")

        # check for origin_id
        if instance.get("origin_id"):
            meeting = self.database.get(
                FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
                ["committee_id"],
            )
            forwarded_from = self.database.get(
                FullQualifiedId(Collection("motion"), instance["origin_id"]),
                ["meeting_id"],
            )
            forwarded_from_meeting = self.database.get(
                FullQualifiedId(Collection("meeting"), forwarded_from["meeting_id"]),
                ["committee_id"],
            )
            committee = self.database.get(
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

        # special check logic
        if instance.get("lead_motion_id"):
            # amendment need either text (or amendment_paragraph_*) must be set
            # TODO add amendment_paragraph_* here
            if not instance.get("text"):
                raise ActionException(
                    "Text or amendment_paragraph is required in this context."
                )

        if (not instance.get("lead_motion_id")) and instance.get(
            "statute_paragraph_id"
        ):
            pass
        elif not instance.get("lead_motion_id") or instance.get("statute_paragraph_id"):
            if not instance.get("text"):
                raise ActionException("text is required in this context.")

        # TODO add amendment_paragraph_* here
        if (
            instance.get("text")
            or instance.get("lead_motion_id")
            or instance.get("statute_paragraph_id")
        ):
            if not instance.get("reason"):
                raise ActionException("reason is required in this context.")

        return instance
