from ...models.models import Committee
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action


@register_action("committee.create")
class CommitteeCreate(CreateAction):
    """
    Action to create committees.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_create_schema(["organisation_id", "name"])
