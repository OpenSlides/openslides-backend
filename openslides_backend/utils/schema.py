import fastjsonschema  # type: ignore

schema_version = "http://json-schema.org/draft-07/schema#"

action_view_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "title": "Schema for actions API",
        "description": "An array of actions.",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "action": {
                    "description": "Name of the action to be performed on the server",
                    "type": "string",
                    "minLength": 1,
                },
                "data": {
                    "description": "Data for the action",
                    "type": "array",
                    "items": {"type": "object"},
                    "minItems": 1,
                    "uniqueItems": True,
                },
            },
            "required": ["action", "data"],
        },
        "minItems": 1,
        "uniqueItems": True,
    }
)
