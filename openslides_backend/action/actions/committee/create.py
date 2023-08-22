from ....models.models import Committee
from ....permissions.management_levels import OrganizationManagementLevel
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .committee_common_mixin import CommitteeCommonCreateUpdateMixin


@register_action("committee.create")
class CommitteeCreate(CommitteeCommonCreateUpdateMixin, CreateAction):
    """
    Action to create committees.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_create_schema(
        required_properties=["organization_id", "name"],
        optional_properties=[
            "description",
            "organization_tag_ids",
            "forward_to_committee_ids",
            "receive_forwardings_from_committee_ids",
            "manager_ids",
            "external_id",
        ],
    )
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
