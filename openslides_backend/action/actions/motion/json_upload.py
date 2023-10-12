from ....models.models import Motion
from ....permissions.permissions import Permissions
from ....shared.schema import required_id_schema
from ...mixins.import_mixins import ImportState, JsonUploadMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("motion.json_upload")
class MotionJsonUpload(JsonUploadMixin):
    """
    Action to allow to upload a json. It is used as first step of an import.
    """

    model = Motion()
    schema = DefaultSchema(Motion()).get_default_schema(
        additional_required_fields={
            "data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        **model.get_properties(
                            "title",
                            "text",
                            "number",
                            "reason",
                        ),
                        # "submitters_verbose": str,
                        # "submitters_username": str,
                        # "supporters_verbose": str,
                        # "supporters_username": str,
                        # "category_name": str,
                        # "category_prefix": str,
                        # "tags": str,
                        # "block": str,
                        # "motion_amendment": str,
                    },
                    "required": ["title", "text"],
                    "additionalProperties": False,
                },
                "minItems": 1,
                "uniqueItems": False,
            },
            "meeting_id": required_id_schema,
        }
    )

    headers = [
        # {"property": "title", "type": "string"},
        # {"property": "text", "type": "string"},
        # {"property": "number", "type": "string", "is_object": True},
        # {"property": "reason", "type": "string"},
        # {"property": "submitters_verbose", "type": "string", "is_list": True},
        # {"property": "submitters_username", "type": "string", "is_object": True, "is_list": True},
        # {"property": "supporters_verbose", "type": "string", "is_list": True},
        # {"property": "supporters_usernames", "type": "string", "is_object": True, "is_list": True},
        # {"property": "category_name", "type": "string", "is_object": True},
        # {"property": "category_prefix", "type": "string"},
        # {"property": "tags", "type": "string", "is_object": True, "is_list": True},
        # {"property": "block", "type": "string", "is_object": True},
        # {"property": "motion_amendment", "type": "boolean", "is_object": True},
    ]
    permission = Permissions.Motion.CAN_MANAGE
    row_state: ImportState
