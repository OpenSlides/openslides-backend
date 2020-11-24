from ...models.models import Committee
from ..default_schema import DefaultSchema
from ..generics import DeleteAction
from ..register import register_action


@register_action("committee.delete")
class CommitteeDeleteAction(DeleteAction):
    """
    Action to delete a committee.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_delete_schema()
