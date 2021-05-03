from typing import Any, Dict

from ....models.models import Committee
from ....permissions.management_levels import OrganisationManagementLevel
from ....permissions.permission_helper import has_organisation_management_level
from ....shared.exceptions import PermissionDenied
from ....shared.patterns import FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("committee.update")
class CommitteeUpdateAction(UpdateAction):
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
            "member_ids",
            "manager_ids",
            "forward_to_committee_ids",
            "receive_forwardings_from_committee_ids",
            "organisation_tag_ids",
        ]
    )

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        if has_organisation_management_level(
            self.datastore, self.user_id, OrganisationManagementLevel.SUPERADMIN
        ):
            return

        manager_ids = None
        if "manager_ids" in instance:
            manager_ids = instance["manager_ids"]
        else:
            committee = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["id"]), ["manager_ids"]
            )
            manager_ids = committee.get("manager_ids")
        if manager_ids is None:
            manager_ids = []
        is_manager = self.user_id in manager_ids
        can_manage_organisation = has_organisation_management_level(
            self.datastore,
            self.user_id,
            OrganisationManagementLevel.CAN_MANAGE_ORGANISATION,
        )
        if (
            any(
                [
                    field in instance
                    for field in [
                        "name",
                        "description",
                        "template_meeting_id",
                        "default_meeting_id",
                    ]
                ]
            )
            and not is_manager
        ):
            raise PermissionDenied("Not manager.")
        if (
            any(
                [
                    field in instance
                    for field in [
                        "member_ids",
                        "manager_ids",
                        "forward_to_committee_ids",
                        "receive_forwardings_from_committee_ids",
                    ]
                ]
            )
            and not can_manage_organisation
        ):
            raise PermissionDenied(
                f"Missing {OrganisationManagementLevel.CAN_MANAGE_ORGANISATION}"
            )
        if (
            "organisation_tag_ids" in instance
            and not is_manager
            and not can_manage_organisation
        ):
            raise PermissionDenied(
                f"Missing {OrganisationManagementLevel.CAN_MANAGE_ORGANISATION} and not manager."
            )
