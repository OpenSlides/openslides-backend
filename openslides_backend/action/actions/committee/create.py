from ....models.models import Committee
from ....permissions.management_levels import OrganisationManagementLevel
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("committee.create")
class CommitteeCreate(CreateAction):
    """
    Action to create committees.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_create_schema(
        required_properties=["organisation_id", "name"],
        optional_properties=["description", "user_ids"],
    )
    permission = OrganisationManagementLevel.CAN_MANAGE_ORGANISATION
