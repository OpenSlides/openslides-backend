from typing import Any, Dict, Iterable, List, Set, Tuple, Union

from mypy_extensions import TypedDict

from ..models.base import Model
from ..models.fields import RelationMixin
from ..shared.interfaces import Database, Event, Permission
from ..shared.patterns import Collection, FullQualifiedField, FullQualifiedId
from .actions_interface import Payload

DataSet = TypedDict("DataSet", {"position": int, "data": Any})


class Action:
    """
    Base class for actions.
    """

    position = 0

    def __init__(self, permission: Permission, database: Database) -> None:
        self.permission = permission
        self.database = database

    def perform(self, payload: Payload, user_id: int) -> Iterable[Event]:
        """
        Entrypoint to perform the action.
        """
        self.user_id = user_id
        self.check_permission_on_entry()
        self.validate(payload)
        dataset = self.prepare_dataset(payload)
        self.check_permission_on_dataset(dataset)
        return self.create_events(dataset)

    def check_permission_on_entry(self) -> None:
        """
        Checks permission at the beginning of the action.
        """
        raise NotImplementedError

    def validate(self, payload: Payload) -> None:
        """
        Validates payload. Raises ActionException if payload is invalid.
        """
        raise NotImplementedError

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

    def create_events(self, dataset: DataSet) -> Iterable[Event]:
        """
        Takes dataset and creates events that can be sent to event store.
        """
        raise NotImplementedError

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
    ) -> Dict[FullQualifiedField, Union[int, List[int]]]:
        """
        Updates references of the given model for the given fields. Use it in
        prepare_dataset method.
        """
        references = {}  # type: Dict[FullQualifiedField, Union[int, List[int]]]

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
                    new_value = ref[model_field.related_name] + [id]
                else:
                    # ref_id in remove
                    new_value = ref[model_field.related_name]
                    new_value.remove(id)
                fqfield = FullQualifiedField(
                    Collection(model_field.to), ref_id, model_field.related_name
                )
                references[fqfield] = new_value
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
        current_ids = set(current_obj.get(field, []))
        new_ids = set(ref_ids)
        add = new_ids - current_ids
        remove = current_ids - new_ids
        return (add, remove)
