from typing import Dict, List, Optional, TypedDict, Union

from ...shared.patterns import FullQualifiedField, FullQualifiedId

Identifier = Union[int, str, FullQualifiedId]
IdentifierList = Union[List[int], List[str], List[FullQualifiedId]]
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
