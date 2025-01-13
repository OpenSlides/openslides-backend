import builtins
from collections import defaultdict
from typing import Literal

from ...shared.exceptions import DatabaseException
from ...shared.filters import And, Filter, FilterOperator
from ...shared.interfaces.env import Env
from ...shared.interfaces.logging import LoggingModule
from ...shared.patterns import (
    Collection,
    FullQualifiedId,
    collection_from_fqid,
    fqid_from_collection_and_id,
    id_from_fqid,
)
from ...shared.typing import ModelMap
from ..database.commands import GetManyRequest
from ..database.interface import (
    Database,
    MappedFieldsPerFqid,
    PartialModel,
)

MODEL_FIELD_SQL = "data->>%s"
MODEL_FIELD_NUMERIC_SQL = r"\(data->%s\)::numeric"
MODEL_FIELD_NUMERIC_REPLACE = "(data->%s)::numeric"
COMPARISON_VALUE_TEXT_SQL = "%s::text"
COMPARISON_VALUE_SQL = "%s"


class ExtendedDatabase(Database):
    """
    Subclass of the datastore adapter to extend the functions with the usage of the changed_models.

    Restrictions:
    -   get_deleted_models only works one way with the changed_models: if the model was not deleted
        in the datastore, but is deleted in the changed_models. The other way around does not work
        since a deleted model in the changed_models is marked via DeletedModel() and does not store
        any data.
    -   all filter-based requests may take two calls to the datastore to succeed. The first call is
        always necessary, since the changed_models are never complete. If, however, a model in the
        changed_models matches the filter which it did not in the database AND some fields are
        missing in the changed_models which are needed through the mapped_fields, a second request
        is needed to fetch the missing fields. This can be circumvented by always storing (more or
        less) "full" models in the changed_data, meaning all relevant fields which are requested in
        future calls are present. This is the case for most applications in the backend.
    -   filters are only evaluated separately on the changed_models and the datastore. If, for
        example, a model in the datastore does not fit the filter, but through a change in the
        changed_models would fit it, BUT does not fit the filter from the changed_models alone, it
        is not found. Example:
        datastore content: {"f": 1, "g": 1}
        changed_models: {"f": 2}
        filter: f = 2 and g = 1
        This also applies in the reverse direction: If the datastore content of a model matches the
        filter, but it is invalidated through a change in the changed_models, it is still found and
        returned with the new fields from the changed_models. This may lead to unexpected results by
        including a model in the results which does not fit the given filter. This could be
        circumvented by applying the filter again after building the result and removing all models
        which do not fit it anymore.
        For performance as well as practical reasons, this is not implemented. In practice, filters
        are only applied to "static" fields which do not changed during a request, e.g.
        `meeting_id`, `list_of_speakers_id` etc. So this should not be a problem.
    """

    changed_models: ModelMap

    def __init__(self, logging: LoggingModule, env: Env) -> None:
        self.env = env
        self.logger = logging.getLogger(__name__)

    def apply_changed_model(
        self, fqid: FullQualifiedId, instance: PartialModel, replace: bool = False
    ) -> None:
        """
        Adds or replaces the model identified by fqid in the changed_models.
        Automatically adds missing id field.
        """
        if replace:
            self.changed_models[fqid] = instance
        else:
            self.changed_models[fqid].update(instance)
        if "id" not in self.changed_models[fqid]:
            self.changed_models[fqid]["id"] = id_from_fqid(fqid)

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: list[str],
        position: int | None = None,
    ) -> PartialModel:
        """
        Get the given model.
        """
        try:
            if self.is_new(fqid):
                # if the model is new, we know it does not exist in the datastore and can directly throw
                # an exception or return an empty result
                return {}
            else:
                # TODO Implement me!
                return {}
        except DatabaseException:
                raise

        return result

    def get_many(
        self,
        get_many_requests: list[GetManyRequest],
        position: int | None = None,
    ) -> dict[Collection, dict[int, PartialModel]]:
        # TODO implement me!
        return {}

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        mapped_fields: list[str],
    ) -> dict[int, PartialModel]:
        # TODO Implement me!
        return {}

    def exists(
        self,
        collection: Collection,
        filter: Filter,
    ) -> bool:
        # TODO Implement me!
        return False

    def count(
        self,
        collection: Collection,
        filter: Filter,
        use_changed_models: bool = True,
    ) -> int:
        # TODO Implement me!
        return 0

    def min(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        use_changed_models: bool = True,
    ) -> int | None:
        # TODO Implement me!
        return None


    def max(
        self,
        collection: Collection,
        filter: Filter,
        field: str,
        use_changed_models: bool = True,
    ) -> int | None:
        # TODO Implement me!
        return None

    def is_deleted(self, fqid: FullQualifiedId) -> bool:
        # TODO Implement me! If necessary?
        return False

    def is_new(self, fqid: FullQualifiedId) -> bool:
        # TODO Implement me! If necessary?
        return False

    def reset(self, hard: bool = True) -> None:
        # TODO Implement me! If necessary?
        return None

#    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]:
#        self.logger.debug(
#            f"Start RESERVE_IDS request to datastore with the following data: "
#            f"Collection: {collection}, Amount: {amount}"
#        )
#        response = self.retrieve(command)
#        return response.get("ids")

#    def reserve_id(self, collection: Collection) -> int:
#        return self.reserve_ids(collection=collection, amount=1)[0]
#
    def write(self, write_requests: list[WriteRequest] | WriteRequest) -> None:
        if isinstance(write_requests, WriteRequest):
            write_requests = [write_requests]
        command = commands.Write(write_requests=write_requests)
        self.logger.debug(
            f"Start WRITE request to datastore with the following data: "
            f"Write request: {write_requests}"
        )
        self.retrieve(command)

    def write_without_events(self, write_request: WriteRequest) -> None:
        command = commands.WriteWithoutEvents(write_requests=[write_request])
        self.logger.debug(
            f"Start WRITE_WITHOUT_EVENTS request to datastore with the following data: "
            f"Write request: {write_request}"
        )
        self.retrieve(command)

    def get_everything(self) -> dict[Collection, dict[int, PartialModel]]:
        command = commands.GetEverything()
        self.logger.debug("Get Everything from datastore.")
        return self.retrieve(command)

    def delete_history_information(self) -> None:
        command = commands.DeleteHistoryInformation()
        self.logger.debug("Delete history information send to datastore.")
        self.retrieve(command)