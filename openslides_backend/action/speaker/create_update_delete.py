from ...models.models import Speaker
from ..action_set import ActionSet
from ..create_action_with_inferred_meeting import (
    get_create_action_with_inferred_meeting,
)
from ..default_schema import DefaultSchema
from ..register import register_action_set


@register_action_set("speaker")
class SpeakerActionSet(ActionSet):
    """
    Actions to create, update and delete speaker.
    """

    model = Speaker()
    create_schema = DefaultSchema(Speaker()).get_create_schema(
        required_properties=["list_of_speakers_id", "user_id"],
        optional_properties=["marked"],
    )
    update_schema = DefaultSchema(Speaker()).get_update_schema(["marked"])
    delete_schema = DefaultSchema(Speaker()).get_delete_schema()

    CreateActionClass = get_create_action_with_inferred_meeting("list_of_speakers_id")
