from collections import defaultdict
from typing import Any, ContextManager, cast

from openslides_backend.datastore.reader.core.reader import (
    CountResult,
    ExistsResult,
    FilterResult,
    MaxResult,
    MinResult,
)
from openslides_backend.datastore.shared.di import service_as_factory
from openslides_backend.datastore.shared.postgresql_backend import (
    ConnectionHandler,
    retry_on_db_failure,
)
from openslides_backend.datastore.shared.services import (
    EnvironmentService,
    HistoryInformation,
    ReadDatabase,
)
from openslides_backend.datastore.shared.services.read_database import (
    AggregateFilterQueryFieldsParameters,
    BaseAggregateFilterQueryFieldsParameters,
    CountFilterQueryFieldsParameters,
)
from openslides_backend.datastore.shared.util import (
    DeletedModelsBehaviour,
    MappedFields,
    get_exception_for_deleted_models_behaviour,
)
from openslides_backend.shared.filters import Filter
from openslides_backend.shared.otel import make_span
from openslides_backend.shared.patterns import (
    Collection,
    FullQualifiedId,
    Id,
    collection_and_id_from_fqid,
)
from openslides_backend.shared.typing import Model

from .requests import (
    AggregateRequest,
    FilterRequest,
    GetAllRequest,
    GetEverythingRequest,
    GetManyRequest,
    GetRequest,
    HistoryInformationRequest,
    MinMaxRequest,
)


@service_as_factory
class ReaderService:
    connection: ConnectionHandler
    database: ReadDatabase
    env: EnvironmentService

    def get_database_context(self) -> ContextManager[None]:
        return self.database.get_context()

    @retry_on_db_failure
    def get(self, request: GetRequest) -> Model:
        with make_span(self.env, "get request"):
            if request.position:
                # if a position is given, first test if the model is in the correct
                # state to prevent the unnecessary building of the model if it's not
                with make_span(
                    self.env, "check deleted status for position-based request"
                ):
                    fqids = self.filter_fqids_by_deleted_status(
                        [request.fqid], request.position, request.get_deleted_models
                    )
                    if not len(fqids):
                        raise get_exception_for_deleted_models_behaviour(
                            request.fqid, request.get_deleted_models
                        )

                    with make_span(self.env, "build model for position"):
                        model = self.database.build_model_ignore_deleted(
                            request.fqid, request.position
                        )
                with make_span(self.env, "apply mapped fields"):
                    model = self.apply_mapped_fields(model, request.mapped_fields)
            else:
                with make_span(self.env, "get from database"):
                    model = self.database.get(
                        request.fqid,
                        request.build_mapped_fields(),
                        request.get_deleted_models,
                    )
        return model

    @retry_on_db_failure
    def get_many(self, request: GetManyRequest) -> dict[Collection, dict[Id, Model]]:
        with make_span(self.env, "get_many request"):
            with make_span(self.env, "gather mapped fields per fqid"):
                mapped_fields = request.build_mapped_fields()

            with make_span(self.env, "call database"):
                if request.position:
                    fqids = self.filter_fqids_by_deleted_status(
                        mapped_fields.fqids,
                        request.position,
                        request.get_deleted_models,
                    )
                    result = self.database.build_models_ignore_deleted(
                        fqids, request.position
                    )
                    result = self.apply_mapped_fields_multi(
                        result, mapped_fields.per_fqid
                    )
                else:
                    result = self.database.get_many(
                        mapped_fields.fqids,
                        mapped_fields,
                        request.get_deleted_models,
                    )

            with make_span(self.env, "change mapping"):
                # change mapping fqid->model to collection->id->model
                final: dict[Collection, dict[Id, Model]] = defaultdict(dict)
                for fqid, model in result.items():
                    collection, id = collection_and_id_from_fqid(fqid)
                    final[collection][id] = model

                with make_span(self.env, "add back empty collections"):
                    # add back empty collections
                    for collection in mapped_fields.collections:
                        if not final[collection]:
                            final[collection] = {}
        return final

    @retry_on_db_failure
    def get_all(self, request: GetAllRequest) -> dict[Id, Model]:
        with make_span(self.env, "get_all request"):
            models = self.database.get_all(
                request.collection,
                MappedFields(request.mapped_fields),
                request.get_deleted_models,
            )
        return models

    @retry_on_db_failure
    def get_everything(
        self, request: GetEverythingRequest
    ) -> dict[Collection, dict[Id, Model]]:
        return self.database.get_everything(request.get_deleted_models)

    @retry_on_db_failure
    def filter(self, request: FilterRequest) -> FilterResult:
        with make_span(self.env, "filter request"):
            data = self.database.filter(
                request.collection, request.filter, request.mapped_fields
            )
            position = self.database.get_max_position()
        return {
            "data": data,
            "position": position,
        }

    def exists(self, request: AggregateRequest) -> ExistsResult:
        count = self.count(request)
        return {"exists": count["count"] > 0, "position": count["position"]}

    def count(self, request: AggregateRequest) -> CountResult:
        res = self.aggregate(
            request.collection, request.filter, CountFilterQueryFieldsParameters()
        )
        return cast(CountResult, res)

    def minmax(self, request: MinMaxRequest, mode: str) -> dict[str, Any]:
        params = AggregateFilterQueryFieldsParameters(mode, request.field, request.type)
        return self.aggregate(request.collection, request.filter, params)

    def min(self, request: MinMaxRequest) -> MinResult:
        res = self.minmax(request, "min")
        return cast(MinResult, res)

    def max(self, request: MinMaxRequest) -> MaxResult:
        res = self.minmax(request, "max")
        return cast(MaxResult, res)

    @retry_on_db_failure
    def aggregate(
        self,
        collection: str,
        filter: Filter,
        fields_params: BaseAggregateFilterQueryFieldsParameters,
    ) -> dict[str, Any]:
        result = self.database.aggregate(collection, filter, fields_params)
        return result

    def filter_fqids_by_deleted_status(
        self,
        fqids: list[str],
        position: int,
        get_deleted_models: DeletedModelsBehaviour,
    ) -> list[str]:
        if get_deleted_models == DeletedModelsBehaviour.ALL_MODELS:
            return fqids
        else:
            deleted_map = self.database.get_deleted_status(fqids, position)
            return [
                fqid
                for fqid in fqids
                if fqid in deleted_map
                and deleted_map[fqid]
                == (get_deleted_models == DeletedModelsBehaviour.ONLY_DELETED)
            ]

    def apply_mapped_fields(self, model: Model, mapped_fields: list[str]) -> Model:
        if not mapped_fields or not len(mapped_fields):
            return model
        return {
            field: model[field]
            for field in mapped_fields
            if field in model and model[field] is not None
        }

    def apply_mapped_fields_multi(
        self,
        models: dict[str, Model],
        mapped_fields_per_fqid: dict[str, list[str]],
    ) -> dict[str, Model]:
        if not mapped_fields_per_fqid or not len(mapped_fields_per_fqid):
            return models
        return {
            fqid: self.apply_mapped_fields(model, mapped_fields_per_fqid.get(fqid, []))
            for fqid, model in models.items()
        }

    @retry_on_db_failure
    def history_information(
        self, request: HistoryInformationRequest
    ) -> dict[FullQualifiedId, list[HistoryInformation]]:
        return self.database.get_history_information(request.fqids)
