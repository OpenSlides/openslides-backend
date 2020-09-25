from ...models.assignment import Assignment
from ..action import register_action_set
from ..action_set import ActionSet
from ..agenda_item.agenda_creation import (
    CreateActionWithAgendaItem,
    agenda_creation_properties,
)
from ..default_schema import DefaultSchema
from ..generics import DeleteAction, UpdateAction

create_schema = DefaultSchema(Assignment()).get_create_schema(
    properties=[
        "title",
        "meeting_id",
        "description",
        "open_posts",
        "phase",
        "default_poll_description",
        "number_poll_candidates",
        "attachment_ids",
        "tag_ids",
    ],
    required_properties=["title", "meeting_id"],
)

create_schema["items"]["properties"].update(agenda_creation_properties)


@register_action_set("assignment")
class AssignmentActionSet(ActionSet):
    """
    Actions to create, update and delete assignments.
    """

    model = Assignment()
    create_schema = create_schema
    update_schema = DefaultSchema(Assignment()).get_update_schema(
        properties=[
            "title",
            "description",
            "open_posts",
            "phase",
            "default_poll_description",
            "number_poll_candidates",
            "attachment_ids",
            "tag_ids",
        ]
    )
    delete_schema = DefaultSchema(Assignment()).get_delete_schema()
    routes = {
        "create": CreateActionWithAgendaItem,
        "update": UpdateAction,
        "delete": DeleteAction,
    }
