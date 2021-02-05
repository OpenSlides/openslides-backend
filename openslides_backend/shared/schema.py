from .patterns import FullQualifiedId
from .typing import Schema

schema_version = "http://json-schema.org/draft-07/schema#"


# jsonschemas for ids and fqids
required_id_schema: Schema = {"type": "integer", "minimum": 1}
optional_id_schema: Schema = {"type": ["integer", "null"], "minimum": 1}

required_fqid_schema: Schema = {
    "type": "string",
    "pattern": FullQualifiedId.REGEX,
    "minLength": 1,
}
optional_fqid_schema: Schema = {
    "type": ["string", "null"],
    "pattern": FullQualifiedId.REGEX,
    "minLength": 1,
}

base_list_schema: Schema = {
    "type": "array",
    "uniqueItems": True,
}
id_list_schema: Schema = {**base_list_schema, "items": required_id_schema}
fqid_list_schema: Schema = {**base_list_schema, "items": required_fqid_schema}

decimal_schema: Schema = {"type": "string", "pattern": r"^-?(\d|[1-9]\d+)\.\d{6}$"}
