from ....models.models import Committee
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
        optional_properties=["description", "member_ids", "manager_ids"],
    )
