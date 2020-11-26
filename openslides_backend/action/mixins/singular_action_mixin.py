import fastjsonschema

from ...shared.exceptions import ActionException
from ...shared.schema import schema_version
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


class SingularActionMixin:
    def assert_singular_payload(self, payload: ActionPayload) -> None:
        try:
            singular_schema(payload)
        except fastjsonschema.JsonSchemaException as exception:
            raise ActionException(exception.message)
