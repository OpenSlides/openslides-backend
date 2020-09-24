from ...models.meeting import Meeting
from ..action import register_action_set
from ..action_set import ActionSet
from ..default_schema import DefaultSchema

meeting_settings_keys = ["description", "location"]  # TODO: Update this list


@register_action_set("meeting")
class MeetingActionSet(ActionSet):
    """
    Actions to create, update and delete meetings.
    """

    model = Meeting()
    create_schema = DefaultSchema(Meeting()).get_create_schema(
        properties=["committee_id", *meeting_settings_keys],
        required_properties=["committee_id", "name"],
    )
    update_schema = DefaultSchema(Meeting()).get_update_schema(
        properties=meeting_settings_keys
    )
    delete_schema = DefaultSchema(Meeting()).get_delete_schema()
