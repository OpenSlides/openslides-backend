from typing import Any, Dict

from ....models.models import Committee
from ....permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)
from ....permissions.permission_helper import (
    has_committee_management_level,
    has_organization_management_level,
)
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.filters import FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..user.update import UserUpdate
from .committee_common_mixin import CommitteeCommonCreateUpdateMixin


@register_action("committee.update")
class CommitteeUpdateAction(CommitteeCommonCreateUpdateMixin, UpdateAction):
    """
    Action to update a committee.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_update_schema(
        optional_properties=[
            "name",
            "description",
            "template_meeting_id",
            "default_meeting_id",
            "user_ids",
            "forward_to_committee_ids",
            "receive_forwardings_from_committee_ids",
            "organization_tag_ids",
        ],
        additional_optional_fields={"manager_ids": id_list_schema},
    )

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        for instance in action_data:
            instance = super().update_instance(instance)
            if instance.get("template_meeting_id"):
                self.check_meeting_in_committee(
                    instance["template_meeting_id"], instance["id"]
                )
            if instance.get("default_meeting_id"):
                self.check_meeting_in_committee(
                    instance["default_meeting_id"], instance["id"]
                )
            if "manager_ids" in instance:
                new_manager_ids = set(instance.pop("manager_ids"))
                filter_ = FilterOperator(
                    f"committee_${instance['id']}_management_level",
                    "=",
                    CommitteeManagementLevel.CAN_MANAGE,
                )
                old_manager = self.datastore.filter(Collection("user"), filter_, ["id"])
                old_manager_ids = set(int(id_) for id_ in old_manager)

                action_data = []
                for manager_id in new_manager_ids - old_manager_ids:
                    action_data.append(
                        {
                            "id": manager_id,
                            "committee_$_management_level": {
                                str(
                                    instance["id"]
                                ): CommitteeManagementLevel.CAN_MANAGE,
                            },
                        }
                    )
                for manager_id in old_manager_ids - new_manager_ids:
                    action_data.append(
                        {
                            "id": manager_id,
                            "committee_$_management_level": {str(instance["id"]): None},
                        }
                    )
                if action_data:
                    self.execute_other_action(UserUpdate, action_data)
            if any(key for key in instance if key != "id"):
                yield instance

    def check_meeting_in_committee(self, meeting_id: int, committee_id: int) -> None:
        meeting = self.datastore.get(
            FullQualifiedId(Collection("meeting"), meeting_id), ["committee_id"]
        )
        if meeting.get("committee_id") != committee_id:
            raise ActionException(
                f"Meeting {meeting_id} does not belong to committee {committee_id}"
            )

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if has_organization_management_level(
            self.datastore,
            self.user_id,
            OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION,
        ):
            return

        if any(
            [
                field in instance
                for field in [
                    "user_ids",
                    "forward_to_committee_ids",
                    "receive_forwardings_from_committee_ids",
                    "manager_ids",
                ]
            ]
        ):
            raise MissingPermission(OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION)

        if has_committee_management_level(
            self.datastore,
            self.user_id,
            CommitteeManagementLevel.CAN_MANAGE,
            instance["id"],
        ):
            return

        raise MissingPermission(
            {
                OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION: 1,
                CommitteeManagementLevel.CAN_MANAGE: instance["id"],
            }
        )
