from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

from fastjsonschema import JsonSchemaException  # type: ignore
from mypy_extensions import TypedDict

from ..models.base import Model
from ..models.fields import RelationMixin
from ..shared.exceptions import ActionException
from ..shared.interfaces import Database, Event, Permission, WriteRequestElement
from ..shared.patterns import Collection, FullQualifiedField, FullQualifiedId
from .actions_interface import Payload

DataSet = TypedDict("DataSet", {"position": int, "data": Any})


class Action:
    """
    Base class for actions.
    """

    model: Model

    schema: Callable[[Payload], None]

    position = 0

    def __init__(self, permission: Permission, database: Database) -> None:
        self.permission = permission
        self.database = database

    def perform(self, payload: Payload, user_id: int) -> Iterable[WriteRequestElement]:
        """
        Entrypoint to perform the action.
        """
        self.user_id = user_id
        self.validate(payload)
        dataset = self.prepare_dataset(payload)
        self.check_permission_on_dataset(dataset)
        return self.create_write_request_elements(dataset)

    def validate(self, payload: Payload) -> None:
        try:
            type(self).schema(payload)
        except JsonSchemaException as exception:
            raise ActionException(exception.message)

    def prepare_dataset(self, payload: Payload) -> DataSet:
        """
        Prepares dataset from payload. Also fires all necessary database
        queries.
        """
        raise NotImplementedError

    def check_permission_on_dataset(self, dataset: DataSet) -> None:
        """
        Checks permission in the middle of the action according to dataset. Can
        be used for extra checks. Just passes at default.
        """
        pass

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        """
        Takes dataset and creates write request elements that can be sent to event
        store.

        By default it calls self.create_element_write_request_element and uses
        get_references_updates() for references.
        """
        position = dataset["position"]
        for element in dataset["data"]:
            element_write_request_element = self.create_instance_write_request_element(
                position, element
            )
            for reference in self.get_references_updates(position, element):
                element_write_request_element = merge_write_request_elements(
                    (element_write_request_element, reference)
                )
            yield element_write_request_element

    def create_instance_write_request_element(
        self, position: int, element: Any
    ) -> WriteRequestElement:
        """
        Creates a write request element for one instance of the current model.
        """
        raise NotImplementedError

    def get_references_updates(
        self, position: int, element: Any
    ) -> Iterable[WriteRequestElement]:
        """
        Creates write request elements (with update events) for all references.
        """
        for fqfield, data in element["references"].items():
            event = Event(type="update", fqfields={fqfield: data["value"]})
            if data["type"] == "add":
                info_text = f"Object attached to {self.model}"
            else:
                # data["type"] == "remove"
                info_text = f"Object attachment to {self.model} reset"
            yield WriteRequestElement(
                events=[event],
                information={
                    FullQualifiedId(fqfield.collection, fqfield.id): [info_text]
                },
                user_id=self.user_id,
                locked_fields={fqfield: position},
            )

    def set_min_position(self, position: int) -> None:
        """
        Sets self.position to the new value position if this value is smaller
        than the old one. Sets it if it is the first call.
        """
        if self.position == 0:
            self.position = position
        else:
            self.position = min(position, self.position)

    def get_references(
        self,
        model: Model,
        id: int,
        obj: Dict[str, Any],
        fields: List[str],
        deletion_possible: bool = False,
    ) -> Dict[FullQualifiedField, Dict[str, Any]]:
        """
        Updates references of the given model for the given fields. Use it in
        prepare_dataset method.
        """
        # TODO: Use proper typing here.
        references = {}  # type: Dict[FullQualifiedField, Dict[str, Any]]

        for field in fields:
            model_field = model.get_field(field)
            if not isinstance(model_field, RelationMixin):
                raise ValueError(f"Field {field} is not a relation field.")

            value = obj.get(field)
            if value is None:
                ref_ids = []
            else:
                if model_field.is_single_reference():
                    ref_ids = [value]
                else:
                    # model_field.is_multiple_reference()
                    ref_ids = value
            if deletion_possible:
                add, remove = self.reference_diff(model, id, field, ref_ids)
            else:
                add = set(ref_ids)
                remove = set()
            refs, position = self.database.getMany(
                Collection(model_field.to),
                list(add | remove),
                mapped_fields=[model_field.related_name],
            )
            self.set_min_position(position)
            for ref_id, ref in refs.items():
                if ref_id in add:
                    ref_value = {
                        "type": "add",
                        "value": ref[model_field.related_name] + [id],
                    }
                else:
                    # ref_id in remove
                    new_value = ref[model_field.related_name]
                    new_value.remove(id)
                    ref_value = {
                        "type": "remove",
                        "value": new_value,
                    }
                fqfield = FullQualifiedField(
                    Collection(model_field.to), ref_id, model_field.related_name
                )
                references[fqfield] = ref_value
        return references

    def reference_diff(
        self, model: Model, id: int, field: str, ref_ids: List[int]
    ) -> Tuple[Set[int], Set[int]]:
        """
        Returns two sets of reference object ids. One with reference objects
        where the given object (represented by model and id) should be added
        and one with reference objects where it should be removed.
        """
        current_obj, position = self.database.get(
            FullQualifiedId(model.collection, id), mapped_fields=[field]
        )
        self.set_min_position(position)
        model_field = model.get_field(field)
        if model_field.is_single_reference():
            current_id = current_obj.get(field)
            if current_id is None:
                current_ids = set()
            else:
                current_ids = set([current_id])
        else:
            # model_field.is_multiple_reference()
            current_ids = set(current_obj.get(field, []))
        new_ids = set(ref_ids)
        add = new_ids - current_ids
        remove = current_ids - new_ids
        return (add, remove)


def merge_write_request_elements(
    write_request_elements: Iterable[WriteRequestElement],
) -> WriteRequestElement:
    """
    Merges the given write request elements to one big write request element.
    """
    events: List[Event] = []
    information: Dict[FullQualifiedId, List[str]] = {}
    user_id: Optional[int] = None
    locked_fields: Dict[Any, int] = {}
    for element in write_request_elements:
        events.extend(element["events"])
        for fqid, info_text in element["information"].items():
            if information.get(fqid) is None:
                information[fqid] = info_text
            else:
                information[fqid].extend(info_text)
        if user_id is None:
            user_id = element["user_id"]
        else:
            if user_id != element["user_id"]:
                raise ValueError(
                    "You can not merge two write request elements of different users."
                )
        for key, position in element["locked_fields"].items():
            if locked_fields.get(key) is None:
                locked_fields[key] = position
            else:
                locked_fields[key] = min(position, locked_fields[key])
    if user_id is None:
        raise
    return WriteRequestElement(
        events=events,
        information=information,
        user_id=user_id,
        locked_fields=locked_fields,
    )
