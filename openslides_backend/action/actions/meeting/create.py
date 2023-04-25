from typing import Any, Dict, List, Type, cast

from openslides_backend.models.models import Meeting

from ....i18n.translator import Translator
from ....i18n.translator import translate as _
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import fqid_from_collection_and_id, id_from_fqid
from ....shared.schema import id_list_schema
from ...action import Action
from ...mixins.create_action_with_dependencies import CreateActionWithDependencies
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ..group.create import GroupCreate
from ..motion_workflow.create import (
    MotionWorkflowCreateComplexWorkflowAction,
    MotionWorkflowCreateSimpleWorkflowAction,
)
from ..projector.create import ProjectorCreateAction
from ..projector_countdown.create import ProjectorCountdownCreate
from ..user.update import UserUpdate
from .mixins import MeetingCheckTimesMixin, MeetingPermissionMixin


@register_action("meeting.create")
class MeetingCreate(
    CreateActionWithDependencies, MeetingPermissionMixin, MeetingCheckTimesMixin
):
    model = Meeting()
    schema = DefaultSchema(Meeting()).get_create_schema(
        required_properties=["committee_id", "name"],
        optional_properties=[
            "description",
            "location",
            "start_time",
            "end_time",
            "organization_tag_ids",
        ],
        additional_optional_fields={
            "user_ids": id_list_schema,
            "admin_ids": id_list_schema,
            "set_as_template": {"type": "boolean"},
        },
        additional_required_fields={
            "language": {"type": "string"},
        },
    )
    dependencies = [
        MotionWorkflowCreateSimpleWorkflowAction,
        MotionWorkflowCreateComplexWorkflowAction,
        ProjectorCreateAction,
    ]
    skip_archived_meeting_check = True
    translation_of_defaults = [
        "name",
        "description",
        "welcome_title",
        "welcome_text",
        "motion_preamble",
        "motions_export_title",
        "assignments_export_title",
        "users_pdf_welcometitle",
        "users_pdf_welcometext",
        "users_email_sender",
        "users_email_subject",
        "users_email_body",
    ]

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        Translator.set_translation_language(instance["language"])
        instance = super().update_instance(instance)
        # handle set_as_template
        if instance.pop("set_as_template", None):
            instance["template_for_organization_id"] = 1

        committee = self.datastore.get(
            fqid_from_collection_and_id("committee", instance["committee_id"]),
            ["user_ids", "organization_id"],
        )
        organization = self.datastore.get(
            fqid_from_collection_and_id("organization", committee["organization_id"]),
            ["limit_of_meetings", "active_meeting_ids"],
        )
        if (
            limit_of_meetings := organization.get("limit_of_meetings", 0)
        ) and limit_of_meetings == len(organization.get("active_meeting_ids", [])):
            raise ActionException(
                f"You cannot create a new meeting, because you reached your limit of {limit_of_meetings} active meetings."
            )
        self.check_start_and_end_time(instance)

        instance["is_active_in_organization_id"] = committee["organization_id"]
        self.apply_instance(instance)
        action_data = [
            {
                "name": _("Default"),
                "meeting_id": instance["id"],
                "permissions": [
                    Permissions.AgendaItem.CAN_SEE_INTERNAL,
                    Permissions.Assignment.CAN_SEE,
                    Permissions.ListOfSpeakers.CAN_SEE,
                    Permissions.Mediafile.CAN_SEE,
                    Permissions.Meeting.CAN_SEE_FRONTPAGE,
                    Permissions.Motion.CAN_SEE,
                    Permissions.Projector.CAN_SEE,
                    Permissions.User.CAN_SEE,
                ],
            },
            {
                "name": _("Admin"),
                "meeting_id": instance["id"],
            },
            {
                "name": _("Delegates"),
                "meeting_id": instance["id"],
                "permissions": [
                    Permissions.AgendaItem.CAN_SEE_INTERNAL,
                    Permissions.Assignment.CAN_NOMINATE_OTHER,
                    Permissions.Assignment.CAN_NOMINATE_SELF,
                    Permissions.ListOfSpeakers.CAN_BE_SPEAKER,
                    Permissions.Mediafile.CAN_SEE,
                    Permissions.Meeting.CAN_SEE_AUTOPILOT,
                    Permissions.Meeting.CAN_SEE_FRONTPAGE,
                    Permissions.Motion.CAN_CREATE,
                    Permissions.Motion.CAN_CREATE_AMENDMENTS,
                    Permissions.Motion.CAN_SUPPORT,
                    Permissions.Projector.CAN_SEE,
                    Permissions.User.CAN_SEE,
                ],
            },
            {
                "name": _("Staff"),
                "meeting_id": instance["id"],
                "permissions": [
                    Permissions.AgendaItem.CAN_MANAGE,
                    Permissions.Assignment.CAN_MANAGE,
                    Permissions.Assignment.CAN_NOMINATE_SELF,
                    Permissions.ListOfSpeakers.CAN_BE_SPEAKER,
                    Permissions.ListOfSpeakers.CAN_MANAGE,
                    Permissions.Mediafile.CAN_MANAGE,
                    Permissions.Meeting.CAN_SEE_FRONTPAGE,
                    Permissions.Meeting.CAN_SEE_HISTORY,
                    Permissions.Motion.CAN_MANAGE,
                    Permissions.Projector.CAN_MANAGE,
                    Permissions.Tag.CAN_MANAGE,
                    Permissions.User.CAN_MANAGE,
                ],
            },
            {
                "name": _("Committees"),
                "meeting_id": instance["id"],
                "permissions": [
                    Permissions.AgendaItem.CAN_SEE_INTERNAL,
                    Permissions.Assignment.CAN_SEE,
                    Permissions.ListOfSpeakers.CAN_SEE,
                    Permissions.Mediafile.CAN_SEE,
                    Permissions.Meeting.CAN_SEE_FRONTPAGE,
                    Permissions.Motion.CAN_CREATE,
                    Permissions.Motion.CAN_CREATE_AMENDMENTS,
                    Permissions.Motion.CAN_SUPPORT,
                    Permissions.Projector.CAN_SEE,
                    Permissions.User.CAN_SEE,
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
                    "id": user_id,
                    "group_$_ids": {
                        str(instance["id"]): [id_from_fqid(fqid_admin_group)]
                    },
                }
                for user_id in admin_ids
            ]
            self.execute_other_action(UserUpdate, action_data)

        # Add users to default group
        if user_ids := instance.pop("user_ids", []):
            action_data = [
                {
                    "id": user_id,
                    "group_$_ids": {
                        str(instance["id"]): [id_from_fqid(fqid_default_group)]
                    },
                }
                for user_id in user_ids
                if user_id not in admin_ids
            ]

            self.execute_other_action(UserUpdate, action_data)
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
        self, instance: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> List[Dict[str, Any]]:
        if CreateActionClass == MotionWorkflowCreateSimpleWorkflowAction:
            return [
                {
                    "name": _("Simple Workflow"),
                    "default_workflow_meeting_id": instance["id"],
                    "default_amendment_workflow_meeting_id": instance["id"],
                    "default_statute_amendment_workflow_meeting_id": instance["id"],
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
                    "used_as_default_$_in_meeting_id": {
                        name: instance["id"]
                        for name in cast(
                            List[str], Meeting.default_projector__ids.replacement_enum
                        )
                    },
                }
            ]
        return []

    def set_defaults(self, instance: Dict[str, Any]) -> Dict[str, Any]:
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
