from typing import TypedDict, Union

from ...shared.patterns import FullQualifiedField, Identifier, IdentifierList


class FieldUpdateElement(TypedDict):
    type: str
    value: Identifier | IdentifierList | None
    modified_element: Identifier


class ListUpdateElement(TypedDict):
    type: str
    add: IdentifierList
    remove: IdentifierList


RelationUpdateElement = Union[FieldUpdateElement, ListUpdateElement]
RelationFieldUpdates = dict[FullQualifiedField, FieldUpdateElement]
RelationUpdates = dict[FullQualifiedField, RelationUpdateElement]
