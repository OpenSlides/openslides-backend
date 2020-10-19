from ...models.models import Speaker
from ..create_action_with_inferred_meeting import CreateActionWithInferredMeeting
from ..default_schema import DefaultSchema
from ..generics import DeleteAction, UpdateAction
from ..register import register_action


@register_action("speaker.create")
class SpeakerCreateAction(CreateActionWithInferredMeeting):
    model = Speaker()
    relation_field_for_meeting = "list_of_speakers_id"
    schema = DefaultSchema(Speaker()).get_create_schema(
        required_properties=["list_of_speakers_id", "user_id"],
        optional_properties=["marked"],
    )


@register_action("speaker.update")
class SpeakerUpdate(UpdateAction):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_update_schema(["marked"])


@register_action("speaker.delete")
class SpeakerDeleteAction(DeleteAction):
    model = Speaker()
    schema = DefaultSchema(Speaker()).get_delete_schema()
