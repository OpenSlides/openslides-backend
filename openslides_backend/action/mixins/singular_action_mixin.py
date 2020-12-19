import fastjsonschema

from ...shared.exceptions import ActionException
from ...shared.schema import schema_version
from ..action import Action
from ..util.typing import ActionPayload

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
    Mixin to ensure that the action payload contains only on object.
    """

    is_singular = True

    def get_updated_instances(self, payload: ActionPayload) -> ActionPayload:
        self.assert_singular_payload(payload)
        return super().get_updated_instances(payload)

    def assert_singular_payload(self, payload: ActionPayload) -> None:
        try:
            singular_schema(payload)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)
