from datastore.shared.util.key_types import _collection_regex, _field_regex, _id_regex

from .patterns import DECIMAL_REGEX, FQID_REGEX, POSITIVE_NUMBER_REGEX
from .typing import Schema

schema_version = "http://json-schema.org/draft-07/schema#"


# jsonschemas for ids and fqids
required_id_schema: Schema = {"type": "integer", "minimum": 1}
optional_id_schema: Schema = {"type": ["integer", "null"], "minimum": 1}

required_fqid_schema: Schema = {
    "type": "string",
    "pattern": FQID_REGEX,
    "minLength": 1,
}
optional_fqid_schema: Schema = {
    "type": ["string", "null"],
    "pattern": FQID_REGEX,
    "minLength": 1,
}
required_str_schema: Schema = {
    "type": ["string"],
    "minLength": 1,
}
optional_str_schema: Schema = {
    "type": ["string", "null"],
    "minLength": 0,
}

base_list_schema: Schema = {
    "type": "array",
    "uniqueItems": True,
}
id_list_schema: Schema = {**base_list_schema, "items": required_id_schema}
fqid_list_schema: Schema = {**base_list_schema, "items": required_fqid_schema}
optional_str_list_schema: Schema = {**base_list_schema, "items": optional_str_schema}
str_list_schema: Schema = {**base_list_schema, "items": required_str_schema}

decimal_schema: Schema = {"type": "string", "pattern": DECIMAL_REGEX}
number_string_json_schema: Schema = {
    "type": "object",
    "patternProperties": {POSITIVE_NUMBER_REGEX: {"type": "string"}},
    "additionalProperties": False,
}
models_map_object: Schema = {
    "type": "object",
    "properties": {
        "_migration_index": {"type": "integer", "minimum": 1},
    },
    "patternProperties": {
        rf"^{_collection_regex}$": {
            "type": "object",
            "patternProperties": {
                rf"^{_id_regex}$": {
                    "type": "object",
                    "properties": {"id": {"type": "number"}},
                    "propertyNames": {"pattern": rf"^{_field_regex}$"},
                    "required": ["id"],
                    "additionalProperties": True,
                }
            },
            "additionalProperties": False,
        },
    },
    "required": ["_migration_index"],
    "additionalProperties": False,
}
