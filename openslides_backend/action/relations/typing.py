from typing import Dict, Optional, TypedDict, Union

from ...shared.patterns import FullQualifiedField, Identifier, IdentifierList

FieldUpdateElement = TypedDict(
    "FieldUpdateElement",
    {
        "type": str,
        "value": Optional[Union[Identifier, IdentifierList]],
        "modified_element": Identifier,
    },
)
ListUpdateElement = TypedDict(
    "ListUpdateElement",
    {
        "type": str,
        "add": IdentifierList,
        "remove": IdentifierList,
    },
)
RelationUpdateElement = Union[FieldUpdateElement, ListUpdateElement]
RelationFieldUpdates = Dict[FullQualifiedField, FieldUpdateElement]
RelationUpdates = Dict[FullQualifiedField, RelationUpdateElement]
