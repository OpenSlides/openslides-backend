from typing import Any

from openslides_backend.models.models import Meeting

from ....i18n.translator import Translator
from ....i18n.translator import translate as _
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id, id_from_fqid
from ....shared.schema import id_list_schema
from ....shared.util import ONE_ORGANIZATION_FQID, ONE_ORGANIZATION_ID
from ...action import Action
from ...mixins.create_action_with_dependencies import CreateActionWithDependencies
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..group.create import GroupCreate
from ..meeting_user.create import MeetingUserCreate
from ..motion_workflow.create import (
    MotionWorkflowCreateComplexWorkflowAction,
    MotionWorkflowCreateSimpleWorkflowAction,
)
from ..projector.create import ProjectorCreateAction
from ..projector_countdown.create import ProjectorCountdownCreate
from .mixins import MeetingCheckTimesMixin, MeetingPermissionMixin


@register_action("meeting.create")
class MeetingCreate(
    CreateActionWithDependencies,
    MeetingPermissionMixin,
    MeetingCheckTimesMixin,
):
    model = Meeting()
    schema = DefaultSchema(Meeting()).get_create_schema(
        required_properties=["committee_id", "name", "language"],
        optional_properties=[
            "description",
            "location",
            "start_time",
            "end_time",
            "organization_tag_ids",
            "external_id",
        ],
        additional_optional_fields={
            "user_ids": id_list_schema,
            "admin_ids": id_list_schema,
            "set_as_template": {"type": "boolean"},
        },
    )
    dependencies = [
        MotionWorkflowCreateSimpleWorkflowAction,
        MotionWorkflowCreateComplexWorkflowAction,
        ProjectorCreateAction,
    ]
    skip_archived_meeting_check = True
    translation_of_defaults = [
        "description",
        "welcome_title",
        "welcome_text",
        "motions_preamble",
        "motions_export_title",
        "assignments_export_title",
        "users_pdf_welcometitle",
        "users_pdf_welcometext",
        "users_email_sender",
        "users_email_subject",
        "users_email_body",
    ]

    def base_update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        Translator.set_translation_language(instance["language"])
        return super().base_update_instance(instance)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        # handle set_as_template
        if instance.pop("set_as_template", None):
            instance["template_for_organization_id"] = ONE_ORGANIZATION_ID

        organization = self.datastore.get(
            ONE_ORGANIZATION_FQID,
            ["limit_of_meetings", "active_meeting_ids"],
        )
        if (
            limit_of_meetings := organization.get("limit_of_meetings", 0)
        ) and limit_of_meetings == len(organization.get("active_meeting_ids", [])):
            raise ActionException(
                f"You cannot create a new meeting, because you reached your limit of {limit_of_meetings} active meetings."
            )
        self.check_start_and_end_time(instance)

        instance["is_active_in_organization_id"] = ONE_ORGANIZATION_ID
        self.apply_instance(instance)
        action_data = [
            {
                "name": _("Default"),
                "external_id": "Default",
                "meeting_id": instance["id"],
                "permissions": [
                    Permissions.AgendaItem.CAN_SEE,
                    Permissions.Assignment.CAN_SEE,
                    Permissions.Meeting.CAN_SEE_AUTOPILOT,
                    Permissions.Meeting.CAN_SEE_FRONTPAGE,
                    Permissions.Motion.CAN_SEE,
                    Permissions.Projector.CAN_SEE,
                ],
            },
            {
                "name": _("Admin"),
                "external_id": "Admin",
                "meeting_id": instance["id"],
            },
            {
                "name": _("Delegates"),
                "external_id": "Delegates",
                "meeting_id": instance["id"],
                "permissions": [
                    Permissions.AgendaItem.CAN_SEE,
                    Permissions.Assignment.CAN_SEE,
                    Permissions.ListOfSpeakers.CAN_SEE,
                    Permissions.ListOfSpeakers.CAN_BE_SPEAKER,
                    Permissions.Mediafile.CAN_SEE,
                    Permissions.Meeting.CAN_SEE_AUTOPILOT,
                    Permissions.Meeting.CAN_SEE_FRONTPAGE,
                    Permissions.Motion.CAN_SEE,
                    Permissions.Projector.CAN_SEE,
                ],
            },
            {
                "name": _("Staff"),
                "external_id": "Staff",
                "meeting_id": instance["id"],
                "permissions": [
                    Permissions.AgendaItem.CAN_MANAGE,
                    Permissions.Assignment.CAN_MANAGE,
                    Permissions.ListOfSpeakers.CAN_MANAGE,
                    Permissions.Mediafile.CAN_MANAGE,
                    Permissions.Meeting.CAN_SEE_FRONTPAGE,
                    Permissions.Meeting.CAN_SEE_AUTOPILOT,
                    Permissions.Motion.CAN_MANAGE,
                    Permissions.Projector.CAN_MANAGE,
                    Permissions.Tag.CAN_MANAGE,
                    Permissions.User.CAN_MANAGE,
                ],
            },
        ]
        action_results = self.execute_other_action(GroupCreate, action_data)

        fqid_default_group = fqid_from_collection_and_id("group", action_results[0]["id"])  # type: ignore
        fqid_admin_group = fqid_from_collection_and_id("group", action_results[1]["id"])  # type: ignore
        fqid_delegates_group = fqid_from_collection_and_id("group", action_results[2]["id"])  # type: ignore

        instance["default_group_id"] = id_from_fqid(fqid_default_group)
        instance["admin_group_id"] = id_from_fqid(fqid_admin_group)
        instance["assignment_poll_default_group_ids"] = [
            id_from_fqid(fqid_delegates_group)
        ]
        instance["motion_poll_default_group_ids"] = [id_from_fqid(fqid_delegates_group)]
        instance["topic_poll_default_group_ids"] = [id_from_fqid(fqid_delegates_group)]

        # Add user to admin group
        if admin_ids := instance.pop("admin_ids", []):
            action_data = [
                {
                    "meeting_id": instance["id"],
                    "user_id": user_id,
                    "group_ids": [id_from_fqid(fqid_admin_group)],
                }
                for user_id in admin_ids
            ]
            self.execute_other_action(MeetingUserCreate, action_data)

        # Add users to default group
        if user_ids := instance.pop("user_ids", []):
            action_data = [
                {
                    "meeting_id": instance["id"],
                    "user_id": user_id,
                    "group_ids": [id_from_fqid(fqid_default_group)],
                }
                for user_id in user_ids
                if user_id not in admin_ids
            ]
            self.execute_other_action(MeetingUserCreate, action_data)
        self.apply_instance(instance)

        action_data_countdowns = [
            {
                "title": _("Speaking time"),
                "meeting_id": instance["id"],
            },
            {
                "title": _("Voting"),
                "meeting_id": instance["id"],
            },
        ]
        action_results = self.execute_other_action(
            ProjectorCountdownCreate,
            action_data_countdowns,
        )
        instance["list_of_speakers_countdown_id"] = action_results[0]["id"]  # type: ignore
        instance["poll_countdown_id"] = action_results[1]["id"]  # type: ignore

        return instance

    def get_dependent_action_data(
        self, instance: dict[str, Any], CreateActionClass: type[Action]
    ) -> list[dict[str, Any]]:
        if CreateActionClass == MotionWorkflowCreateSimpleWorkflowAction:
            return [
                {
                    "name": _("Simple Workflow"),
                    "default_workflow_meeting_id": instance["id"],
                    "default_amendment_workflow_meeting_id": instance["id"],
                    "meeting_id": instance["id"],
                }
            ]
        elif CreateActionClass == MotionWorkflowCreateComplexWorkflowAction:
            return [
                {
                    "name": _("Complex Workflow"),
                    "meeting_id": instance["id"],
                }
            ]
        elif CreateActionClass == ProjectorCreateAction:
            return [
                {
                    "name": _("Default projector"),
                    "meeting_id": instance["id"],
                    "used_as_reference_projector_meeting_id": instance["id"],
                    **{
                        field: instance["id"]
                        for field in Meeting.reverse_default_projectors()
                    },
                }
            ]
        return []

    def set_defaults(self, instance: dict[str, Any]) -> dict[str, Any]:
        for field in self.model.get_fields():
            if (
                field.own_field_name not in instance.keys()
                and field.default is not None
            ):
                if field.own_field_name in self.translation_of_defaults:
                    instance[field.own_field_name] = _(field.default)
                else:
                    instance[field.own_field_name] = field.default
        return instance
