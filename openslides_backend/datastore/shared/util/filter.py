from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, Union

from openslides_backend.datastore.shared.typing import Field

from .self_validating_dataclass import SelfValidatingDataclass


@dataclass
class FilterOperator(SelfValidatingDataclass):
    field: Field
    operator: Literal["=", "!=", "<", ">", ">=", "<=", "~=", "%="]
    value: Any


@dataclass
class Not:
    not_filter: "Filter"


@dataclass
class And:
    and_filter: Sequence["Filter"]


@dataclass
class Or:
    or_filter: Sequence["Filter"]


Filter = Union[And, Or, Not, FilterOperator]


filter_definitions_schema = {
    "filter": {
        "anyOf": [
            {"$ref": "#/$defs/filter_operator"},
            {"$ref": "#/$defs/not_filter"},
            {"$ref": "#/$defs/and_filter"},
            {"$ref": "#/$defs/or_filter"},
        ],
    },
    "filter_operator": {
        "type": "object",
        "properties": {
            "field": {"type": "string"},
            "value": {},
            "operator": {
                "type": "string",
                "enum": ["=", "!=", "<", ">", ">=", "<=", "~=", "%="],
            },
        },
        "required": ["field", "value", "operator"],
    },
    "not_filter": {
        "type": "object",
        "properties": {"not_filter": {"$ref": "#/$defs/filter"}},
        "required": ["not_filter"],
    },
    "and_filter": {
        "type": "object",
        "properties": {
            "and_filter": {
                "type": "array",
                "items": {"$ref": "#/$defs/filter"},
            },
        },
        "required": ["and_filter"],
    },
    "or_filter": {
        "type": "object",
        "properties": {
            "or_filter": {
                "type": "array",
                "items": {"$ref": "#/$defs/filter"},
            },
        },
        "required": ["or_filter"],
    },
}
