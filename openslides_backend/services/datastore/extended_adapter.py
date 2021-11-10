import re
from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from datastore.shared.postgresql_backend import SqlQueryHelper
from datastore.shared.util import DeletedModelsBehaviour

from ...shared.exceptions import DatastoreException
from ...shared.filters import Filter
from ...shared.interfaces.collection_field_lock import CollectionFieldLockWithFilter
from ...shared.interfaces.logging import LoggingModule
from ...shared.patterns import (
    Collection,
    CollectionField,
    FullQualifiedField,
    FullQualifiedId,
)
from ...shared.typing import DeletedModel, ModelMap
from .adapter import DatastoreAdapter
from .interface import Engine, InstanceAdditionalBehaviour, LockResult, PartialModel

MODEL_FIELD_SQL = "data->>%s"
COMPARISON_VALUE_SQL = "%s::text"


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
        self, fqid: FullQualifiedId, instance: PartialModel, replace: bool = False
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

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: Optional[List[str]] = None,
        position: int = None,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
        db_additional_relevance: InstanceAdditionalBehaviour = InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
        raise_exception: bool = True,
    ) -> PartialModel:
        """
        Uses the current additional_relation_models to fetch the given model.
        additional_relation_models serves as a kind of cache layer of all recently done
        changes - all updates to any model during the action are saved in there.
        The parameter db_additional_relevance defines what is searched first: the
        datastore or the additional models.
        """
        datastore_exception: Optional[DatastoreException] = None

        if (
            position
            and db_additional_relevance != InstanceAdditionalBehaviour.ONLY_DBINST
        ):
            raise DatastoreException(
                "Position-based fetching is only possible for ONLY_DBINST"
            )

        if db_additional_relevance in (
            InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
            InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
        ):
            complete, result = self._get_model_from_additional(
                fqid, mapped_fields, get_deleted_models, lock_result
            )
            okay = bool(result)
            if (
                not complete
                and db_additional_relevance
                == InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST
            ):
                db_result, datastore_exception = self._get_model_from_db(
                    fqid, mapped_fields, get_deleted_models, lock_result
                )
                if not datastore_exception:
                    return {**db_result, **result}
        else:
            result, datastore_exception = self._get_model_from_db(
                fqid, mapped_fields, get_deleted_models, lock_result, position
            )
            okay = not datastore_exception
            if (
                datastore_exception
                and db_additional_relevance
                == InstanceAdditionalBehaviour.DBINST_BEFORE_ADDITIONAL
            ):
                _, result = self._get_model_from_additional(
                    fqid, mapped_fields, get_deleted_models, lock_result
                )
                okay = bool(result)

        if not okay and raise_exception:
            if datastore_exception:
                raise datastore_exception
            else:
                raise DatastoreException(f"{fqid} not found at all.")
        return result

    def _get_model_from_additional(
        self,
        fqid: FullQualifiedId,
        mapped_fields: Optional[List[str]],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
    ) -> Tuple[bool, PartialModel]:
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

    def _get_model_from_db(
        self,
        fqid: FullQualifiedId,
        mapped_fields: Optional[List[str]],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: LockResult = True,
        position: int = None,
    ) -> Tuple[PartialModel, Optional[DatastoreException]]:
        try:
            instance = super().get(
                fqid,
                mapped_fields=mapped_fields,
                position=position,
                get_deleted_models=get_deleted_models,
                lock_result=lock_result,
            )
            return instance, None
        except DatastoreException as e:
            return {}, e

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: List[str] = [],
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        db_additional_relevance: InstanceAdditionalBehaviour = InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
    ) -> Dict[int, PartialModel]:
        if db_additional_relevance in (
            InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
            InstanceAdditionalBehaviour.ONLY_ADDITIONAL,
        ):
            results = self._filter_additional_models(collection, filter)
            self._apply_mapped_fields(results, mapped_fields)
            if (
                db_additional_relevance
                == InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST
            ):
                db_results = super().filter(
                    collection, filter, mapped_fields, get_deleted_models, lock_result
                )
                results = self._merge_model_mappings(results, db_results)
        else:
            results = super().filter(
                collection, filter, mapped_fields, get_deleted_models, lock_result
            )
            if (
                db_additional_relevance
                == InstanceAdditionalBehaviour.DBINST_BEFORE_ADDITIONAL
            ):
                add_results = self._filter_additional_models(collection, filter)
                self._apply_mapped_fields(add_results, mapped_fields)
                results = self._merge_model_mappings(results, add_results)
        return results

    def min(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        db_additional_relevance: InstanceAdditionalBehaviour = InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
    ) -> Optional[int]:
        return self._extended_minmax(
            collection,
            filter,
            field,
            get_deleted_models,
            lock_result,
            db_additional_relevance,
            "min",
        )

    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour = DeletedModelsBehaviour.NO_DELETED,
        lock_result: bool = True,
        db_additional_relevance: InstanceAdditionalBehaviour = InstanceAdditionalBehaviour.ADDITIONAL_BEFORE_DBINST,
    ) -> Optional[int]:
        return self._extended_minmax(
            collection,
            filter,
            field,
            get_deleted_models,
            lock_result,
            db_additional_relevance,
            "max",
        )

    def _extended_minmax(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        get_deleted_models: DeletedModelsBehaviour,
        lock_result: bool,
        db_additional_relevance: InstanceAdditionalBehaviour,
        mode: Literal["min", "max"],
    ) -> Optional[int]:
        factor = int(mode == "max") * 2 - 1
        add_extreme = db_extreme = float("-inf")
        if db_additional_relevance != InstanceAdditionalBehaviour.ONLY_DBINST:
            results = self._filter_additional_models(collection, filter)
            comparable_results = [
                model[field] * factor
                for model in results.values()
                if self._comparable(model.get(field), 0)
            ]
            if comparable_results:
                add_extreme = max(comparable_results)
        if db_additional_relevance != InstanceAdditionalBehaviour.ONLY_ADDITIONAL:
            _db_extreme = getattr(super(), mode)(
                collection, filter, field, get_deleted_models, lock_result
            )
            if _db_extreme is not None:
                db_extreme = _db_extreme * factor
        full_extreme = max(add_extreme, db_extreme)
        return int(full_extreme * factor) if full_extreme != float("-inf") else None

    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        return isinstance(self.additional_relation_models.get(fqid), DeletedModel)

    def reset(self) -> None:
        super().reset()
        self.additional_relation_models.clear()

    def _filter_additional_models(
        self, collection: Collection, filter: Filter
    ) -> Dict[int, Dict[str, Any]]:
        """
        Uses the datastore's SqlQueryHelper to build an SQL query for the given filter, transforms it into valid python
        code and then executes it.
        """
        # Build sql query for this filter. The arguments array contains the replacements for all %s in the query in the
        # correct order.
        query_helper = SqlQueryHelper()
        arguments: List[str] = []
        sql_query = query_helper.build_filter_str(filter, arguments)

        # transform query into valid python code
        filter_code = sql_query.lower().replace("null", "None").replace(" = ", " == ")
        # regex for all FilterOperators which were translated by the SqlQueryHelper
        regex = f"{MODEL_FIELD_SQL} (<|<=|>=|>|==|!=|is|is not) ({COMPARISON_VALUE_SQL}|None)"
        matches = re.findall(regex, filter_code)
        # this will hold all items from arguments, but correctly formatted for python and enhanced with validity checks
        formatted_args = []
        i = 0
        for match in matches:
            # for these operators, ensure that the model field is actually comparable to prevent TypeErrors
            if match[0] in ("<", "<=", ">=", ">"):
                formatted_args.append(
                    f'self._comparable(model.get("{arguments[i]}"), {repr(arguments[i + 1])}) and model.get("{arguments[i]}")'
                )
            else:
                formatted_args.append(f'model.get("{arguments[i]}")')
            i += 1
            # if comparison happens with a value, append it as well
            if match[1] == COMPARISON_VALUE_SQL:
                formatted_args.append(repr(arguments[i]))
                i += 1
        # replace SQL placeholders and SQL specific code with the formatted python snippets
        filter_code = filter_code.replace(MODEL_FIELD_SQL, "{}").replace(
            COMPARISON_VALUE_SQL, "{}"
        )
        filter_code = filter_code.format(*formatted_args)
        # run eval with the generated code
        filter_code = (
            "{model['id']: model for fqid, model in self.additional_relation_models.items() if fqid.collection == collection and ("
            + filter_code
            + ")}"
        )
        scope = locals()
        results = eval(filter_code, scope)
        return deepcopy(results)

    def _comparable(self, a: Any, b: Any) -> bool:
        """
        Tries to compare a and b. If they are not comparable, the resulting TypeError is caught and False is returned.
        Only < is tested since generally either all comparisons are implemented or none, so it is sufficient to only
        test one.
        """
        try:
            a < b
            return True
        except TypeError:
            return False

    def _apply_mapped_fields(
        self, results: Dict[int, PartialModel], mapped_fields: List[str]
    ) -> None:
        """
        Apply the given mapped_fields by removing all fields from the models which are not present in the list.
        """
        for model in results.values():
            for field in list(model.keys()):
                if field not in mapped_fields:
                    del model[field]

    def _merge_model_mappings(
        self, a: Dict[int, PartialModel], b: Dict[int, PartialModel]
    ) -> Dict[int, PartialModel]:
        """
        Merge the model mappings a and b, where a takes priority over b in teh case of duplicate field values.
        """
        merged = deepcopy(a)
        for id, model in b.items():
            merged[id] = {**model, **a.get(id, {})}
        return merged
