from typing import Any, Dict

from ...models.models import Speaker
from ..action_set import ActionSet
from ..default_schema import DefaultSchema
from ..generics import CreateAction, DeleteAction, UpdateAction
from ..register import register_action_set


class SpeakerCreateAction(CreateAction):
    """
    Create speaker Action with default weight.
    """

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance["weight"] = 10000
        return instance


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

    routes = {
        "create": SpeakerCreateAction,
        "delete": DeleteAction,
        "update": UpdateAction,
    }
