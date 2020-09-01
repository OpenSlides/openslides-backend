from ...models.group import (  # noqa  # TODO: Remove this unused import after some group actions are installed.
    Group,
)
from ...models.meeting import Meeting
from ..action import register_action_set
from ..action_set import ActionSet
from ..default_schema import DefaultSchema


@register_action_set("meeting")
class MeetingActionSet(ActionSet):
    """
    Actions to create, update and delete meetings.
    """

    model = Meeting()
    create_schema = DefaultSchema(Meeting()).get_create_schema(
        properties=["committee_id", *Meeting().get_settings_keys()],
        required_properties=["committee_id", "name"],
    )
    update_schema = DefaultSchema(Meeting()).get_update_schema(
        properties=Meeting().get_settings_keys()
    )
    delete_schema = DefaultSchema(Meeting()).get_delete_schema()
