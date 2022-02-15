from typing import Any, Dict, List, Type, cast

from openslides_backend.models.models import Meeting

from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
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
from .mixins import MeetingPermissionMixin


@register_action("meeting.create")
class MeetingCreate(CreateActionWithDependencies, MeetingPermissionMixin):
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
        },
    )
    dependencies = [
        MotionWorkflowCreateSimpleWorkflowAction,
        MotionWorkflowCreateComplexWorkflowAction,
        ProjectorCreateAction,
    ]
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        committee = self.datastore.get(
            FullQualifiedId(Collection("committee"), instance["committee_id"]),
            ["user_ids", "organization_id"],
        )
        organization = self.datastore.get(
            FullQualifiedId(Collection("organization"), committee["organization_id"]),
            ["limit_of_meetings", "active_meeting_ids"],
        )
        if (
            limit_of_meetings := organization.get("limit_of_meetings", 0)
        ) and limit_of_meetings == len(organization.get("active_meeting_ids", [])):
            raise ActionException(
                f"You cannot create a new meeting, because you reached your limit of {limit_of_meetings} active meetings."
            )

        instance["is_active_in_organization_id"] = committee["organization_id"]
        self.apply_instance(instance)
        action_data = [
            {
                "name": "Default",
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
                "name": "Admin",
                "meeting_id": instance["id"],
            },
            {
                "name": "Delegates",
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
                "name": "Staff",
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
                "name": "Committees",
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

        fqid_default_group = FullQualifiedId(
            Collection("group"), action_results[0]["id"]  # type: ignore
        )
        fqid_admin_group = FullQualifiedId(Collection("group"), action_results[1]["id"])  # type: ignore
        fqid_delegates_group = FullQualifiedId(Collection("group"), action_results[2]["id"])  # type: ignore
        assert (
            self.datastore.additional_relation_models[fqid_default_group]["name"]
            == "Default"
        )
        assert (
            self.datastore.additional_relation_models[fqid_admin_group]["name"]
            == "Admin"
        )
        assert (
            self.datastore.additional_relation_models[fqid_delegates_group]["name"]
            == "Delegates"
        )

        instance["default_group_id"] = fqid_default_group.id
        instance["admin_group_id"] = fqid_admin_group.id
        instance["assignment_poll_default_group_ids"] = [fqid_delegates_group.id]
        instance["motion_poll_default_group_ids"] = [fqid_delegates_group.id]

        # Add user to admin group
        if admin_ids := instance.pop("admin_ids", []):
            action_data = [
                {
                    "id": user_id,
                    "group_$_ids": {str(instance["id"]): [fqid_admin_group.id]},
                }
                for user_id in admin_ids
            ]
            self.execute_other_action(UserUpdate, action_data)

        # Add users to default group
        if user_ids := instance.pop("user_ids", []):
            action_data = [
                {
                    "id": user_id,
                    "group_$_ids": {str(instance["id"]): [fqid_default_group.id]},
                }
                for user_id in user_ids
                if user_id not in admin_ids
            ]

            self.execute_other_action(UserUpdate, action_data)
        self.apply_instance(instance)

        action_data_countdowns = [
            {
                "title": "List of speakers countdown",
                "meeting_id": instance["id"],
            },
            {
                "title": "Voting countdown",
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
                    "name": "Simple Workflow",
                    "default_workflow_meeting_id": instance["id"],
                    "default_amendment_workflow_meeting_id": instance["id"],
                    "default_statute_amendment_workflow_meeting_id": instance["id"],
                    "meeting_id": instance["id"],
                }
            ]
        elif CreateActionClass == MotionWorkflowCreateComplexWorkflowAction:
            return [
                {
                    "name": "Complex Workflow",
                    "meeting_id": instance["id"],
                }
            ]
        elif CreateActionClass == ProjectorCreateAction:
            return [
                {
                    "name": "Default projector",
                    "meeting_id": instance["id"],
                    "used_as_reference_projector_meeting_id": instance["id"],
                    "used_as_default_$_in_meeting_id": {
                        name: instance["id"]
                        for name in cast(
                            List[str], Meeting.default_projector__id.replacement_enum
                        )
                    },
                }
            ]
        return []
