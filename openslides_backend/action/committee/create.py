from ...models.committee import Committee
from ..action import register_action
from ..default_schema import DefaultSchema
from ..generics import CreateAction


@register_action("committee.create")
class CommitteeCreate(CreateAction):
    """
    Action to create committees.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_create_schema(
        properties=["organisation_id", "name"],
        required_properties=["organisation_id", "name"],
    )
