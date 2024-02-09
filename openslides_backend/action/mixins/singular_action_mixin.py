import fastjsonschema

from ...shared.exceptions import ActionException
from ...shared.schema import schema_version
from ..action import Action, original_instances
from ..util.typing import ActionData

singular_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "array",
        "items": {
            "type": "object",
        },
        "minItems": 1,
        "maxItems": 1,
    }
)


class SingularActionMixin(Action):
    """
    Mixin to ensure that the action data contains only on object.
    """

    is_singular = True

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        self.assert_singular_action_data(action_data)
        return super().get_updated_instances(action_data)

    def assert_singular_action_data(self, action_data: ActionData) -> None:
        try:
            singular_schema(action_data)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)
