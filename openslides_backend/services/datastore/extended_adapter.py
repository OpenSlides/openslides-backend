from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple, Union

from datastore.shared.util import DeletedModelsBehaviour

from ...shared.exceptions import DatastoreException
from ...shared.interfaces.collection_field_lock import CollectionFieldLockWithFilter
from ...shared.interfaces.logging import LoggingModule
from ...shared.patterns import CollectionField, FullQualifiedField, FullQualifiedId
from ...shared.typing import DeletedModel, ModelMap
from .adapter import DatastoreAdapter
from .interface import Engine, InstanceAdditionalBehaviour, LockResult


class ExtendedDatastoreAdapter(DatastoreAdapter):
    """
    Subclass of the datastore adapter to extend the functions with the usage of
    the additional_relation_models. Normal adapter methods are still available
    with a _ prefix.
    """

    additional_relation_models: ModelMap
    additional_relation_model_locks: Dict[FullQualifiedId, int]

    def __init__(self, engine: Engine, logging: LoggingModule) -> None:
        super().__init__(engine, logging)
        self.additional_relation_models = defaultdict(dict)
        self.additional_relation_model_locks = {}

    def update_locked_fields(
        self,
        key: Union[FullQualifiedId, FullQualifiedField, CollectionField],
        lock: Union[int, CollectionFieldLockWithFilter],
    ) -> None:
        super().update_locked_fields(key, lock)
        # save to additional models locks in case it is needed later
        if isinstance(key, (FullQualifiedId, FullQualifiedField)):
            if isinstance(key, FullQualifiedId):
                fqid = key
            else:
                fqid = FullQualifiedId(key.collection, key.id)
            # new value already holds the lower of both locks if there previously was one
            new_value = self.locked_fields[str(key)]
            assert isinstance(new_value, int)
            self.additional_relation_model_locks[fqid] = new_value

    def update_additional_models(
        self, fqid: FullQualifiedId, instance: Dict[str, Any], replace: bool = False
    ) -> None:
        """
        Adds or replaces the model identified by fqid in the additional models.
        Automatically adds missing id field.
        """
        if replace or isinstance(instance, DeletedModel):
            self.additional_relation_models[fqid] = instance
        else:
            self.additional_relation_models[fqid].update(instance)
        if "id" not in self.additional_relation_models[fqid]:
            self.additional_relation_models[fqid]["id"] = fqid.id

    def fetch_model(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str],
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
        db_additional_relevance: InstanceAdditionalBehaviour = InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
        exception: bool = True,
    ) -> Dict[str, Any]:
        """
        Uses the current additional_relation_models to fetch the given model.
        additional_relation_models serves as a kind of cache layer of all recently done
        changes - all updates to any model during the action are saved in there.
        The parameter db_additional_relevance defines what is searched first: the
        datastore or the additional models.

        Use this over the get method when in doubt.
        """
        datastore_exception: Optional[DatastoreException] = None

        def get_additional() -> Tuple[bool, Dict[str, Any]]:
            if (model := self.additional_relation_models.get(fqid)) and (
                get_deleted_models == DeletedModelsBehaviour.ALL_MODELS
                or (
                    isinstance(model, DeletedModel)
                    == (get_deleted_models == DeletedModelsBehaviour.ONLY_DELETED)
                )
            ):
                found_fields = set()
                complete = True
                if mapped_fields:
                    instance = {}
                    for field in mapped_fields:
                        if field in model:
                            instance[field] = deepcopy(model[field])
                            found_fields.add(field)
                    if len(mapped_fields) != len(found_fields):
                        complete = False
                    if (
                        lock_result
                        and found_fields
                        and fqid in self.additional_relation_model_locks
                    ):
                        position = self.additional_relation_model_locks[fqid]
                        if isinstance(lock_result, list):
                            fields_to_lock = found_fields.intersection(lock_result)
                        else:
                            fields_to_lock = found_fields
                        self.update_locked_fields_from_mapped_fields(
                            fqid, position, fields_to_lock
                        )
                else:
                    instance = deepcopy(model)
                    if lock_result and fqid in self.additional_relation_model_locks:
                        position = self.additional_relation_model_locks[fqid]
                        self.update_locked_fields(fqid, position)
                return (complete, instance)
            else:
                return (False, {})

        def get_db() -> Tuple[bool, Dict[str, Any], Optional[DatastoreException]]:
            try:
                instance = self.get(
                    fqid,
                    mapped_fields=mapped_fields,
                    position=position,
                    get_deleted_models=get_deleted_models,
                    lock_result=lock_result,
                )
                return (
                    True,
                    instance,
                    None,
                )
            except DatastoreException as e:
                return False, {}, e if exception else None

        if db_additional_relevance in (
            InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
            InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
        ):
            complete, result = get_additional()
            okay = bool(result)
            if (
                not complete
                and db_additional_relevance
                == InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST
            ):
                cache_okay = okay
                cache_result = result
                okay, result, datastore_exception = get_db()
                if okay:
                    result = {**result, **cache_result}
                elif cache_okay:
                    okay = True
                    result = cache_result
        else:
            okay, result, datastore_exception = get_db()
            if (
                not okay
                and db_additional_relevance
                == InstanceAdditionalBehaviour.DBINST_BEFORE_ADDITIONAL
            ):
                okay, result = get_additional()
        if not okay and exception:
            if datastore_exception:
                raise datastore_exception
            else:
                raise DatastoreException(f"{fqid} not found at all.")
        return result

    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        """
        Returns whether the given model was deleted during this request or not.
        """
        return isinstance(self.additional_relation_models.get(fqid), DeletedModel)

    def reset(self) -> None:
        super().reset()
        self.additional_relation_models.clear()
