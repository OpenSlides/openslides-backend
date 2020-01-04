import fastjsonschema  # type: ignore

from ...models.topic import Topic
from ...utils.schema import schema_version

is_valid_new_topic = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "New topics schema",
        "description": "An array of new topics.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "title": Topic().get_schema("title"),
                "text": Topic().get_schema("text"),
                "attachments": Topic().get_schema("attachments"),
            },
            "required": ["title"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)


# is_valid_update_topic = fastjsonschema.compile(
#     {
#         "$schema": schema_version,
#         "title": "Update topics schema",
#         "description": "An array of topics to be updated.",
#         "type": "array",
#         "items": {
#             "type": "object",
#             "properties": {
#                 "id": Topic().get_schema("id"),
#                 "title": Topic().get_schema("title"),
#                 "text": Topic().get_schema("text"),
#                 "attachments": Topic().get_schema("attachments"),
#             },
#             "required": ["id"],
#         },
#         "minItems": 1,
#         "uniqueItems": True,
#     }
# )
